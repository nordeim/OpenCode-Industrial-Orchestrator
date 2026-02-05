"""
INDUSTRIAL DATABASE INTEGRATION TESTS
Test PostgreSQL integration with real database connection.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from src.industrial_orchestrator.infrastructure.config.database import (
    DatabaseManager,
    DatabaseSettings,
    get_database_manager,
    shutdown_database,
)


class TestDatabaseManagerIntegration:
    """Integration tests for DatabaseManager"""
    
    @pytest_asyncio.fixture
    async def db_manager(self):
        """Create database manager for testing"""
        # Use test settings
        settings = DatabaseSettings(
            host="localhost",
            port=5432,
            name="orchestration",
            user="cybernetics",
            password="industrial_secure_001",
            pool_size=5,
            max_overflow=2,
            echo=False,
            ssl_mode="disable",
        )
        
        manager = DatabaseManager(settings)
        await manager.initialize()
        
        yield manager
        
        await manager.close()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connection_pool_initialization(self, db_manager):
        """Test connection pool initialization"""
        assert db_manager.engine is not None
        assert db_manager.session_factory is not None
        
        # Verify connection works
        async with db_manager.get_session() as session:
            result = await session.execute("SELECT 1 as test_value")
            row = result.fetchone()
            assert row.test_value == 1
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_context_manager(self, db_manager):
        """Test session context manager functionality"""
        async with db_manager.get_session() as session:
            # Should be able to execute queries
            result = await session.execute("SELECT version()")
            version = result.scalar()
            assert "PostgreSQL" in version
            
            # Session should commit automatically on success
            await session.execute("CREATE TEMPORARY TABLE test (id SERIAL PRIMARY KEY)")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_transaction_management(self, db_manager):
        """Test transaction management with savepoints"""
        async with db_manager.get_session() as session:
            # Create test table
            await session.execute("""
                CREATE TEMPORARY TABLE transaction_test (
                    id SERIAL PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Start transaction
            async with db_manager.transaction(session):
                await session.execute(
                    "INSERT INTO transaction_test (value) VALUES (:value)",
                    {"value": "test1"}
                )
            
            # Verify commit
            result = await session.execute("SELECT COUNT(*) FROM transaction_test")
            count = result.scalar()
            assert count == 1
            
            # Test nested transaction with savepoint
            async with db_manager.transaction(session, "sp1"):
                await session.execute(
                    "INSERT INTO transaction_test (value) VALUES (:value)",
                    {"value": "test2"}
                )
                
                # Rollback savepoint
                raise Exception("Test rollback")
            
            # Verify savepoint rollback
            result = await session.execute("SELECT COUNT(*) FROM transaction_test")
            count = result.scalar()
            assert count == 1  # Only first insert persisted
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self, db_manager):
        """Test database health check"""
        health = await db_manager.health_check()
        
        assert "status" in health
        assert "version" in health
        assert "connections" in health
        assert "database_size_bytes" in health
        
        if health["status"] == "healthy":
            assert "PostgreSQL" in health["version"]
            assert health["connections"]["pool_managed"] >= 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connection_retry_logic(self):
        """Test connection retry logic with invalid host"""
        settings = DatabaseSettings(
            host="invalid_host",
            port=5432,
            name="nonexistent",
            user="invalid",
            password="wrong",
            max_retries=2,
            retry_delay=0.1,
        )
        
        manager = DatabaseManager(settings)
        
        # Should fail after retries
        with pytest.raises(ConnectionError):
            await manager.initialize()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, db_manager):
        """Test concurrent session usage"""
        async def use_session(session_id: int):
            async with db_manager.get_session() as session:
                await session.execute("SELECT pg_sleep(0.1)")
                return session_id
        
        # Create multiple concurrent sessions
        tasks = [use_session(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert set(results) == set(range(10))
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_metrics_collection(self, db_manager):
        """Test metrics collection"""
        metrics = db_manager.get_metrics()
        
        assert "connection_count" in metrics
        assert "failed_connections" in metrics
        assert "pool_size" in metrics
        assert "timestamp" in metrics


class TestGlobalDatabaseFunctions:
    """Test global database functions"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_database_manager(self):
        """Test global database manager singleton"""
        manager1 = await get_database_manager()
        manager2 = await get_database_manager()
        
        assert manager1 is manager2  # Should be same instance
        
        await shutdown_database()
    
        @pytest.mark.integration
    
        @pytest.mark.asyncio
    
        async def test_shutdown_database(self):
    
            """Test database shutdown"""
    
            manager = await get_database_manager()
    
        
    
            # Verify manager exists
    
            assert manager is not None
    
        
    
            # Shutdown
    
            await shutdown_database()
    
        
    
            # Verify we can get a new manager
    
            manager2 = await get_database_manager()
    
            assert manager2 is not None
    
            assert manager2 is not manager
    
    
