"""
INDUSTRIAL SESSION REPOSITORY
Session-specific repository with advanced query capabilities and caching.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple, Union
from uuid import UUID

from sqlalchemy import select, update, delete, and_, or_, func, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from ...domain.entities.session import (
    SessionEntity, SessionType, SessionPriority
)
from ...domain.value_objects.session_status import SessionStatus
from ...domain.value_objects.execution_metrics import ExecutionMetrics
from ...domain.exceptions.repository_exceptions import (
    EntityNotFoundError,
    OptimisticLockError,
    RepositoryError,
)
from ..database.models import (
    SessionModel, SessionMetricsModel, SessionCheckpointModel,
    SessionStatusDB, SessionTypeDB, SessionPriorityDB
)
from .base import (
    IndustrialRepository, QueryOptions, FilterOperator,
    FilterCondition, SortOrder, PaginatedResult, UnitOfWork
)


class SessionRepository(IndustrialRepository[SessionEntity, SessionModel, UUID]):
    """
    Industrial Session Repository
    
    Specialized features:
    1. Advanced session filtering by status, type, priority
    2. Performance metrics aggregation
    3. Checkpoint management
    4. Hierarchical session queries
    5. Bulk operations with dependency handling
    """
    
    @property
    def model_class(self):
        return SessionModel
    
    @property
    def entity_class(self):
        return SessionEntity
    
    @property
    def cache_prefix(self):
        return "session_repo"
    
    def _to_entity(self, model: SessionModel) -> SessionEntity:
        """Convert database model to domain entity"""
        # Convert enums
        session_type = SessionType(model.session_type.value)
        priority = SessionPriority(model.priority.value)
        status = SessionStatus(model.status.value)
        
        # Convert metrics if present
        metrics = None
        if model.metrics:
            metrics = ExecutionMetrics(
                created_at=model.metrics.created_at,
                started_at=model.metrics.started_at,
                completed_at=model.metrics.completed_at,
                failed_at=model.metrics.failed_at,
                queue_duration_seconds=model.metrics.queue_duration_seconds,
                execution_duration_seconds=model.metrics.execution_duration_seconds,
                total_duration_seconds=model.metrics.total_duration_seconds,
                cpu_usage_percent=model.metrics.cpu_usage_percent,
                memory_usage_mb=model.metrics.memory_usage_mb,
                disk_usage_mb=model.metrics.disk_usage_mb,
                network_bytes_sent=model.metrics.network_bytes_sent,
                network_bytes_received=model.metrics.network_bytes_received,
                total_tokens_used=model.metrics.total_tokens_used,
                api_calls_count=model.metrics.api_calls_count,
                api_errors_count=model.metrics.api_errors_count,
                retry_count=model.metrics.retry_count,
                success_rate=model.metrics.success_rate,
                confidence_score=model.metrics.confidence_score,
                code_quality_score=model.metrics.code_quality_score,
                result=model.metrics.result,
                error=model.metrics.error,
                warnings=model.metrics.warnings,
                checkpoint_count=model.metrics.checkpoint_count,
                last_checkpoint_at=model.metrics.last_checkpoint_at,
                estimated_cost_usd=model.metrics.estimated_cost_usd,
            )
        
        # Convert checkpoints
        checkpoints = []
        if model.checkpoints:
            for cp in model.checkpoints:
                checkpoints.append({
                    'timestamp': cp.created_at.isoformat() if cp.created_at else None,
                    'data': cp.data,
                    'sequence': cp.sequence
                })
        
        # Create entity
        entity = SessionEntity(
            id=model.id,
            created_at=model.created_at,
            title=model.title,
            description=model.description,
            session_type=session_type,
            priority=priority,
            status=status,
            status_updated_at=model.status_updated_at,
            parent_id=model.parent_id,
            child_ids=model.metadata.get('child_ids', []) if model.metadata else [],
            agent_config=model.agent_config,
            model_config=model.model_config,
            initial_prompt=model.initial_prompt,
            max_duration_seconds=model.max_duration_seconds,
            cpu_limit=model.cpu_limit,
            memory_limit_mb=model.memory_limit_mb,
            metrics=metrics or ExecutionMetrics(),
            checkpoints=checkpoints,
            created_by=model.created_by,
            tags=model.tags,
            metadata=model.metadata,
        )
        
        # Set version for optimistic locking
        if hasattr(model, 'version'):
            entity.metadata['version'] = model.version
        
        return entity
    
    def _to_model(
        self,
        entity: SessionEntity,
        existing_model: Optional[SessionModel] = None
    ) -> SessionModel:
        """Convert domain entity to database model"""
        if existing_model:
            model = existing_model
        else:
            model = SessionModel(id=entity.id)
        
        # Update basic fields
        model.title = entity.title
        model.description = entity.description
        model.session_type = SessionTypeDB(entity.session_type.value)
        model.priority = SessionPriorityDB(entity.priority.value)
        model.status = SessionStatusDB(entity.status.value)
        model.status_updated_at = entity.status_updated_at
        model.parent_id = entity.parent_id
        model.agent_config = entity.agent_config
        model.model_config = entity.model_config
        model.initial_prompt = entity.initial_prompt
        model.max_duration_seconds = entity.max_duration_seconds
        model.cpu_limit = entity.cpu_limit
        model.memory_limit_mb = entity.memory_limit_mb
        model.created_by = entity.created_by
        model.tags = entity.tags
        model.metadata = entity.metadata
        
        # Handle metrics
        if entity.metrics and not model.metrics:
            model.metrics = SessionMetricsModel(
                id=UUID(int=0),  # Will be generated by database
                session_id=entity.id,
                created_at=entity.metrics.created_at,
                started_at=entity.metrics.started_at,
                completed_at=entity.metrics.completed_at,
                failed_at=entity.metrics.failed_at,
                queue_duration_seconds=entity.metrics.queue_duration_seconds,
                execution_duration_seconds=entity.metrics.execution_duration_seconds,
                total_duration_seconds=entity.metrics.total_duration_seconds,
                cpu_usage_percent=entity.metrics.cpu_usage_percent,
                memory_usage_mb=entity.metrics.memory_usage_mb,
                disk_usage_mb=entity.metrics.disk_usage_mb,
                network_bytes_sent=entity.metrics.network_bytes_sent,
                network_bytes_received=entity.metrics.network_bytes_received,
                total_tokens_used=entity.metrics.total_tokens_used,
                api_calls_count=entity.metrics.api_calls_count,
                api_errors_count=entity.metrics.api_errors_count,
                retry_count=entity.metrics.retry_count,
                success_rate=entity.metrics.success_rate,
                confidence_score=entity.metrics.confidence_score,
                code_quality_score=entity.metrics.code_quality_score,
                result=entity.metrics.result,
                error=entity.metrics.error,
                warnings=entity.metrics.warnings,
                checkpoint_count=entity.metrics.checkpoint_count,
                last_checkpoint_at=entity.metrics.last_checkpoint_at,
                estimated_cost_usd=entity.metrics.estimated_cost_usd,
            )
        elif entity.metrics and model.metrics:
            # Update existing metrics
            model.metrics.started_at = entity.metrics.started_at
            model.metrics.completed_at = entity.metrics.completed_at
            model.metrics.failed_at = entity.metrics.failed_at
            model.metrics.queue_duration_seconds = entity.metrics.queue_duration_seconds
            model.metrics.execution_duration_seconds = entity.metrics.execution_duration_seconds
            model.metrics.total_duration_seconds = entity.metrics.total_duration_seconds
            model.metrics.cpu_usage_percent = entity.metrics.cpu_usage_percent
            model.metrics.memory_usage_mb = entity.metrics.memory_usage_mb
            model.metrics.disk_usage_mb = entity.metrics.disk_usage_mb
            model.metrics.network_bytes_sent = entity.metrics.network_bytes_sent
            model.metrics.network_bytes_received = entity.metrics.network_bytes_received
            model.metrics.total_tokens_used = entity.metrics.total_tokens_used
            model.metrics.api_calls_count = entity.metrics.api_calls_count
            model.metrics.api_errors_count = entity.metrics.api_errors_count
            model.metrics.retry_count = entity.metrics.retry_count
            model.metrics.success_rate = entity.metrics.success_rate
            model.metrics.confidence_score = entity.metrics.confidence_score
            model.metrics.code_quality_score = entity.metrics.code_quality_score
            model.metrics.result = entity.metrics.result
            model.metrics.error = entity.metrics.error
            model.metrics.warnings = entity.metrics.warnings
            model.metrics.checkpoint_count = entity.metrics.checkpoint_count
            model.metrics.last_checkpoint_at = entity.metrics.last_checkpoint_at
            model.metrics.estimated_cost_usd = entity.metrics.estimated_cost_usd
        
        # Handle checkpoints
        if entity.checkpoints:
            # Clear existing checkpoints if updating
            if existing_model and model.checkpoints:
                model.checkpoints.clear()
            
            # Add new checkpoints
            for i, checkpoint_data in enumerate(entity.checkpoints, 1):
                checkpoint = SessionCheckpointModel(
                    session_id=entity.id,
                    sequence=i,
                    data=checkpoint_data.get('data', {}),
                    metadata=checkpoint_data.get('metadata', {})
                )
                if 'timestamp' in checkpoint_data:
                    try:
                        checkpoint.created_at = datetime.fromisoformat(
                            checkpoint_data['timestamp'].replace('Z', '+00:00')
                        )
                    except (ValueError, TypeError):
                        pass
                model.checkpoints.append(checkpoint)
        
        return model
    
    # Specialized query methods for sessions
    
    async def get_with_metrics(self, session_id: UUID) -> Optional[SessionEntity]:
        """Get session with eager-loaded metrics"""
        options = QueryOptions(
            eager_load=["metrics"],
            select_only=None  # Get all fields
        )
        return await self.get_by_id(session_id, options)
    
    async def get_with_checkpoints(self, session_id: UUID) -> Optional[SessionEntity]:
        """Get session with eager-loaded checkpoints"""
        options = QueryOptions(
            eager_load=["checkpoints"],
            select_only=None
        )
        return await self.get_by_id(session_id, options)
    
    async def get_full_session(self, session_id: UUID) -> Optional[SessionEntity]:
        """Get session with all relationships eager-loaded"""
        options = QueryOptions(
            eager_load=["metrics", "checkpoints", "parent", "children"],
            select_only=None
        )
        return await self.get_by_id(session_id, options)
    
    async def find_by_status(
        self,
        status: SessionStatus,
        options: QueryOptions = None
    ) -> List[SessionEntity]:
        """Find sessions by status"""
        filters = [
            FilterCondition(
                field="status",
                operator=FilterOperator.EQUALS,
                value=SessionStatusDB(status.value)
            )
        ]
        
        if options:
            options.filters.extend(filters)
        else:
            options = QueryOptions(filters=filters)
        
        return await self.find(options)
    
    async def find_active_sessions(
        self,
        options: QueryOptions = None
    ) -> List[SessionEntity]:
        """Find all active sessions (non-terminal)"""
        active_statuses = [
            SessionStatusDB.PENDING,
            SessionStatusDB.QUEUED,
            SessionStatusDB.RUNNING,
            SessionStatusDB.PAUSED,
            SessionStatusDB.DEGRADED,
        ]
        
        filters = [
            FilterCondition(
                field="status",
                operator=FilterOperator.IN,
                value=active_statuses
            )
        ]
        
        if options:
            options.filters.extend(filters)
        else:
            options = QueryOptions(filters=filters)
        
        return await self.find(options)
    
    async def find_by_parent(
        self,
        parent_id: UUID,
        options: QueryOptions = None
    ) -> List[SessionEntity]:
        """Find child sessions by parent ID"""
        filters = [
            FilterCondition(
                field="parent_id",
                operator=FilterOperator.EQUALS,
                value=parent_id
            )
        ]
        
        if options:
            options.filters.extend(filters)
        else:
            options = QueryOptions(filters=filters)
        
        return await self.find(options)
    
    async def find_by_priority(
        self,
        priority: SessionPriority,
        options: QueryOptions = None
    ) -> List[SessionEntity]:
        """Find sessions by priority"""
        filters = [
            FilterCondition(
                field="priority",
                operator=FilterOperator.EQUALS,
                value=SessionPriorityDB(priority.value)
            )
        ]
        
        if options:
            options.filters.extend(filters)
        else:
            options = QueryOptions(filters=filters)
        
        return await self.find(options)
    
    async def find_by_type(
        self,
        session_type: SessionType,
        options: QueryOptions = None
    ) -> List[SessionEntity]:
        """Find sessions by type"""
        filters = [
            FilterCondition(
                field="session_type",
                operator=FilterOperator.EQUALS,
                value=SessionTypeDB(session_type.value)
            )
        ]
        
        if options:
            options.filters.extend(filters)
        else:
            options = QueryOptions(filters=filters)
        
        return await self.find(options)
    
    async def find_expired_sessions(
        self,
        max_age_hours: int = 24
    ) -> List[SessionEntity]:
        """Find sessions that have exceeded their max duration"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        # This requires a more complex query with metrics join
        async with self._get_session() as session:
            query = select(SessionModel).join(
                SessionMetricsModel,
                SessionModel.metrics_id == SessionMetricsModel.id
            ).where(
                and_(
                    SessionModel.status.in_([
                        SessionStatusDB.RUNNING,
                        SessionStatusDB.PAUSED,
                        SessionStatusDB.DEGRADED,
                    ]),
                    SessionMetricsModel.started_at < cutoff_time,
                    SessionModel.deleted_at.is_(None)
                )
            )
            
            result = await session.execute(query)
            models = result.scalars().all()
            
            return [self._to_entity(model) for model in models]
    
    async def get_session_tree(
        self,
        root_session_id: UUID,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Get hierarchical session tree
        
        Uses recursive CTE for efficient tree traversal
        """
        async with self._get_session() as session:
            # Recursive CTE for hierarchical query
            cte_query = text(f"""
                WITH RECURSIVE session_tree AS (
                    -- Anchor: root session
                    SELECT 
                        id,
                        title,
                        status,
                        parent_id,
                        session_type,
                        1 as depth,
                        ARRAY[id] as path
                    FROM sessions
                    WHERE id = :root_id
                    
                    UNION ALL
                    
                    -- Recursive: child sessions
                    SELECT 
                        s.id,
                        s.title,
                        s.status,
                        s.parent_id,
                        s.session_type,
                        st.depth + 1,
                        st.path || s.id
                    FROM sessions s
                    JOIN session_tree st ON s.parent_id = st.id
                    WHERE st.depth < :max_depth
                      AND s.deleted_at IS NULL
                )
                SELECT * FROM session_tree
                ORDER BY path
            """)
            
            result = await session.execute(
                cte_query,
                {"root_id": root_session_id, "max_depth": max_depth}
            )
            
            rows = result.fetchall()
            
            # Build tree structure
            tree_map = {}
            root = None
            
            for row in rows:
                node = {
                    "id": str(row.id),
                    "title": row.title,
                    "status": row.status,
                    "session_type": row.session_type,
                    "depth": row.depth,
                    "children": []
                }
                
                tree_map[str(row.id)] = node
                
                if row.parent_id:
                    parent_id = str(row.parent_id)
                    if parent_id in tree_map:
                        tree_map[parent_id]["children"].append(node)
                else:
                    root = node
            
            return root or {}
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get comprehensive session statistics"""
        async with self._get_session() as session:
            # Status distribution
            status_query = text("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
                FROM sessions
                WHERE deleted_at IS NULL
                GROUP BY status
                ORDER BY count DESC
            """)
            
            # Type distribution
            type_query = text("""
                SELECT 
                    session_type,
                    COUNT(*) as count
                FROM sessions
                WHERE deleted_at IS NULL
                GROUP BY session_type
                ORDER BY count DESC
            """)
            
            # Priority distribution
            priority_query = text("""
                SELECT 
                    priority,
                    COUNT(*) as count
                FROM sessions
                WHERE deleted_at IS NULL
                GROUP BY priority
                ORDER BY priority
            """)
            
            # Duration statistics
            duration_query = text("""
                SELECT 
                    COUNT(*) as total_sessions,
                    AVG(sm.total_duration_seconds) as avg_duration,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sm.total_duration_seconds) as median_duration,
                    MIN(sm.total_duration_seconds) as min_duration,
                    MAX(sm.total_duration_seconds) as max_duration
                FROM sessions s
                JOIN session_metrics sm ON s.metrics_id = sm.id
                WHERE s.deleted_at IS NULL
                  AND sm.total_duration_seconds IS NOT NULL
            """)
            
            # Execute all queries
            status_result = await session.execute(status_query)
            type_result = await session.execute(type_query)
            priority_result = await session.execute(priority_query)
            duration_result = await session.execute(duration_query)
            
            # Build stats dictionary
            stats = {
                "status_distribution": [
                    {"status": row.status, "count": row.count, "percentage": float(row.percentage or 0)}
                    for row in status_result.fetchall()
                ],
                "type_distribution": [
                    {"type": row.session_type, "count": row.count}
                    for row in type_result.fetchall()
                ],
                "priority_distribution": [
                    {"priority": row.priority, "count": row.count}
                    for row in priority_result.fetchall()
                ],
                "duration_stats": {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Add duration stats if available
            duration_row = duration_result.fetchone()
            if duration_row:
                stats["duration_stats"] = {
                    "total_sessions": duration_row.total_sessions or 0,
                    "avg_duration_seconds": float(duration_row.avg_duration or 0),
                    "median_duration_seconds": float(duration_row.median_duration or 0),
                    "min_duration_seconds": float(duration_row.min_duration or 0),
                    "max_duration_seconds": float(duration_row.max_duration or 0),
                }
            
            return stats
    
    async def update_status(
        self,
        session_id: UUID,
        new_status: SessionStatus,
        error_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update session status with industrial validation"""
        async with self._get_session() as session:
            # Get current session
            query = select(SessionModel).where(
                SessionModel.id == session_id
            )
            result = await session.execute(query)
            session_model = result.scalar_one_or_none()
            
            if not session_model:
                raise EntityNotFoundError(f"Session not found: {session_id}")
            
            # Validate status transition
            current_status = SessionStatus(session_model.status.value)
            if not current_status.can_transition_to(new_status):
                raise ValueError(
                    f"Invalid status transition from {current_status} to {new_status}"
                )
            
            # Update status
            session_model.status = SessionStatusDB(new_status.value)
            session_model.status_updated_at = datetime.now(timezone.utc)
            
            # Update metrics if needed
            if session_model.metrics:
                if new_status == SessionStatus.RUNNING and not session_model.metrics.started_at:
                    session_model.metrics.started_at = datetime.now(timezone.utc)
                elif new_status == SessionStatus.COMPLETED and not session_model.metrics.completed_at:
                    session_model.metrics.completed_at = datetime.now(timezone.utc)
                elif new_status == SessionStatus.FAILED and not session_model.metrics.failed_at:
                    session_model.metrics.failed_at = datetime.now(timezone.utc)
                    if error_context:
                        session_model.metrics.error = error_context
            
            # Invalidate cache
            await self._cache_delete(f"id:{session_id}")
            
            await session.commit()
            return True
    
    async def add_checkpoint(
        self,
        session_id: UUID,
        checkpoint_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add checkpoint to session"""
        async with self._get_session() as session:
            # Get session with checkpoints
            query = select(SessionModel).options(
                selectinload(SessionModel.checkpoints)
            ).where(
                SessionModel.id == session_id
            )
            result = await session.execute(query)
            session_model = result.scalar_one_or_none()
            
            if not session_model:
                raise EntityNotFoundError(f"Session not found: {session_id}")
            
            # Determine next sequence number
            next_sequence = 1
            if session_model.checkpoints:
                next_sequence = max(cp.sequence for cp in session_model.checkpoints) + 1
            
            # Create checkpoint
            checkpoint = SessionCheckpointModel(
                session_id=session_id,
                sequence=next_sequence,
                data=checkpoint_data,
                created_at=datetime.now(timezone.utc)
            )
            
            session.add(checkpoint)
            
            # Update metrics checkpoint count
            if session_model.metrics:
                session_model.metrics.checkpoint_count = next_sequence
                session_model.metrics.last_checkpoint_at = datetime.now(timezone.utc)
            
            await session.commit()
            
            # Invalidate cache
            await self._cache_delete(f"id:{session_id}")
            
            return {
                "sequence": next_sequence,
                "timestamp": checkpoint.created_at.isoformat(),
                "data": checkpoint_data
            }
    
    async def bulk_update_status(
        self,
        session_ids: List[UUID],
        new_status: SessionStatus
    ) -> int:
        """Bulk update session statuses"""
        async with self._get_session() as session:
            update_stmt = update(SessionModel).where(
                SessionModel.id.in_(session_ids)
            ).values(
                status=SessionStatusDB(new_status.value),
                status_updated_at=datetime.now(timezone.utc)
            )
            
            result = await session.execute(update_stmt)
            updated_count = result.rowcount
            
            # Invalidate cache for all updated sessions
            for session_id in session_ids:
                await self._cache_delete(f"id:{session_id}")
            
            await session.commit()
            return updated_count
    
    async def cleanup_old_sessions(
        self,
        older_than_days: int = 30,
        batch_size: int = 1000
    ) -> Dict[str, int]:
        """
        Clean up old sessions (soft delete)
        
        Industrial cleanup with:
        1. Batch processing for performance
        2. Progress reporting
        3. Transaction safety
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        
        stats = {
            "total_sessions": 0,
            "sessions_cleaned": 0,
            "batches_processed": 0,
            "errors": 0,
        }
        
        try:
            # Get total count
            async with self._get_session() as session:
                count_query = select(func.count()).where(
                    and_(
                        SessionModel.created_at < cutoff_date,
                        SessionModel.deleted_at.is_(None)
                    )
                )
                result = await session.execute(count_query)
                stats["total_sessions"] = result.scalar() or 0
            
            # Process in batches
            offset = 0
            while True:
                async with self._get_session() as session:
                    # Get batch of old session IDs
                    query = select(SessionModel.id).where(
                        and_(
                            SessionModel.created_at < cutoff_date,
                            SessionModel.deleted_at.is_(None)
                        )
                    ).order_by(
                        SessionModel.created_at
                    ).limit(
                        batch_size
                    ).offset(
                        offset
                    )
                    
                    result = await session.execute(query)
                    session_ids = [row[0] for row in result.fetchall()]
                    
                    if not session_ids:
                        break  # No more sessions
                    
                    # Soft delete batch
                    update_stmt = update(SessionModel).where(
                        SessionModel.id.in_(session_ids)
                    ).values(
                        deleted_at=datetime.now(timezone.utc)
                    )
                    
                    await session.execute(update_stmt)
                    await session.commit()
                    
                    # Update stats
                    stats["sessions_cleaned"] += len(session_ids)
                    stats["batches_processed"] += 1
                    
                    # Invalidate cache
                    for session_id in session_ids:
                        await self._cache_delete(f"id:{session_id}")
                    
                    offset += batch_size
                    
        except Exception as e:
            stats["errors"] += 1
            raise RepositoryError(f"Error cleaning up old sessions: {e}")
        
        return stats
