# Searchive Backend Tests

테스트 코드 구조 및 가이드

## 📁 디렉토리 구조

```
tests/
├── conftest.py                 # 전역 fixtures (DB, Redis, FastAPI client 등)
├── pytest.ini                  # Pytest 설정
├── unit/                       # 단위 테스트 (빠르고 독립적)
│   ├── domains/               # 도메인별 단위 테스트
│   │   ├── users/            # 예: 사용자 도메인
│   │   │   ├── test_models.py
│   │   │   ├── test_schemas.py
│   │   │   └── test_services.py
│   │   ├── documents/        # 예: 문서 도메인
│   │   └── search/           # 예: 검색 도메인
│   └── core/                 # 코어 로직 테스트
├── integration/               # 통합 테스트 (DB, Redis 등 외부 의존성)
│   ├── test_db_connection.py
│   ├── test_redis_connection.py
│   └── domains/              # 도메인별 통합 테스트
│       ├── users/           # 예: 사용자 도메인
│       │   ├── test_repository.py
│       │   └── test_api.py
│       ├── documents/
│       └── search/
└── e2e/                      # E2E 테스트 (전체 플로우)
    ├── test_user_flow.py
    └── test_search_flow.py
```

## 🧪 테스트 실행

### 전체 테스트
```bash
pytest
```

### 마커별 실행
```bash
pytest -m unit              # 단위 테스트만
pytest -m integration       # 통합 테스트만
pytest -m e2e              # E2E 테스트만
pytest -m "not slow"       # 느린 테스트 제외
```

### 특정 도메인 테스트
```bash
pytest tests/unit/domains/users/
pytest tests/integration/domains/documents/
```

### 커버리지 리포트
```bash
pytest --cov=src --cov-report=html
# htmlcov/index.html 에서 확인
```

### 병렬 실행 (빠른 테스트)
```bash
pip install pytest-xdist
pytest -n auto
```

## 📝 테스트 작성 가이드

### 단위 테스트 (Unit Tests)
- **목적**: 개별 함수/메서드 로직 검증
- **특징**: 빠르고, 외부 의존성 없음 (Mock 사용)
- **예시**:

```python
# tests/unit/domains/users/test_services.py
import pytest
from unittest.mock import Mock
from src.domains.users.services import UserService

class TestUserService:
    def test_create_user_success(self):
        # Mock repository
        mock_repo = Mock()
        mock_repo.create.return_value = {"id": 1, "email": "test@test.com"}

        service = UserService(repository=mock_repo)
        result = service.create_user("test@test.com", "password123")

        assert result["id"] == 1
        assert result["email"] == "test@test.com"
```

### 통합 테스트 (Integration Tests)
- **목적**: 여러 컴포넌트 간 상호작용 검증
- **특징**: DB, Redis 등 실제 의존성 사용
- **예시**:

```python
# tests/integration/domains/users/test_repository.py
import pytest
from src.domains.users.repository import UserRepository
from src.domains.users.models import User

@pytest.mark.integration
class TestUserRepository:
    def test_create_and_fetch_user(self, db_session):
        repo = UserRepository(db_session)

        # Create
        user = repo.create(email="test@test.com", password_hash="hash")
        assert user.id is not None

        # Fetch
        fetched = repo.get_by_id(user.id)
        assert fetched.email == "test@test.com"
```

### E2E 테스트 (End-to-End Tests)
- **목적**: 사용자 시나리오 전체 플로우 검증
- **특징**: API 엔드포인트 호출, 전체 스택 사용
- **예시**:

```python
# tests/e2e/test_user_flow.py
import pytest

@pytest.mark.e2e
async def test_user_registration_and_login(async_client):
    # 1. 회원가입
    register_response = await async_client.post("/api/auth/register", json={
        "email": "newuser@test.com",
        "password": "password123"
    })
    assert register_response.status_code == 201

    # 2. 로그인
    login_response = await async_client.post("/api/auth/login", json={
        "email": "newuser@test.com",
        "password": "password123"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
```

## 🔧 사용 가능한 Fixtures

### conftest.py에서 제공하는 fixtures:
- `db_engine`: 데이터베이스 엔진
- `db_session`: 데이터베이스 세션 (트랜잭션 롤백)
- `redis_client`: Redis 클라이언트 (테스트용 DB 1)
- `clean_redis`: 테스트 전후 Redis 초기화
- `app`: FastAPI 앱 인스턴스
- `async_client`: 비동기 HTTP 클라이언트

## 📊 커버리지 목표
- **전체**: 80% 이상
- **단위 테스트**: 각 서비스/유틸리티 90% 이상
- **통합 테스트**: API 엔드포인트 100%

## 🏷️ 테스트 마커

```python
@pytest.mark.unit           # 단위 테스트
@pytest.mark.integration    # 통합 테스트
@pytest.mark.e2e           # E2E 테스트
@pytest.mark.slow          # 느린 테스트
@pytest.mark.skip_ci       # CI에서 스킵
```

## 📦 Factory 사용 예시

```python
# tests/factories/user_factory.py
import factory
from src.domains.users.models import User

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Faker('email')
    username = factory.Faker('user_name')
    is_active = True

# 테스트에서 사용
user = UserFactory.create(email="custom@test.com")
```
