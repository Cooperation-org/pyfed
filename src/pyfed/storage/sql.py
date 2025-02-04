"""
SQL storage backend for ActivityPub data.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import enum
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy import Index, UniqueConstraint, event

from .base import BaseStorageBackend
from ..utils.exceptions import StorageError
from ..utils.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()

class ActivityType(enum.Enum):
    """Activity types."""
    CREATE = "Create"
    FOLLOW = "Follow"
    LIKE = "Like"
    ANNOUNCE = "Announce"
    DELETE = "Delete"
    UPDATE = "Update"
    UNDO = "Undo"
    ACCEPT = "Accept"
    REJECT = "Reject"
    ADD = "Add"
    REMOVE = "Remove"
    BLOCK = "Block"

class ObjectType(enum.Enum):
    """Object types."""
    NOTE = "Note"
    ARTICLE = "Article"
    IMAGE = "Image"
    VIDEO = "Video"
    AUDIO = "Audio"
    PERSON = "Person"
    GROUP = "Group"
    ORGANIZATION = "Organization"
    COLLECTION = "Collection"
    ORDERED_COLLECTION = "OrderedCollection"

class Activity(Base):
    """Activity table with enhanced indexing and relationships."""
    __tablename__ = 'activities'
    
    id = sa.Column(sa.String, primary_key=True)
    type = sa.Column(sa.Enum(ActivityType), nullable=False)
    actor = sa.Column(sa.String, sa.ForeignKey('actors.id'), nullable=False)
    object_id = sa.Column(sa.String, sa.ForeignKey('objects.id'), nullable=True)
    target_id = sa.Column(sa.String, sa.ForeignKey('objects.id'), nullable=True)
    data = sa.Column(JSONB, nullable=False)
    local = sa.Column(sa.Boolean, default=False)
    visibility = sa.Column(sa.String, default='public')
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    # Relationships
    actor_obj = relationship("Actor", back_populates="activities")
    object = relationship("Object", foreign_keys=[object_id])
    target = relationship("Object", foreign_keys=[target_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_activities_type', 'type'),
        Index('idx_activities_actor', 'actor'),
        Index('idx_activities_object', 'object_id'),
        Index('idx_activities_target', 'target_id'),
        Index('idx_activities_created', 'created_at'),
        Index('idx_activities_visibility', 'visibility'),
        Index('idx_activities_local', 'local'),
    )

class Object(Base):
    """Object table with enhanced indexing and relationships."""
    __tablename__ = 'objects'
    
    id = sa.Column(sa.String, primary_key=True)
    type = sa.Column(sa.Enum(ObjectType), nullable=False)
    attributed_to = sa.Column(sa.String, sa.ForeignKey('actors.id'), nullable=True)
    data = sa.Column(JSONB, nullable=False)
    local = sa.Column(sa.Boolean, default=False)
    visibility = sa.Column(sa.String, default='public')
    content = sa.Column(sa.Text, nullable=True)  # Extracted content for search
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, onupdate=datetime.utcnow)
    deleted_at = sa.Column(sa.DateTime, nullable=True)
    
    # Relationships
    attributed_to_actor = relationship("Actor", back_populates="objects")
    activities_as_object = relationship("Activity", foreign_keys=[Activity.object_id])
    activities_as_target = relationship("Activity", foreign_keys=[Activity.target_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_objects_type', 'type'),
        Index('idx_objects_attributed', 'attributed_to'),
        Index('idx_objects_created', 'created_at'),
        Index('idx_objects_updated', 'updated_at'),
        Index('idx_objects_visibility', 'visibility'),
        Index('idx_objects_local', 'local'),
        Index('idx_objects_content', 'content', postgresql_using='gin'),
    )

class Actor(Base):
    """Actor table with enhanced indexing and relationships."""
    __tablename__ = 'actors'
    
    id = sa.Column(sa.String, primary_key=True)
    type = sa.Column(sa.Enum(ObjectType), nullable=False)
    username = sa.Column(sa.String)
    domain = sa.Column(sa.String, nullable=False)
    inbox_url = sa.Column(sa.String)
    outbox_url = sa.Column(sa.String)
    following_url = sa.Column(sa.String)
    followers_url = sa.Column(sa.String)
    shared_inbox_url = sa.Column(sa.String, nullable=True)
    public_key = sa.Column(sa.Text, nullable=True)
    private_key = sa.Column(sa.Text, nullable=True)
    local = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, onupdate=datetime.utcnow)
    last_fetched_at = sa.Column(sa.DateTime, nullable=True)
    
    # Relationships
    activities = relationship("Activity", back_populates="actor_obj")
    objects = relationship("Object", back_populates="attributed_to_actor")
    followers = relationship("Follow", foreign_keys="Follow.following", back_populates="following_actor")
    following = relationship("Follow", foreign_keys="Follow.follower", back_populates="follower_actor")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('username', 'domain', name='uq_actor_username_domain'),
        Index('idx_actors_username_domain', 'username', 'domain'),
        Index('idx_actors_domain', 'domain'),
        Index('idx_actors_local', 'local'),
        Index('idx_actors_type', 'type'),
    )

class Follow(Base):
    """Follow relationship table with enhanced indexing."""
    __tablename__ = 'follows'
    
    id = sa.Column(sa.Integer, primary_key=True)
    follower = sa.Column(sa.String, sa.ForeignKey('actors.id'), nullable=False)
    following = sa.Column(sa.String, sa.ForeignKey('actors.id'), nullable=False)
    accepted = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    accepted_at = sa.Column(sa.DateTime, nullable=True)
    
    # Relationships
    follower_actor = relationship("Actor", foreign_keys=[follower], back_populates="following")
    following_actor = relationship("Actor", foreign_keys=[following], back_populates="followers")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('follower', 'following', name='uq_follow_relationship'),
        Index('idx_follows_follower', 'follower'),
        Index('idx_follows_following', 'following'),
        Index('idx_follows_accepted', 'accepted'),
    )

class Like(Base):
    """Like relationship table."""
    __tablename__ = 'likes'
    
    id = sa.Column(sa.Integer, primary_key=True)
    actor_id = sa.Column(sa.String, sa.ForeignKey('actors.id'), nullable=False)
    object_id = sa.Column(sa.String, sa.ForeignKey('objects.id'), nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    # Relationships
    actor = relationship("Actor")
    object = relationship("Object")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('actor_id', 'object_id', name='uq_like_relationship'),
        Index('idx_likes_actor', 'actor_id'),
        Index('idx_likes_object', 'object_id'),
    )

class SQLStorageBackend(BaseStorageBackend):
    """SQL storage backend implementation with enhanced features."""
    
    def __init__(self, database_url: str):
        """Initialize storage backend."""
        self.database_url = database_url
        self.engine = None
        self.async_session = None
        
    async def initialize(self) -> None:
        """Initialize database connection."""
        try:
            self.engine = create_async_engine(
                self.database_url,
                pool_size=20,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=300,
            )
            
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise StorageError(f"Database initialization failed: {e}")
            
    async def bulk_create_activities(
        self,
        activities: List[Dict[str, Any]]
    ) -> List[str]:
        """Bulk create activities."""
        if not activities:
            return []
            
        activity_models = []
        activity_ids = []
        
        async with self.async_session() as session:
            async with session.begin():
                for activity_data in activities:
                    activity_id = activity_data.get('id')
                    if not activity_id:
                        raise StorageError("Activity must have an ID")
                        
                    activity_ids.append(activity_id)
                    activity = Activity(
                        id=activity_id,
                        type=ActivityType(activity_data.get('type')),
                        actor=activity_data.get('actor'),
                        object_id=activity_data.get('object', {}).get('id'),
                        target_id=activity_data.get('target', {}).get('id'),
                        data=activity_data,
                        local=activity_data.get('local', False),
                        visibility=activity_data.get('visibility', 'public')
                    )
                    activity_models.append(activity)
                    
                session.add_all(activity_models)
                await session.commit()
                
        return activity_ids
        
    async def bulk_create_objects(
        self,
        objects: List[Dict[str, Any]]
    ) -> List[str]:
        """Bulk create objects."""
        if not objects:
            return []
            
        object_models = []
        object_ids = []
        
        async with self.async_session() as session:
            async with session.begin():
                for obj_data in objects:
                    object_id = obj_data.get('id')
                    if not object_id:
                        raise StorageError("Object must have an ID")
                        
                    object_ids.append(object_id)
                    obj = Object(
                        id=object_id,
                        type=ObjectType(obj_data.get('type')),
                        attributed_to=obj_data.get('attributedTo'),
                        data=obj_data,
                        local=obj_data.get('local', False),
                        visibility=obj_data.get('visibility', 'public'),
                        content=obj_data.get('content')
                    )
                    object_models.append(obj)
                    
                session.add_all(object_models)
                await session.commit()
                
        return object_ids
        
    async def get_collection(
        self,
        collection_id: str,
        page_size: int = 20,
        cursor: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get paginated collection."""
        collection_parts = collection_id.split('/')
        collection_type = collection_parts[-1]
        actor_id = '/'.join(collection_parts[:-1])
        
        async with self.async_session() as session:
            if collection_type in ['followers', 'following']:
                query = select(Follow).where(
                    and_(
                        Follow.following == actor_id if collection_type == 'followers' else Follow.follower == actor_id,
                        Follow.accepted == True
                    )
                ).order_by(Follow.created_at.desc())
                
            elif collection_type in ['likes']:
                query = select(Like).where(
                    Like.object_id == actor_id
                ).order_by(Like.created_at.desc())
                
            elif collection_type in ['outbox']:
                query = select(Activity).where(
                    and_(
                        Activity.actor == actor_id,
                        Activity.visibility == 'public'
                    )
                ).order_by(Activity.created_at.desc())
                
            elif collection_type in ['inbox']:
                query = select(Activity).where(
                    or_(
                        and_(
                            Activity.target_id == actor_id,
                            Activity.visibility.in_(['public', 'followers'])
                        ),
                        Activity.actor == actor_id
                    )
                ).order_by(Activity.created_at.desc())
                
            else:
                raise StorageError(f"Unsupported collection type: {collection_type}")
                
            if cursor:
                query = query.where(Activity.created_at < cursor)
                
            query = query.limit(page_size + 1)
            result = await session.execute(query)
            items = result.scalars().all()
            
            next_cursor = None
            if len(items) > page_size:
                next_cursor = str(items[page_size].created_at)
                items = items[:page_size]
                
            return [item.data for item in items], next_cursor
            
    async def search_objects(
        self,
        query: str,
        object_type: Optional[ObjectType] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search objects by content."""
        async with self.async_session() as session:
            stmt = select(Object).where(
                Object.content.ilike(f"%{query}%")
            )
            
            if object_type:
                stmt = stmt.where(Object.type == object_type)
                
            stmt = stmt.order_by(Object.created_at.desc()).offset(offset).limit(limit)
            
            result = await session.execute(stmt)
            objects = result.scalars().all()
            return [obj.data for obj in objects]
            
    async def get_actor_stats(self, actor_id: str) -> Dict[str, int]:
        """Get actor statistics."""
        async with self.async_session() as session:
            # Count followers
            followers = await session.execute(
                select(sa.func.count()).where(
                    and_(
                        Follow.following == actor_id,
                        Follow.accepted == True
                    )
                )
            )
            
            # Count following
            following = await session.execute(
                select(sa.func.count()).where(
                    and_(
                        Follow.follower == actor_id,
                        Follow.accepted == True
                    )
                )
            )
            
            # Count posts
            posts = await session.execute(
                select(sa.func.count()).where(
                    and_(
                        Activity.actor == actor_id,
                        Activity.type == ActivityType.CREATE
                    )
                )
            )
            
            return {
                "followers_count": followers.scalar(),
                "following_count": following.scalar(),
                "posts_count": posts.scalar()
            }

    async def create_activity(self, activity: Dict[str, Any]) -> str:
        """Store activity."""
        try:
            activity_id = activity.get('id')
            if not activity_id:
                raise StorageError("Activity has no ID")
                
            async with self.async_session() as session:
                db_activity = Activity(
                    id=activity_id,
                    type=ActivityType(activity.get('type')),
                    actor=activity.get('actor'),
                    object_id=activity.get('object', {}).get('id'),
                    target_id=activity.get('target', {}).get('id'),
                    data=activity,
                    local=activity.get('local', False),
                    visibility=activity.get('visibility', 'public')
                )
                session.add(db_activity)
                await session.commit()
                
            return activity_id
            
        except Exception as e:
            logger.error(f"Failed to create activity: {e}")
            raise StorageError(f"Failed to create activity: {e}")
            
    async def create_object(self, obj: Dict[str, Any]) -> str:
        """Store object."""
        try:
            object_id = obj.get('id')
            if not object_id:
                raise StorageError("Object has no ID")
                
            async with self.async_session() as session:
                db_object = Object(
                    id=object_id,
                    type=ObjectType(obj.get('type')),
                    attributed_to=obj.get('attributedTo'),
                    data=obj,
                    local=obj.get('local', False),
                    visibility=obj.get('visibility', 'public'),
                    content=obj.get('content')
                )
                session.add(db_object)
                await session.commit()
                
            return object_id
            
        except Exception as e:
            logger.error(f"Failed to create object: {e}")
            raise StorageError(f"Failed to create object: {e}")
            
    async def create_actor(self, actor: Dict[str, Any]) -> str:
        """Store actor."""
        try:
            actor_id = actor.get('id')
            if not actor_id:
                raise StorageError("Actor has no ID")
                
            async with self.async_session() as session:
                db_actor = Actor(
                    id=actor_id,
                    type=ObjectType(actor.get('type')),
                    username=actor.get('preferredUsername'),
                    domain=actor.get('domain'),
                    inbox_url=actor.get('inbox'),
                    outbox_url=actor.get('outbox'),
                    following_url=actor.get('following'),
                    followers_url=actor.get('followers'),
                    shared_inbox_url=actor.get('sharedInbox'),
                    public_key=actor.get('publicKey'),
                    private_key=actor.get('privateKey'),
                    local=actor.get('local', False)
                )
                session.add(db_actor)
                await session.commit()
                
            return actor_id
            
        except Exception as e:
            logger.error(f"Failed to create actor: {e}")
            raise StorageError(f"Failed to create actor: {e}")
            
    async def create_follow(self, follower: str, following: str) -> None:
        """Create follow relationship."""
        try:
            async with self.async_session() as session:
                follow = Follow(follower=follower, following=following)
                session.add(follow)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to create follow: {e}")
            raise StorageError(f"Failed to create follow: {e}")
            
    async def get_inbox(self, actor_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get actor's inbox."""
        try:
            async with self.async_session() as session:
                query = select(Activity).where(
                    or_(
                        and_(
                            Activity.target_id == actor_id,
                            Activity.visibility.in_(['public', 'followers'])
                        ),
                        Activity.actor == actor_id
                    )
                ).order_by(
                    Activity.created_at.desc()
                ).offset(offset).limit(limit)
                
                result = await session.execute(query)
                activities = result.scalars().all()
                
                return [activity.data for activity in activities]
                
        except Exception as e:
            logger.error(f"Failed to get inbox: {e}")
            raise StorageError(f"Failed to get inbox: {e}")
            
    async def get_outbox(self, actor_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get actor's outbox."""
        try:
            async with self.async_session() as session:
                query = select(Activity).where(
                    and_(
                        Activity.actor == actor_id,
                        Activity.visibility == 'public'
                    )
                ).order_by(
                    Activity.created_at.desc()
                ).offset(offset).limit(limit)
                
                result = await session.execute(query)
                activities = result.scalars().all()
                
                return [activity.data for activity in activities]
                
        except Exception as e:
            logger.error(f"Failed to get outbox: {e}")
            raise StorageError(f"Failed to get outbox: {e}")
            
    async def get_followers(self, actor_id: str) -> List[str]:
        """Get actor's followers."""
        try:
            async with self.async_session() as session:
                query = select(Follow.follower).where(
                    and_(
                        Follow.following == actor_id,
                        Follow.accepted == True
                    )
                )
                result = await session.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to get followers: {e}")
            raise StorageError(f"Failed to get followers: {e}")
            
    async def get_following(self, actor_id: str) -> List[str]:
        """Get actors that this actor is following."""
        try:
            async with self.async_session() as session:
                query = select(Follow.following).where(
                    and_(
                        Follow.follower == actor_id,
                        Follow.accepted == True
                    )
                )
                result = await session.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to get following: {e}")
            raise StorageError(f"Failed to get following: {e}")
            
    async def close(self) -> None:
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
