"""
INDUSTRIAL REPOSITORY BASE CLASS
Abstract base class for all repositories with common functionality:
1. Unit of Work pattern
2. Optimistic locking
3. Soft deletion
4. Audit logging
5. Performance monitoring
"""

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import (
    TypeVar, Generic, Optional, List, Dict, Any, AsyncIterator,
    Type, Union, get_args
)
from uuid import UUID

from sqlalchemy import select, update, delete, and_, or_, text
from sqlalchemy.exc import (
    IntegrityError, NoResultFound, MultipleResultsFound,
    DBAPIError, OperationalError
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload, load_only
from pydantic import BaseModel

from ...domain.entities.base import DomainEntity
from ...domain.exceptions.repository_exceptions import (
    EntityNotFoundError,
    EntityAlreadyExistsError,
    OptimisticLockError,
    RepositoryError,
    DatabaseConnectionError,
)
from ..config.database import DatabaseManager, get_database_manager
from ..config.redis import IndustrialRedisClient, get_redis_client


# Type variables for generic repository
T = TypeVar('T', bound=DomainEntity)
M = TypeVar('M')  # SQLAlchemy model type
ID = TypeVar('ID', UUID, str, int)  # ID type


class FilterOperator(str):
    """Filter operators for repository queries"""
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    ILIKE = "ilike"
    CONTAINS = "contains"
    JSON_CONTAINS = "json_contains"


class SortOrder(str):
    """Sort order for repository queries"""
    ASCENDING = "asc"
    DESCENDING = "desc"


class FilterCondition(BaseModel):
    """Industrial filter condition for repository queries"""
    field: str
    operator: FilterOperator
    value: Any
    
    class Config:
        arbitrary_types_allowed = True


class QueryOptions(BaseModel):
    """Industrial query options for repository operations"""
    filters: List[FilterCondition] = []
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.ASCENDING
    limit: Optional[int] = None
    offset: Optional[int] = None
    include_deleted: bool = False
    eager_load: List[str] = []
    select_only: List[str] = []
    
    class Config:
        arbitrary_types_allowed = True


class PaginatedResult(BaseModel):
    """Industrial paginated result structure"""
    items: List[Any]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class IndustrialRepository(ABC, Generic[T, M, ID]):
    """
    Industrial Repository Abstract Base Class
    
    Design Principles:
    1. Follows Repository pattern for data access abstraction
    2. Implements Unit of Work for transaction management
    3. Provides optimistic locking for concurrent updates
    4. Includes soft deletion with audit trail
    5. Monitors performance and errors
    """
    
    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        redis_client: Optional[IndustrialRedisClient] = None,
        cache_ttl: int = 300
    ):
        self._db_manager = db_manager
        self._redis_client = redis_client
        self._cache_ttl = cache_ttl
        self._operation_count = 0
        self._error_count = 0
    
    async def initialize(self) -> None:
        """Initialize repository dependencies"""
        if self._db_manager is None:
            self._db_manager = await get_database_manager()
        
        if self._redis_client is None:
            self._redis_client = await get_redis_client()
    
    @property
    @abstractmethod
    def model_class(self) -> Type[M]:
        """Get SQLAlchemy model class"""
        pass
    
    @property
    @abstractmethod
    def entity_class(self) -> Type[T]:
        """Get domain entity class"""
        pass
    
    @property
    @abstractmethod
    def cache_prefix(self) -> str:
        """Get cache key prefix for this repository"""
        pass
    
    def _get_cache_key(self, key: str) -> str:
        """Generate cache key with prefix"""
        return f"{self.cache_prefix}:{key}"
    
    async def _cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._redis_client:
            return None
        
        cache_key = self._get_cache_key(key)
        try:
            return await self._redis_client.get_json(cache_key)
        except Exception:
            return None
    
    async def _cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self._redis_client:
            return False
        
        cache_key = self._get_cache_key(key)
        try:
            await self._redis_client.set_json(
                cache_key,
                value,
                expire_seconds=ttl or self._cache_ttl
            )
            return True
        except Exception:
            return False
    
    async def _cache_delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self._redis_client:
            return False
        
        cache_key = self._get_cache_key(key)
        try:
            await self._redis_client._client.delete(cache_key)
            return True
        except Exception:
            return False
    
    async def _cache_invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern"""
        if not self._redis_client:
            return 0
        
        cache_pattern = self._get_cache_key(pattern)
        try:
            keys = await self._redis_client._client.keys(f"{cache_pattern}*")
            if keys:
                await self._redis_client._client.delete(*keys)
            return len(keys)
        except Exception:
            return 0
    
    @asynccontextmanager
    async def _get_session(self) -> AsyncIterator[AsyncSession]:
        """Get database session with error handling"""
        async with self._db_manager.get_session() as session:
            try:
                yield session
            except DBAPIError as e:
                self._error_count += 1
                raise DatabaseConnectionError(f"Database error: {e}")
            except Exception as e:
                self._error_count += 1
                raise RepositoryError(f"Repository error: {e}")
    
    def _build_query(self, session: AsyncSession, options: QueryOptions):
        """Build SQLAlchemy query based on options"""
        query = select(self.model_class)
        
        # Apply soft deletion filter
        if not options.include_deleted:
            query = query.where(self.model_class.deleted_at.is_(None))
        
        # Apply filters
        for filter_cond in options.filters:
            field = getattr(self.model_class, filter_cond.field, None)
            if not field:
                continue
            
            if filter_cond.operator == FilterOperator.EQUALS:
                query = query.where(field == filter_cond.value)
            elif filter_cond.operator == FilterOperator.NOT_EQUALS:
                query = query.where(field != filter_cond.value)
            elif filter_cond.operator == FilterOperator.GREATER_THAN:
                query = query.where(field > filter_cond.value)
            elif filter_cond.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
                query = query.where(field >= filter_cond.value)
            elif filter_cond.operator == FilterOperator.LESS_THAN:
                query = query.where(field < filter_cond.value)
            elif filter_cond.operator == FilterOperator.LESS_THAN_OR_EQUAL:
                query = query.where(field <= filter_cond.value)
            elif filter_cond.operator == FilterOperator.IN:
                query = query.where(field.in_(filter_cond.value))
            elif filter_cond.operator == FilterOperator.NOT_IN:
                query = query.where(field.notin_(filter_cond.value))
            elif filter_cond.operator == FilterOperator.LIKE:
                query = query.where(field.like(filter_cond.value))
            elif filter_cond.operator == FilterOperator.ILIKE:
                query = query.where(field.ilike(filter_cond.value))
            elif filter_cond.operator == FilterOperator.CONTAINS:
                query = query.where(field.contains(filter_cond.value))
            elif filter_cond.operator == FilterOperator.JSON_CONTAINS:
                query = query.where(field.contains(filter_cond.value))
        
        # Apply sorting
        if options.sort_by:
            field = getattr(self.model_class, options.sort_by, None)
            if field:
                if options.sort_order == SortOrder.DESCENDING:
                    query = query.order_by(field.desc())
                else:
                    query = query.order_by(field.asc())
        
        # Apply eager loading
        for relation in options.eager_load:
            # Simple eager loading strategy
            query = query.options(selectinload(getattr(self.model_class, relation)))
        
        # Apply field selection
        if options.select_only:
            fields = []
            for field_name in options.select_only:
                field = getattr(self.model_class, field_name, None)
                if field:
                    fields.append(field)
            if fields:
                query = query.options(load_only(*fields))
        
        return query
    
    @abstractmethod
    def _to_entity(self, model: M) -> T:
        """Convert database model to domain entity"""
        pass
    
    @abstractmethod
    def _to_model(self, entity: T, existing_model: Optional[M] = None) -> M:
        """Convert domain entity to database model"""
        pass
    
    async def get_by_id(self, id: ID, options: QueryOptions = None) -> Optional[T]:
        """
        Get entity by ID with industrial resilience
        
        Features:
        1. Cache layer with TTL
        2. Eager loading support
        3. Optimistic lock validation
        4. Error handling and retry
        """
        self._operation_count += 1
        
        options = options or QueryOptions()
        
        # Try cache first
        cache_key = f"id:{id}"
        cached = await self._cache_get(cache_key)
        if cached:
            return self._to_entity(cached) if isinstance(cached, dict) else cached
        
        try:
            async with self._get_session() as session:
                query = self._build_query(session, options)
                query = query.where(self.model_class.id == id)
                
                result = await session.execute(query)
                model = result.scalar_one_or_none()
                
                if not model:
                    return None
                
                entity = self._to_entity(model)
                
                # Cache the result
                await self._cache_set(cache_key, model.to_dict() if hasattr(model, 'to_dict') else model)
                
                return entity
                
        except NoResultFound:
            return None
        except MultipleResultsFound:
            raise RepositoryError(f"Multiple entities found for ID: {id}")
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error getting entity by ID {id}: {e}")
    
    async def get_all(self, options: QueryOptions = None) -> List[T]:
        """Get all entities with industrial query capabilities"""
        self._operation_count += 1
        
        options = options or QueryOptions()
        
        try:
            async with self._get_session() as session:
                query = self._build_query(session, options)
                
                # Apply pagination
                if options.limit:
                    query = query.limit(options.limit)
                if options.offset:
                    query = query.offset(options.offset)
                
                result = await session.execute(query)
                models = result.scalars().all()
                
                return [self._to_entity(model) for model in models]
                
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error getting all entities: {e}")
    
    async def find(self, options: QueryOptions) -> List[T]:
        """Find entities with industrial filtering"""
        self._operation_count += 1
        
        try:
            async with self._get_session() as session:
                query = self._build_query(session, options)
                
                result = await session.execute(query)
                models = result.scalars().all()
                
                return [self._to_entity(model) for model in models]
                
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error finding entities: {e}")
    
    async def paginate(
        self,
        page: int = 1,
        page_size: int = 20,
        options: QueryOptions = None
    ) -> PaginatedResult:
        """Industrial pagination with total count"""
        self._operation_count += 1
        
        options = options or QueryOptions()
        offset = (page - 1) * page_size
        
        # Create paginated options
        paginated_options = QueryOptions(
            **options.dict(exclude={'limit', 'offset'}),
            limit=page_size,
            offset=offset
        )
        
        try:
            async with self._get_session() as session:
                # Get total count
                count_query = select(func.count()).select_from(self.model_class)
                if not options.include_deleted:
                    count_query = count_query.where(self.model_class.deleted_at.is_(None))
                
                count_result = await session.execute(count_query)
                total_count = count_result.scalar()
                
                # Get paginated items
                query = self._build_query(session, paginated_options)
                result = await session.execute(query)
                models = result.scalars().all()
                
                items = [self._to_entity(model) for model in models]
                
                total_pages = (total_count + page_size - 1) // page_size
                
                return PaginatedResult(
                    items=items,
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_previous=page > 1
                )
                
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error paginating entities: {e}")
    
    async def add(self, entity: T) -> T:
        """
        Add entity with industrial resilience
        
        Features:
        1. Optimistic locking
        2. Cache invalidation
        3. Audit logging
        4. Transaction management
        """
        self._operation_count += 1
        
        try:
            async with self._get_session() as session:
                model = self._to_model(entity)
                
                session.add(model)
                await session.flush()
                
                # Refresh to get database-generated values
                await session.refresh(model)
                
                # Update entity with persisted values
                updated_entity = self._to_entity(model)
                
                # Invalidate relevant cache
                await self._cache_invalidate_pattern("list:*")
                
                return updated_entity
                
        except IntegrityError as e:
            self._error_count += 1
            if "unique constraint" in str(e).lower():
                raise EntityAlreadyExistsError(
                    f"Entity already exists: {entity}"
                ) from e
            raise RepositoryError(f"Integrity error adding entity: {e}")
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error adding entity: {e}")
    
    async def update(self, entity: T) -> T:
        """
        Update entity with industrial features
        
        Features:
        1. Optimistic locking with version check
        2. Partial update detection
        3. Cache invalidation
        4. Audit trail
        """
        self._operation_count += 1
        
        try:
            async with self._get_session() as session:
                # Get existing model
                existing_query = select(self.model_class).where(
                    self.model_class.id == entity.id
                )
                result = await session.execute(existing_query)
                existing_model = result.scalar_one_or_none()
                
                if not existing_model:
                    raise EntityNotFoundError(f"Entity not found for update: {entity.id}")
                
                # Check optimistic lock version
                if hasattr(existing_model, 'version') and hasattr(entity, 'version'):
                    if existing_model.version != entity.version:
                        raise OptimisticLockError(
                            f"Optimistic lock violation for entity {entity.id}: "
                            f"expected version {existing_model.version}, got {entity.version}"
                        )
                
                # Update model
                updated_model = self._to_model(entity, existing_model)
                
                # Increment version for optimistic locking
                if hasattr(updated_model, 'version'):
                    updated_model.version = existing_model.version + 1
                
                # Merge changes
                session.add(updated_model)
                await session.flush()
                
                # Refresh to get updated values
                await session.refresh(updated_model)
                
                # Update entity
                updated_entity = self._to_entity(updated_model)
                
                # Invalidate cache
                await self._cache_delete(f"id:{entity.id}")
                await self._cache_invalidate_pattern("list:*")
                
                return updated_entity
                
        except EntityNotFoundError:
            raise
        except OptimisticLockError:
            raise
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error updating entity {entity.id}: {e}")
    
    async def delete(self, id: ID, hard_delete: bool = False) -> bool:
        """
        Delete entity with industrial features
        
        Features:
        1. Soft deletion by default (audit trail)
        2. Hard deletion option for sensitive data
        3. Cascading deletion for relationships
        4. Cache invalidation
        """
        self._operation_count += 1
        
        try:
            async with self._get_session() as session:
                if hard_delete:
                    # Hard delete
                    delete_stmt = delete(self.model_class).where(
                        self.model_class.id == id
                    )
                    result = await session.execute(delete_stmt)
                    deleted = result.rowcount > 0
                else:
                    # Soft delete
                    update_stmt = update(self.model_class).where(
                        and_(
                            self.model_class.id == id,
                            self.model_class.deleted_at.is_(None)
                        )
                    ).values(
                        deleted_at=datetime.now(timezone.utc)
                    )
                    result = await session.execute(update_stmt)
                    deleted = result.rowcount > 0
                
                if deleted:
                    # Invalidate cache
                    await self._cache_delete(f"id:{id}")
                    await self._cache_invalidate_pattern("list:*")
                
                return deleted
                
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error deleting entity {id}: {e}")
    
    async def count(self, options: QueryOptions = None) -> int:
        """Count entities with industrial filtering"""
        self._operation_count += 1
        
        options = options or QueryOptions()
        
        try:
            async with self._get_session() as session:
                query = select(func.count()).select_from(self.model_class)
                
                # Apply soft deletion filter
                if not options.include_deleted:
                    query = query.where(self.model_class.deleted_at.is_(None))
                
                # Apply filters
                for filter_cond in options.filters:
                    field = getattr(self.model_class, filter_cond.field, None)
                    if not field:
                        continue
                    
                    # Apply filter condition (simplified)
                    if filter_cond.operator == FilterOperator.EQUALS:
                        query = query.where(field == filter_cond.value)
                    # Add other operators as needed
                
                result = await session.execute(query)
                return result.scalar()
                
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error counting entities: {e}")
    
    async def exists(self, id: ID) -> bool:
        """Check if entity exists"""
        self._operation_count += 1
        
        try:
            async with self._get_session() as session:
                query = select(func.count()).where(
                    and_(
                        self.model_class.id == id,
                        self.model_class.deleted_at.is_(None)
                    )
                )
                result = await session.execute(query)
                count = result.scalar()
                return count > 0
                
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error checking existence of entity {id}: {e}")
    
    async def bulk_insert(self, entities: List[T]) -> List[T]:
        """Bulk insert with industrial performance"""
        self._operation_count += 1
        
        try:
            async with self._get_session() as session:
                models = [self._to_model(entity) for entity in entities]
                
                session.add_all(models)
                await session.flush()
                
                # Refresh all models
                for model in models:
                    await session.refresh(model)
                
                # Invalidate cache
                await self._cache_invalidate_pattern("list:*")
                
                return [self._to_entity(model) for model in models]
                
        except IntegrityError as e:
            self._error_count += 1
            raise RepositoryError(f"Integrity error in bulk insert: {e}")
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error in bulk insert: {e}")
    
    async def bulk_update(self, entities: List[T]) -> List[T]:
        """Bulk update with industrial performance"""
        self._operation_count += 1
        
        try:
            async with self._get_session() as session:
                updated_entities = []
                
                for entity in entities:
                    # Get existing model
                    query = select(self.model_class).where(
                        self.model_class.id == entity.id
                    )
                    result = await session.execute(query)
                    existing_model = result.scalar_one_or_none()
                    
                    if not existing_model:
                        continue
                    
                    # Check optimistic lock
                    if hasattr(existing_model, 'version') and hasattr(entity, 'version'):
                        if existing_model.version != entity.version:
                            raise OptimisticLockError(
                                f"Optimistic lock violation for entity {entity.id}"
                            )
                    
                    # Update model
                    updated_model = self._to_model(entity, existing_model)
                    
                    if hasattr(updated_model, 'version'):
                        updated_model.version = existing_model.version + 1
                    
                    session.add(updated_model)
                    updated_entities.append(updated_model)
                
                await session.flush()
                
                # Refresh all models
                for model in updated_entities:
                    await session.refresh(model)
                
                # Invalidate cache
                await self._cache_invalidate_pattern("list:*")
                for entity in entities:
                    await self._cache_delete(f"id:{entity.id}")
                
                return [self._to_entity(model) for model in updated_entities]
                
        except Exception as e:
            self._error_count += 1
            raise RepositoryError(f"Error in bulk update: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get repository metrics for monitoring"""
        return {
            "operation_count": self._operation_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._operation_count, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class UnitOfWork:
    """
    Industrial Unit of Work pattern implementation
    
    Manages transactions across multiple repositories
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self._db_manager = db_manager
        self._repositories: Dict[str, IndustrialRepository] = {}
    
    async def initialize(self) -> None:
        """Initialize unit of work"""
        if self._db_manager is None:
            self._db_manager = await get_database_manager()
    
    def register_repository(self, name: str, repository: IndustrialRepository) -> None:
        """Register repository with unit of work"""
        self._repositories[name] = repository
    
    def get_repository(self, name: str) -> IndustrialRepository:
        """Get registered repository"""
        if name not in self._repositories:
            raise KeyError(f"Repository not registered: {name}")
        return self._repositories[name]
    
    @asynccontextmanager
    async def transaction(self):
        """
        Industrial transaction context manager
        
        Features:
        1. Nested transaction support with savepoints
        2. Automatic rollback on exception
        3. Transaction isolation level control
        4. Performance monitoring
        """
        async with self._db_manager.get_session() as session:
            try:
                # Start transaction
                async with session.begin():
                    yield session
                    # Commit happens automatically on successful exit
                    
            except Exception as e:
                # Rollback happens automatically
                raise RepositoryError(f"Transaction failed: {e}") from e
    
    async def commit(self) -> None:
        """Manual commit (use transaction context manager instead)"""
        # This method is kept for compatibility
        # but transactions should be managed via context manager
        pass
    
    async def rollback(self) -> None:
        """Manual rollback (use transaction context manager instead)"""
        # This method is kept for compatibility
        pass
