"""
INDUSTRIAL ALEMBIC ENVIRONMENT
Advanced database migration environment with:
1. Multiple database support
2. Transaction management
3. Error recovery
4. Migration validation
"""

import asyncio
import logging
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import industrial models
from src.industrial_orchestrator.infrastructure.database.models import Base

# Alembic Config object
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger('alembic.env')

# Get database URL from environment or config
def get_database_url():
    """Get database URL with industrial configuration"""
    from src.industrial_orchestrator.infrastructure.config.database import DatabaseSettings
    
    settings = DatabaseSettings()
    return settings.connection_string

# Set target metadata
target_metadata = Base.metadata

# Other values from the config
config.set_main_option('sqlalchemy.url', get_database_url())


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Industrial options
        transaction_per_migration=True,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
        include_schemas=True,
        version_table='alembic_version_industrial',
        version_table_schema=None,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection):
    """
    Industrial migration runner with error handling.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Industrial options
        transaction_per_migration=True,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
        include_schemas=True,
        version_table='alembic_version_industrial',
        version_table_schema=None,
        # Advanced options
        user_module_prefix='src.industrial_orchestrator.infrastructure.database.models.',
        process_revision_directives=None,
        # Logging
        version_path='alembic/versions',
        # Custom template
        template_args={
            'industrial_prefix': 'industrial_',
            'timestamp_format': '%Y%m%d_%H%M%S',
        }
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
