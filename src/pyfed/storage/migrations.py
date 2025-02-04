from typing import Dict, Any, List, Optional
import importlib
import pkgutil
import asyncio
from datetime import datetime
from pathlib import Path
import aiosqlite
import asyncpg
from enum import Enum

from ..utils.exceptions import MigrationError
from ..utils.logging import get_logger

logger = get_logger(__name__)

class DatabaseType(Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"

class MigrationInfo:
    """Migration metadata."""
    def __init__(self,
                 version: str,
                 name: str,
                 description: str,
                 applied_at: Optional[datetime] = None):
        self.version = version
        self.name = name
        self.description = description
        self.applied_at = applied_at

class MigrationManager:
    """Database migration manager."""

    def __init__(self,
                 db_type: DatabaseType,
                 connection_string: str,
                 migrations_dir: str = "migrations"):
        self.db_type = db_type
        self.connection_string = connection_string
        self.migrations_dir = Path(migrations_dir)
        self.conn = None

    async def initialize(self) -> None:
        """Initialize migration system."""
        try:
            # Connect to database
            if self.db_type == DatabaseType.SQLITE:
                self.conn = await aiosqlite.connect(self.connection_string)
            else:
                self.conn = await asyncpg.connect(self.connection_string)

            # Create migrations table
            await self._create_migrations_table()
            
        except Exception as e:
            logger.error(f"Failed to initialize migrations: {e}")
            raise MigrationError(f"Migration initialization failed: {e}")

    async def _create_migrations_table(self) -> None:
        """Create migrations tracking table."""
        if self.db_type == DatabaseType.SQLITE:
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await self.conn.commit()
        else:
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)

    async def get_applied_migrations(self) -> List[MigrationInfo]:
        """Get list of applied migrations."""
        try:
            if self.db_type == DatabaseType.SQLITE:
                async with self.conn.execute(
                    "SELECT version, name, description, applied_at FROM migrations ORDER BY version"
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [
                        MigrationInfo(
                            version=row[0],
                            name=row[1],
                            description=row[2],
                            applied_at=datetime.fromisoformat(row[3])
                        )
                        for row in rows
                    ]
            else:
                rows = await self.conn.fetch(
                    "SELECT version, name, description, applied_at FROM migrations ORDER BY version"
                )
                return [
                    MigrationInfo(
                        version=row['version'],
                        name=row['name'],
                        description=row['description'],
                        applied_at=row['applied_at']
                    )
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            raise MigrationError(f"Failed to get applied migrations: {e}")

    async def get_pending_migrations(self) -> List[MigrationInfo]:
        """Get list of pending migrations."""
        try:
            applied = await self.get_applied_migrations()
            applied_versions = {m.version for m in applied}
            
            pending = []
            for migration in self._load_migrations():
                if migration.version not in applied_versions:
                    pending.append(migration)
                    
            return sorted(pending, key=lambda m: m.version)
            
        except Exception as e:
            logger.error(f"Failed to get pending migrations: {e}")
            raise MigrationError(f"Failed to get pending migrations: {e}")

    def _load_migrations(self) -> List[MigrationInfo]:
        """Load migration files."""
        migrations = []
        
        for item in sorted(self.migrations_dir.glob("*.sql")):
            version = item.stem
            with open(item) as f:
                description = f.readline().strip("-- ").strip()
                migrations.append(MigrationInfo(
                    version=version,
                    name=item.name,
                    description=description
                ))
                
        return migrations

    async def migrate(self, target_version: Optional[str] = None) -> None:
        """
        Run migrations up to target version.
        
        Args:
            target_version: Version to migrate to, or None for latest
        """
        try:
            pending = await self.get_pending_migrations()
            if not pending:
                logger.info("No pending migrations")
                return
                
            for migration in pending:
                if target_version and migration.version > target_version:
                    break
                    
                logger.info(f"Applying migration {migration.version}: {migration.name}")
                
                # Read migration file
                with open(self.migrations_dir / migration.name) as f:
                    sql = f.read()
                
                # Apply migration
                if self.db_type == DatabaseType.SQLITE:
                    await self.conn.executescript(sql)
                    await self.conn.execute(
                        """
                        INSERT INTO migrations (version, name, description)
                        VALUES (?, ?, ?)
                        """,
                        (migration.version, migration.name, migration.description)
                    )
                    await self.conn.commit()
                else:
                    async with self.conn.transaction():
                        await self.conn.execute(sql)
                        await self.conn.execute(
                            """
                            INSERT INTO migrations (version, name, description)
                            VALUES ($1, $2, $3)
                            """,
                            migration.version,
                            migration.name,
                            migration.description
                        )
                        
                logger.info(f"Applied migration {migration.version}")
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise MigrationError(f"Migration failed: {e}")

    async def rollback(self, target_version: str) -> None:
        """
        Rollback migrations to target version.
        
        Args:
            target_version: Version to rollback to
        """
        try:
            applied = await self.get_applied_migrations()
            to_rollback = [
                m for m in reversed(applied)
                if m.version > target_version
            ]
            
            for migration in to_rollback:
                logger.info(f"Rolling back migration {migration.version}")
                
                # Read rollback file
                rollback_file = self.migrations_dir / f"{migration.version}_rollback.sql"
                if not rollback_file.exists():
                    raise MigrationError(
                        f"No rollback file for migration {migration.version}"
                    )
                    
                with open(rollback_file) as f:
                    sql = f.read()
                
                # Apply rollback
                if self.db_type == DatabaseType.SQLITE:
                    await self.conn.executescript(sql)
                    await self.conn.execute(
                        "DELETE FROM migrations WHERE version = ?",
                        (migration.version,)
                    )
                    await self.conn.commit()
                else:
                    async with self.conn.transaction():
                        await self.conn.execute(sql)
                        await self.conn.execute(
                            "DELETE FROM migrations WHERE version = $1",
                            migration.version
                        )
                        
                logger.info(f"Rolled back migration {migration.version}")
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise MigrationError(f"Rollback failed: {e}")

    async def close(self) -> None:
        """Close database connection."""
        if self.conn:
            await self.conn.close()