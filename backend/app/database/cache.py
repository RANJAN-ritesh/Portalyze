"""
Caching service for portfolio analysis results
Reduces API costs by ~80% through intelligent caching
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, delete
from app.database.models import Base, GradingCache, ShareableLink
from app.config import settings
import hashlib

logger = logging.getLogger(__name__)


class CacheService:
    """
    Intelligent caching service for portfolio analysis
    - Caches results for 7 days (configurable)
    - Tracks access patterns
    - Automatically cleans expired entries
    """

    def __init__(self):
        self.engine = create_async_engine(
            settings.database_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self._initialized = False

    async def initialize(self):
        """Initialize database tables"""
        if not self._initialized:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self._initialized = True
            logger.info("Cache database initialized")

    async def get_cached_result(self, portfolio_url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result if available and not expired

        Args:
            portfolio_url: The portfolio URL to check

        Returns:
            Cached result dict or None if not found/expired
        """
        if not settings.enable_caching:
            return None

        try:
            async with self.async_session() as session:
                # Query cache
                stmt = select(GradingCache).where(
                    GradingCache.portfolio_url == portfolio_url
                )
                result = await session.execute(stmt)
                cache_entry = result.scalar_one_or_none()

                if not cache_entry:
                    return None

                # Check if expired
                age = datetime.utcnow() - cache_entry.created_at
                if age.days > settings.cache_ttl_days:
                    # Delete expired entry
                    await session.delete(cache_entry)
                    await session.commit()
                    logger.info(f"Cache expired for {portfolio_url}")
                    return None

                # Update access tracking
                cache_entry.accessed_at = datetime.utcnow()
                cache_entry.access_count += 1
                await session.commit()

                # Return cached data
                logger.info(
                    f"Cache hit for {portfolio_url} "
                    f"(age: {age.days}d, accesses: {cache_entry.access_count})"
                )
                return json.loads(cache_entry.result_data)

        except Exception as e:
            logger.error(f"Cache retrieval error: {str(e)}")
            return None

    async def set_cached_result(
        self,
        portfolio_url: str,
        result_data: Dict[str, Any]
    ) -> bool:
        """
        Store result in cache

        Args:
            portfolio_url: Portfolio URL
            result_data: Complete analysis result

        Returns:
            True if cached successfully
        """
        if not settings.enable_caching:
            return False

        try:
            async with self.async_session() as session:
                # Check if already exists
                stmt = select(GradingCache).where(
                    GradingCache.portfolio_url == portfolio_url
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.result_data = json.dumps(result_data)
                    existing.created_at = datetime.utcnow()
                    existing.accessed_at = datetime.utcnow()
                else:
                    # Create new
                    cache_entry = GradingCache(
                        portfolio_url=portfolio_url,
                        result_data=json.dumps(result_data)
                    )
                    session.add(cache_entry)

                await session.commit()
                logger.info(f"Cached result for {portfolio_url}")
                return True

        except Exception as e:
            logger.error(f"Cache storage error: {str(e)}")
            return False

    async def create_shareable_link(
        self,
        portfolio_url: str,
        result_data: Dict[str, Any],
        expires_in_days: Optional[int] = None
    ) -> Optional[str]:
        """
        Create a shareable link for results

        Args:
            portfolio_url: Portfolio URL
            result_data: Analysis results
            expires_in_days: Optional expiration (None = never expires)

        Returns:
            Short share ID like 'abc123xyz' or None if failed
        """
        try:
            # Generate short ID (12 characters)
            share_id = self._generate_share_id(portfolio_url)

            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

            async with self.async_session() as session:
                # Check if already exists
                stmt = select(ShareableLink).where(
                    ShareableLink.share_id == share_id
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.result_data = json.dumps(result_data)
                    existing.expires_at = expires_at
                else:
                    # Create new
                    shareable = ShareableLink(
                        share_id=share_id,
                        portfolio_url=portfolio_url,
                        result_data=json.dumps(result_data),
                        expires_at=expires_at
                    )
                    session.add(shareable)

                await session.commit()
                logger.info(f"Created shareable link: {share_id}")
                return share_id

        except Exception as e:
            logger.error(f"Shareable link creation error: {str(e)}")
            return None

    async def get_shared_result(self, share_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve result by share ID

        Args:
            share_id: The short share ID

        Returns:
            Result data or None if not found/expired
        """
        try:
            async with self.async_session() as session:
                stmt = select(ShareableLink).where(
                    ShareableLink.share_id == share_id
                )
                result = await session.execute(stmt)
                shareable = result.scalar_one_or_none()

                if not shareable:
                    return None

                # Check expiration
                if shareable.expires_at and datetime.utcnow() > shareable.expires_at:
                    await session.delete(shareable)
                    await session.commit()
                    logger.info(f"Shareable link expired: {share_id}")
                    return None

                # Update view count
                shareable.view_count += 1
                await session.commit()

                return json.loads(shareable.result_data)

        except Exception as e:
            logger.error(f"Shared result retrieval error: {str(e)}")
            return None

    async def delete_cached_result(self, portfolio_url: str) -> bool:
        """
        Delete a specific cached result

        Args:
            portfolio_url: The portfolio URL to delete from cache

        Returns:
            True if deleted, False if not found
        """
        try:
            async with self.async_session() as session:
                stmt = select(GradingCache).where(
                    GradingCache.portfolio_url == portfolio_url
                )
                result = await session.execute(stmt)
                cache_entry = result.scalar_one_or_none()

                if cache_entry:
                    await session.delete(cache_entry)
                    await session.commit()
                    logger.info(f"Deleted cache entry for {portfolio_url}")
                    return True
                return False

        except Exception as e:
            logger.error(f"Cache deletion error: {str(e)}")
            return False

    async def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries and shareable links

        Returns:
            Number of entries deleted
        """
        try:
            deleted_count = 0
            async with self.async_session() as session:
                # Delete expired cache
                cache_cutoff = datetime.utcnow() - timedelta(days=settings.cache_ttl_days)
                cache_stmt = delete(GradingCache).where(
                    GradingCache.created_at < cache_cutoff
                )
                cache_result = await session.execute(cache_stmt)
                deleted_count += cache_result.rowcount

                # Delete expired shareable links
                share_stmt = delete(ShareableLink).where(
                    ShareableLink.expires_at.isnot(None),
                    ShareableLink.expires_at < datetime.utcnow()
                )
                share_result = await session.execute(share_stmt)
                deleted_count += share_result.rowcount

                await session.commit()
                logger.info(f"Cleaned up {deleted_count} expired entries")
                return deleted_count

        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
            return 0

    async def clear_all_cache(self) -> int:
        """
        Clear ALL cache entries (not shareable links)

        Returns:
            Number of entries deleted
        """
        try:
            async with self.async_session() as session:
                # Delete all cache entries
                stmt = delete(GradingCache)
                result = await session.execute(stmt)
                await session.commit()

                deleted_count = result.rowcount
                logger.info(f"Cleared all cache - deleted {deleted_count} entries")
                return deleted_count

        except Exception as e:
            logger.error(f"Clear all cache error: {str(e)}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            async with self.async_session() as session:
                # Count cache entries
                cache_stmt = select(GradingCache)
                cache_result = await session.execute(cache_stmt)
                cache_entries = cache_result.scalars().all()

                # Count shareable links
                share_stmt = select(ShareableLink)
                share_result = await session.execute(share_stmt)
                share_entries = share_result.scalars().all()

                total_accesses = sum(entry.access_count for entry in cache_entries)

                return {
                    "cache_entries": len(cache_entries),
                    "shareable_links": len(share_entries),
                    "total_cache_hits": total_accesses,
                    "cache_enabled": settings.enable_caching,
                    "cache_ttl_days": settings.cache_ttl_days
                }

        except Exception as e:
            logger.error(f"Stats retrieval error: {str(e)}")
            return {}

    def _generate_share_id(self, portfolio_url: str) -> str:
        """
        Generate a short, URL-safe share ID
        Uses hash of URL + timestamp for uniqueness
        """
        hash_input = f"{portfolio_url}{datetime.utcnow().isoformat()}"
        hash_obj = hashlib.sha256(hash_input.encode())
        # Take first 12 characters of hex digest
        return hash_obj.hexdigest()[:12]


# Global cache instance
cache_service = CacheService()
