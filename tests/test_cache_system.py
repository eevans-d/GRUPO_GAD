"""
Cache System Tests

Tests for cache decorators and invalidation patterns.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.core.cache_decorators import (
    _generate_cache_key,
    cache_result,
    invalidate_cache,
    cache_and_invalidate
)


class TestCacheKeyGeneration:
    """Test cache key generation from function arguments."""
    
    def test_simple_args(self):
        """Test key generation with simple string/int args."""
        key = _generate_cache_key("list_users", (1, "admin"), {})
        
        assert "list_users" in key
        assert len(key) == len("list_users:") + 32  # func_name + md5 hash
    
    def test_kwargs_only(self):
        """Test key generation with only kwargs."""
        key = _generate_cache_key("get_user", (), {"skip": 10, "limit": 100})
        
        assert "get_user" in key
        assert len(key) > len("get_user:")
    
    def test_excluded_keys(self):
        """Test that technical keys are excluded."""
        key1 = _generate_cache_key("endpoint", (), {"telegram_id": 123})
        key2 = _generate_cache_key("endpoint", (), {"telegram_id": 123, "db": "session", "_internal": "yes"})
        
        # Both should be the same since db and _internal are excluded
        assert key1 == key2
    
    def test_consistent_keys(self):
        """Test that same args generate same key."""
        key1 = _generate_cache_key("func", (1, 2, 3), {"a": "b"})
        key2 = _generate_cache_key("func", (1, 2, 3), {"a": "b"})
        
        assert key1 == key2
    
    def test_different_args_different_keys(self):
        """Test that different args generate different keys."""
        key1 = _generate_cache_key("func", (1,), {})
        key2 = _generate_cache_key("func", (2,), {})
        
        assert key1 != key2


class TestCacheResultDecorator:
    """Test @cache_result decorator."""
    
    @pytest.mark.asyncio
    async def test_caches_result(self):
        """Test that decorator caches function result."""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None  # Cache miss
        
        call_count = 0
        
        @cache_result(ttl_seconds=300)
        async def get_data():
            nonlocal call_count
            call_count += 1
            return {"data": "test"}
        
        with patch("src.core.cache_decorators._cache_service", mock_cache):
            # First call
            result1 = await get_data()
            assert result1 == {"data": "test"}
            assert call_count == 1
            
            # Verify cache.set was called
            mock_cache.set.assert_called_once()
            call_args = mock_cache.set.call_args
            assert call_args.kwargs["ttl"] == 300
    
    @pytest.mark.asyncio
    async def test_returns_cached_result(self):
        """Test that cached result is returned."""
        cached_data = {"data": "cached"}
        mock_cache = AsyncMock()
        mock_cache.get.return_value = cached_data
        
        call_count = 0
        
        @cache_result(ttl_seconds=300)
        async def get_data():
            nonlocal call_count
            call_count += 1
            return {"data": "fresh"}
        
        with patch("src.core.cache_decorators._cache_service", mock_cache):
            # Call function
            result = await get_data()
            
            # Should return cached data, not fresh
            assert result == cached_data
            assert call_count == 0  # Function not called
    
    @pytest.mark.asyncio
    async def test_no_cache_service(self):
        """Test that decorator works without cache service."""
        
        @cache_result(ttl_seconds=300)
        async def get_data():
            return {"data": "test"}
        
        with patch("src.core.cache_decorators._cache_service", None):
            result = await get_data()
            assert result == {"data": "test"}


class TestCacheInvalidationDecorator:
    """Test @invalidate_cache decorator."""
    
    @pytest.mark.asyncio
    async def test_invalidates_pattern(self):
        """Test that cache pattern is invalidated after function."""
        mock_cache = AsyncMock()
        mock_cache.delete_pattern.return_value = 3  # 3 keys deleted
        
        @invalidate_cache("users:*")
        async def create_user():
            return {"id": 1, "name": "test"}
        
        with patch("src.core.cache_decorators._cache_service", mock_cache):
            result = await create_user()
            
            assert result == {"id": 1, "name": "test"}
            mock_cache.delete_pattern.assert_called_once_with("users:*")


class TestCacheAndInvalidateDecorator:
    """Test @cache_and_invalidate decorator."""
    
    @pytest.mark.asyncio
    async def test_invalidates_multiple_patterns(self):
        """Test that multiple patterns are invalidated."""
        mock_cache = AsyncMock()
        mock_cache.delete_pattern.return_value = 2
        
        @cache_and_invalidate(
            invalidate_patterns=["users:*", "stats:*"]
        )
        async def update_user():
            return {"id": 1}
        
        with patch("src.core.cache_decorators._cache_service", mock_cache):
            result = await update_user()
            
            assert result == {"id": 1}
            assert mock_cache.delete_pattern.call_count == 2


class TestCacheIntegration:
    """Integration tests with realistic scenarios."""
    
    @pytest.mark.asyncio
    async def test_list_then_create_then_list(self):
        """Test cache invalidation on create."""
        mock_cache = AsyncMock()
        list_data = [{"id": 1, "name": "alice"}]
        
        # First list: cache miss
        mock_cache.get.return_value = None
        
        @cache_result(ttl_seconds=300, key_prefix="users")
        async def list_users():
            return list_data
        
        # Create user: should invalidate
        @cache_and_invalidate(invalidate_patterns=["users:*"])
        async def create_user():
            return {"id": 2, "name": "bob"}
        
        with patch("src.core.cache_decorators._cache_service", mock_cache):
            # List users (miss, cache it)
            result1 = await list_users()
            assert result1 == list_data
            assert mock_cache.set.called
            
            # Create user (should invalidate cache)
            mock_cache.reset_mock()
            mock_cache.delete_pattern.return_value = 1
            result2 = await create_user()
            assert result2 == {"id": 2, "name": "bob"}
            mock_cache.delete_pattern.assert_called_once_with("users:*")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
