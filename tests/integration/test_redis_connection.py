# -*- coding: utf-8 -*-
"""Redis 연결 및 기본 동작 테스트"""
import pytest
import time

from src.core.config import settings


class TestRedisConnection:
    """Redis 연결 및 기본 동작 테스트"""

    def test_redis_connection(self, redis_client):
        """Redis 연결 테스트"""
        assert redis_client.ping() is True

    def test_redis_config(self):
        """Redis 설정이 올바르게 로드되었는지 테스트"""
        assert settings.REDIS_HOST is not None
        assert settings.REDIS_PORT is not None
        assert settings.REDIS_URL is not None

    def test_redis_url_format(self):
        """REDIS_URL 형식이 올바른지 테스트"""
        expected_prefix = f"redis://"
        assert settings.REDIS_URL.startswith(expected_prefix)
        assert str(settings.REDIS_PORT) in settings.REDIS_URL

    def test_redis_info(self, redis_client):
        """Redis 서버 정보 조회 테스트"""
        info = redis_client.info()
        assert 'redis_version' in info
        assert 'os' in info

    def test_redis_database_selection(self, redis_client):
        """올바른 테스트 데이터베이스를 사용하는지 테스트"""
        # 픽스처는 테스트를 위해 db=1을 사용
        redis_client.set('test_db', '1')
        result = redis_client.get('test_db')
        assert result == '1'


class TestRedisOperations:
    """Redis 기본 CRUD 연산 테스트"""

    def test_set_and_get(self, clean_redis):
        """기본 SET과 GET 연산 테스트"""
        clean_redis.set('test_key', 'test_value')
        result = clean_redis.get('test_key')
        assert result == 'test_value'

    def test_delete_operation(self, clean_redis):
        """DELETE 연산 테스트"""
        clean_redis.set('to_delete', 'value')
        assert clean_redis.exists('to_delete') == 1

        clean_redis.delete('to_delete')
        assert clean_redis.exists('to_delete') == 0

    def test_expiration(self, clean_redis):
        """키 만료 테스트"""
        clean_redis.setex('expiring_key', 1, 'value')
        assert clean_redis.get('expiring_key') == 'value'

        time.sleep(1.1)
        assert clean_redis.get('expiring_key') is None

    def test_increment_operation(self, clean_redis):
        """증가(INCREMENT) 연산 테스트"""
        clean_redis.set('counter', 0)
        clean_redis.incr('counter')
        clean_redis.incr('counter')

        result = clean_redis.get('counter')
        assert int(result) == 2

    def test_list_operations(self, clean_redis):
        """리스트 PUSH와 POP 연산 테스트"""
        clean_redis.lpush('test_list', 'item1', 'item2', 'item3')

        assert clean_redis.llen('test_list') == 3
        assert clean_redis.lpop('test_list') == 'item3'
        assert clean_redis.llen('test_list') == 2

    def test_hash_operations(self, clean_redis):
        """해시(Hash) 자료구조 연산 테스트 (실제 세션 구조와 무관한 기능 테스트)"""
        # 구버전 Redis 호환성을 위해 개별 hset 사용
        clean_redis.hset('test_hash:1', 'name', 'John Doe')
        clean_redis.hset('test_hash:1', 'email', 'john@example.com')
        clean_redis.hset('test_hash:1', 'age', '30')

        assert clean_redis.hget('test_hash:1', 'name') == 'John Doe'
        assert clean_redis.hget('test_hash:1', 'email') == 'john@example.com'

        all_data = clean_redis.hgetall('test_hash:1')
        assert len(all_data) == 3

    def test_set_operations(self, clean_redis):
        """집합(Set) 연산 테스트"""
        clean_redis.sadd('tags', 'python', 'redis', 'testing')

        assert clean_redis.scard('tags') == 3
        assert clean_redis.sismember('tags', 'python') == 1
        assert clean_redis.sismember('tags', 'java') == 0

    def test_multiple_keys(self, clean_redis):
        """다중 키 연산 테스트"""
        clean_redis.mset({
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3'
        })

        values = clean_redis.mget('key1', 'key2', 'key3')
        assert values == ['value1', 'value2', 'value3']


class TestRedisCaching:
    """Redis 캐싱 패턴 테스트"""

    def test_cache_hit(self, clean_redis):
        """캐시 히트 시나리오 테스트"""
        cache_key = 'cache:user:123'
        cache_value = '{"id": 123, "name": "John"}'

        # 캐시 미스 시뮬레이션
        assert clean_redis.get(cache_key) is None

        # 캐시 설정
        clean_redis.setex(cache_key, 300, cache_value)

        # 캐시 히트 시뮬레이션
        result = clean_redis.get(cache_key)
        assert result == cache_value

    def test_cache_invalidation(self, clean_redis):
        """캐시 무효화 테스트"""
        cache_key = 'cache:product:456'
        clean_redis.set(cache_key, 'old_data')

        # 캐시 무효화
        clean_redis.delete(cache_key)

        assert clean_redis.get(cache_key) is None

    def test_cache_ttl(self, clean_redis):
        """캐시 TTL(Time-To-Live) 테스트"""
        cache_key = 'cache:session:789'
        clean_redis.setex(cache_key, 2, 'session_data')

        ttl = clean_redis.ttl(cache_key)
        assert 0 < ttl <= 2

    def test_pattern_matching(self, clean_redis):
        """키 패턴 매칭 테스트"""
        clean_redis.set('user:1', 'data1')
        clean_redis.set('user:2', 'data2')
        clean_redis.set('product:1', 'data3')

        user_keys = list(clean_redis.scan_iter(match='user:*'))
        assert len(user_keys) == 2


class TestRedisPerformance:
    """Redis 성능 특성 테스트"""

    def test_bulk_operations(self, clean_redis):
        """대량 쓰기 성능 테스트"""
        pipe = clean_redis.pipeline()

        for i in range(100):
            pipe.set(f'bulk:key:{i}', f'value_{i}')

        pipe.execute()

        # 검증
        assert clean_redis.exists('bulk:key:0') == 1
        assert clean_redis.exists('bulk:key:99') == 1

    def test_pipeline_performance(self, clean_redis):
        """파이프라인 연산 테스트"""
        with clean_redis.pipeline() as pipe:
            for i in range(50):
                pipe.set(f'pipe:key:{i}', i)
                pipe.get(f'pipe:key:{i}')
            results = pipe.execute()

        # GET 연산 결과가 포함되어야 함
        assert len(results) == 100
