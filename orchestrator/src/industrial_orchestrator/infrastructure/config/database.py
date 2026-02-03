"""
INDUSTRIAL DATABASE CONFIGURATION
PostgreSQL configuration with connection pooling, retry logic, and resilience patterns.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime, event

from pydantic_settings import BaseSettings, SettingsConfigDict

# Declarative base for all models
Base = declarative_base()


class DatabaseSettings(BaseSettings):
    """Industrial database configuration settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DB_",
        case_sensitive=False
    )
    
    # Connection settings
    host: str = "localhost"
    port: int = 5432
    name: str = "orchestration"
    user: str = "cybernetics"
    password: str = "industrial_secure_001"
    
    # Connection pooling
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800  # Recycle connections every 30 minutes
    
    # SSL/TLS
    ssl_mode: str = "prefer"
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_root_cert: Optional[str] = None
    
    # Performance
    statement_cache_size: int = 1000
    echo: bool = False
    echo_pool: bool = False
    
    # Resilience
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        ssl_params = ""
        if self.ssl_mode != "disable":
            ssl_params = f"&sslmode={self.ssl_mode}"
            if self.ssl_cert:
                ssl_params += f"&sslcert={self.ssl_cert}"
            if self.ssl_key:
                ssl_params += f"&sslkey={self.ssl_key}"
            if self.ssl_root_cert:
                ssl_params += f"&sslrootcert={self.ssl_root_cert}"
        
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
            f"?async_fallback=True{ssl_params}"
        )


class TimestampMixin:
    """Industrial timestamp mixin for all models"""
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="UTC timestamp of creation"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="UTC timestamp of last update"
    )
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of soft deletion"
    )


class DatabaseManager:
    """
    Industrial-grade database manager
    
    Features:
    1. Connection pooling with monitoring
    2. Automatic retry with exponential backoff
    3. Connection health checking
    4. Transaction management with savepoints
    5. Query logging and performance tracking
    """
    
    def __init__(self, settings: DatabaseSettings):
        self.settings = settings
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._connection_count = 0
        self._failed_connections = 0
        
    async def initialize(self) -> None:
        """Initialize database connection pool"""
        if self._engine is not None:
            return
        
        engine_args: Dict[str, Any] = {
            "poolclass": AsyncAdaptedQueuePool,
            "pool_size": self.settings.pool_size,
            "max_overflow": self.settings.max_overflow,
            "pool_timeout": self.settings.pool_timeout,
            "pool_recycle": self.settings.pool_recycle,
            "echo": self.settings.echo,
            "echo_pool": self.settings.echo_pool,
            "future": True,
        }
        
        # Create engine with retry logic
        for attempt in range(self.settings.max_retries):
            try:
                self._engine = create_async_engine(
                    self.settings.connection_string,
                    **engine_args
                )
                
                # Add event listeners for monitoring
                self._setup_event_listeners()
                
                # Test connection
                async with self._engine.connect() as conn:
                    await conn.execute("SELECT 1")
                
                print(f"Database connection established (attempt {attempt + 1})")
                break
                
            except Exception as e:
                self._failed_connections += 1
                if attempt == self.settings.max_retries - 1:
                    raise ConnectionError(
                        f"Failed to connect to database after {self.settings.max_retries} attempts: {e}"
                    )
                
                delay = self.settings.retry_delay * (self.settings.retry_backoff ** attempt)
                print(f"Database connection failed (attempt {attempt + 1}), retrying in {delay:.1f}s: {e}")
                await asyncio.sleep(delay)
        
        # Create session factory
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    def _setup_event_listeners(self) -> None:
        """Setup SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self._engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self._connection_count += 1
            # Set statement timeout to prevent runaway queries
            cursor = dbapi_connection.cursor()
            cursor.execute("SET statement_timeout = 30000")  # 30 seconds
            cursor.close()
        
        @event.listens_for(self._engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            # Verify connection is still alive
            cursor = dbapi_connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        
        @event.listens_for(self._engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            pass  # Connection returned to pool
        
        @event.listens_for(self._engine.sync_engine, "close")
        def on_close(dbapi_connection, connection_record):
            self._connection_count -= 1
    
    @property
    def engine(self) -> AsyncEngine:
        """Get database engine"""
        if self._engine is None:
            raise RuntimeError("Database manager not initialized")
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker:
        """Get session factory"""
        if self._session_factory is None:
            raise RuntimeError("Database manager not initialized")
        return self._session_factory
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """
        Industrial-grade session context manager
        
        Features:
        1. Automatic transaction management
        2. Savepoint support for nested transactions
        3. Automatic rollback on exception
        4. Connection health verification
        """
        session: AsyncSession = self.session_factory()
        
        try:
            # Verify connection is alive
            await session.execute("SELECT 1")
            
            yield session
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            raise
            
        finally:
            await session.close()
    
    @asynccontextmanager
    async def transaction(self, session: AsyncSession, savepoint_name: Optional[str] = None):
        """
        Industrial transaction manager with savepoint support
        
        Usage:
            async with db.get_session() as session:
                async with db.transaction(session, "sp1") as sp:
                    # Nested transaction work
                    pass
        """
        if savepoint_name:
            # Nested transaction using savepoint
            savepoint = await session.begin_nested()
            try:
                yield savepoint
                await session.commit()
            except Exception:
                await savepoint.rollback()
                raise
        else:
            # Top-level transaction
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive database health check"""
        try:
            async with self.get_session() as session:
                # Check basic connectivity
                result = await session.execute("SELECT 1 as healthy, version() as version")
                row = result.fetchone()
                
                # Check connection pool status
                pool_status = await session.execute("""
                    SELECT 
                        COUNT(*) as total_connections,
                        SUM(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active_connections,
                        SUM(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) as idle_connections
                    FROM pg_stat_activity 
                    WHERE usename = current_user
                """)
                pool_row = pool_status.fetchone()
                
                # Check database size
                size_status = await session.execute("""
                    SELECT pg_database_size(current_database()) as size_bytes
                """)
                size_row = size_status.fetchone()
                
                return {
                    "status": "healthy",
                    "version": row.version if row else "unknown",
                    "connections": {
                        "total": pool_row.total_connections if pool_row else 0,
                        "active": pool_row.active_connections if pool_row else 0,
                        "idle": pool_row.idle_connections if pool_row else 0,
                        "pool_managed": self._connection_count,
                    },
                    "database_size_bytes": size_row.size_bytes if size_row else 0,
                    "failed_connection_attempts": self._failed_connections,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def close(self) -> None:
        """Close all database connections"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._connection_count = 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get database metrics for monitoring"""
        return {
            "connection_count": self._connection_count,
            "failed_connections": self._failed_connections,
            "pool_size": self.settings.pool_size,
            "max_overflow": self.settings.max_overflow,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """Get or create global database manager"""
    global _db_manager
    
    if _db_manager is None:
        settings = DatabaseSettings()
        _db_manager = DatabaseManager(settings)
        await _db_manager.initialize()
    
    return _db_manager


async def shutdown_database() -> None:
    """Shutdown database connections"""
    global _db_manager
    
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
