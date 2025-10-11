import pytest
import time

from src.core.config import settings


class TestRedisConnection:
    """Test Redis connectivity and basic operations."""

    def test_redis_connection(self, redis_client):
        """Test that we can connect to Redis."""
        assert redis_client.ping() is True

    def test_redis_config(self):
        """Test that Redis configuration is properly loaded."""
        assert settings.REDIS_HOST is not None
        assert settings.REDIS_PORT is not None
        assert settings.REDIS_URL is not None

    def test_redis_url_format(self):
        """Test that REDIS_URL is properly formatted."""
        expected_prefix = f"redis://"
        assert settings.REDIS_URL.startswith(expected_prefix)
        assert str(settings.REDIS_PORT) in settings.REDIS_URL

    def test_redis_info(self, redis_client):
        """Test that we can get Redis server info."""
        info = redis_client.info()
        assert 'redis_version' in info
        assert 'os' in info

    def test_redis_database_selection(self, redis_client):
        """Test that we're using the correct test database."""
        # The fixture uses db=1 for testing
        redis_client.set('test_db', '1')
        result = redis_client.get('test_db')
        assert result == '1'


class TestRedisOperations:
    """Test basic Redis CRUD operations."""

    def test_set_and_get(self, clean_redis):
        """Test basic set and get operations."""
        clean_redis.set('test_key', 'test_value')
        result = clean_redis.get('test_key')
        assert result == 'test_value'

    def test_delete_operation(self, clean_redis):
        """Test delete operations."""
        clean_redis.set('to_delete', 'value')
        assert clean_redis.exists('to_delete') == 1

        clean_redis.delete('to_delete')
        assert clean_redis.exists('to_delete') == 0

    def test_expiration(self, clean_redis):
        """Test key expiration."""
        clean_redis.setex('expiring_key', 1, 'value')
        assert clean_redis.get('expiring_key') == 'value'

        time.sleep(1.1)
        assert clean_redis.get('expiring_key') is None

    def test_increment_operation(self, clean_redis):
        """Test increment operations."""
        clean_redis.set('counter', 0)
        clean_redis.incr('counter')
        clean_redis.incr('counter')

        result = clean_redis.get('counter')
        assert int(result) == 2

    def test_list_operations(self, clean_redis):
        """Test list push and pop operations."""
        clean_redis.lpush('test_list', 'item1', 'item2', 'item3')

        assert clean_redis.llen('test_list') == 3
        assert clean_redis.lpop('test_list') == 'item3'
        assert clean_redis.llen('test_list') == 2

    def test_hash_operations(self, clean_redis):
        """Test hash operations."""
        clean_redis.hset('user:1', mapping={
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': '30'
        })

        assert clean_redis.hget('user:1', 'name') == 'John Doe'
        assert clean_redis.hget('user:1', 'email') == 'john@example.com'

        all_data = clean_redis.hgetall('user:1')
        assert len(all_data) == 3

    def test_set_operations(self, clean_redis):
        """Test set operations."""
        clean_redis.sadd('tags', 'python', 'redis', 'testing')

        assert clean_redis.scard('tags') == 3
        assert clean_redis.sismember('tags', 'python') == 1
        assert clean_redis.sismember('tags', 'java') == 0

    def test_multiple_keys(self, clean_redis):
        """Test operations with multiple keys."""
        clean_redis.mset({
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3'
        })

        values = clean_redis.mget('key1', 'key2', 'key3')
        assert values == ['value1', 'value2', 'value3']


class TestRedisCaching:
    """Test Redis caching patterns."""

    def test_cache_hit(self, clean_redis):
        """Test cache hit scenario."""
        cache_key = 'cache:user:123'
        cache_value = '{"id": 123, "name": "John"}'

        # Simulate cache miss
        assert clean_redis.get(cache_key) is None

        # Set cache
        clean_redis.setex(cache_key, 300, cache_value)

        # Simulate cache hit
        result = clean_redis.get(cache_key)
        assert result == cache_value

    def test_cache_invalidation(self, clean_redis):
        """Test cache invalidation."""
        cache_key = 'cache:product:456'
        clean_redis.set(cache_key, 'old_data')

        # Invalidate cache
        clean_redis.delete(cache_key)

        assert clean_redis.get(cache_key) is None

    def test_cache_ttl(self, clean_redis):
        """Test cache time-to-live."""
        cache_key = 'cache:session:789'
        clean_redis.setex(cache_key, 2, 'session_data')

        ttl = clean_redis.ttl(cache_key)
        assert 0 < ttl <= 2

    def test_pattern_matching(self, clean_redis):
        """Test key pattern matching."""
        clean_redis.set('user:1', 'data1')
        clean_redis.set('user:2', 'data2')
        clean_redis.set('product:1', 'data3')

        user_keys = list(clean_redis.scan_iter(match='user:*'))
        assert len(user_keys) == 2


class TestRedisPerformance:
    """Test Redis performance characteristics."""

    def test_bulk_operations(self, clean_redis):
        """Test bulk write performance."""
        pipe = clean_redis.pipeline()

        for i in range(100):
            pipe.set(f'bulk:key:{i}', f'value_{i}')

        pipe.execute()

        # Verify
        assert clean_redis.exists('bulk:key:0') == 1
        assert clean_redis.exists('bulk:key:99') == 1

    def test_pipeline_performance(self, clean_redis):
        """Test pipeline operations."""
        with clean_redis.pipeline() as pipe:
            for i in range(50):
                pipe.set(f'pipe:key:{i}', i)
                pipe.get(f'pipe:key:{i}')
            results = pipe.execute()

        # Every other result should be the get operation
        assert len(results) == 100
