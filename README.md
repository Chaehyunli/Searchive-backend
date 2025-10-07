# Searchive Backend

Searchive 프로젝트의 핵심 두뇌 역할을 하는 Python/FastAPI 기반 API 서버입니다. 사용자 인증, 문서 관리, 검색, 그리고 지능형 RAG 파이프라인을 총괄합니다.

---

## ✨ 아키텍처: 도메인 주도 계층형 아키텍처

본 프로젝트는 유지보수성과 확장성을 극대화하기 위해 **도메인 주도 설계(Domain-Driven Design)**의 개념을 도입한 계층형 아키텍처를 따릅니다. 모든 소스 코드는 `src/domains` 폴더 아래에 각 기능(도메인)별로 그룹화됩니다.

### 각 계층의 역할

-   **`router.py` (Controller/API Layer)**: HTTP 요청을 받아 유효성을 검사하고, 적절한 서비스로 요청을 전달하는 API 엔드포인트 계층입니다.
-   **`schemas.py` (DTO Layer)**: Pydantic 모델을 사용하여 API 요청 및 응답의 데이터 구조를 정의하고 유효성을 검사합니다.
-   **`services.py` (Service/Business Logic Layer)**: 실제 비즈니스 로직을 수행합니다. 여러 리포지토리를 조합하여 복잡한 작업을 처리합니다.
-   **`repositories.py` (Data Access Layer)**: 데이터베이스와의 상호작용을 담당하며, CRUD 연산을 추상화합니다.
-   **`models.py` (Domain/Entity Layer)**: SQLAlchemy ORM 모델로, 데이터베이스 테이블 구조를 정의합니다.

---

## 📂 폴더 구조

```
Searchive-backend/
├── .env                    # 실제 환경 변수 파일 (Git 무시)
├── .env_example            # 환경 변수 예시 파일
├── .gitignore              # Git 무시 목록
├── alembic/                # Alembic 마이그레이션 스크립트 저장 폴더
│   ├── versions/           # 마이그레이션 버전 파일들
│   ├── env.py              # Alembic 환경 설정
│   ├── script.py.mako      # 마이그레이션 템플릿
│   └── README
├── alembic.ini             # Alembic 설정 파일
├── requirements.txt        # Python 의존성 목록
├── pytest.ini              # Pytest 설정 파일
├── README.md               # 프로젝트 설명 파일
├── tests/                  # 테스트 코드
│   ├── __init__.py
│   ├── conftest.py         # Pytest 설정 및 픽스처
│   ├── README.md           # 테스트 가이드
│   ├── unit/               # 단위 테스트
│   │   ├── __init__.py
│   │   └── domains/
│   │       └── __init__.py
│   └── integration/        # 통합 테스트
│       ├── __init__.py
│       ├── domains/
│       │   └── __init__.py
│       ├── test_db_connection.py
│       └── test_redis_connection.py
└── src/                    # 소스 코드 루트
    ├── __init__.py
    ├── main.py             # FastAPI 앱 생성 및 라우터 포함
    ├── core/               # 프로젝트 핵심 설정
    │   ├── __init__.py
    │   ├── config.py       # .env 파일을 읽어오는 환경 변수 관리
    │   ├── exception.py    # 예외 처리 핸들러
    │   ├── redis.py        # Redis 연결 및 세션 관리
    │   └── security.py     # 보안 관련 유틸리티 (JWT 등)
    ├── db/                 # 데이터베이스 연결 및 세션 관리
    │   ├── __init__.py
    │   └── session.py
    └── domains/            # ✨ 핵심: 도메인별 모듈
        ├── __init__.py
        ├── auth/           # 인증 도메인
        │   ├── __init__.py
        │   ├── controller.py   # API 엔드포인트 (라우터)
        │   ├── schema/         # Pydantic 스키마
        │   │   ├── __init__.py
        │   │   ├── request.py  # 요청 스키마
        │   │   └── response.py # 응답 스키마
        │   └── service/        # 비즈니스 로직
        │       ├── __init__.py
        │       ├── kakao_service.py    # 카카오 OAuth 서비스
        │       └── session_service.py  # 세션 관리 서비스
        ├── users/          # 사용자 도메인
        │   ├── __init__.py
        │   └── models.py       # User 엔티티 모델
        ├── documents/      # 문서 관리 도메인
        │   ├── __init__.py
        │   └── models.py       # Document 엔티티 모델
        └── tags/           # 태그 도메인
            ├── __init__.py
            └── models.py       # Tag 엔티티 모델
```

---

## 🛠️ 기술 스택

-   **Framework**: FastAPI
-   **Database**: PostgreSQL (SQLAlchemy ORM, Alembic)
-   **Cache**: Redis
-   **Search**: Elasticsearch
-   **Data Validation**: Pydantic
-   **AI Frameworks**: LangChain, LangGraph
-   **Async Runtime**: Uvicorn

---

## 🏁 시작하기 (Getting Started)

### 1. 레포지토리 클론 및 가상 환경 설정

```bash
git clone https://github.com/Chaehyunli/Searchive-backend.git 
cd Searchive-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env_example` 파일을 복사하여 `.env` 파일을 생성하고, `Searchive-db` 스택의 접속 정보를 입력합니다.

```bash
cp .env_example .env
```

그 후 `.env` 파일을 열어 데이터베이스 정보 및 API 키를 설정합니다.

### 4. DB 인프라 실행

`Searchive-db` 레포지토리에서 `docker compose up -d`를 실행하여 모든 데이터베이스를 준비시킵니다.

### 5. 데이터베이스 마이그레이션

백엔드 서버를 실행하기 전에, 아래 명령어로 데이터베이스 스키마를 생성합니다.

```bash
# Alembic 초기화 (최초 1회만)
alembic init alembic

# 마이그레이션 파일 생성
alembic revision --autogenerate -m "Initial migration"

# 마이그레이션 실행
alembic upgrade head
```

### 6. 서버 실행

```bash
# 개발 모드 (자동 리로드)
.\venv\Scripts\activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 또는
# python src/main.py
```

서버가 실행되면 다음 URL에서 확인할 수 있습니다:

-   API 서버: http://localhost:8000
-   API 문서 (Swagger): http://localhost:8000/docs
-   API 문서 (ReDoc): http://localhost:8000/redoc

---

## 📖 개발 가이드

### 새로운 도메인 추가하기

1. `src/domains/` 아래에 새 폴더 생성 (예: `users`)
2. 다음 파일들을 생성:
   - `models.py`: SQLAlchemy 모델 정의
   - `schemas.py`: Pydantic 스키마 정의
   - `repositories.py`: 데이터 액세스 로직
   - `services.py`: 비즈니스 로직
   - `router.py`: API 엔드포인트
3. `src/main.py`에 라우터 등록

```python
from src.domains.users.router import router as users_router
app.include_router(users_router, prefix="/api/users", tags=["Users"])
```

### 코드 스타일

프로젝트는 다음 도구들을 사용하여 코드 품질을 유지합니다:

```bash
# 코드 포맷팅
black .

# 린팅
flake8 .

# 타입 체크
mypy src/
```

### 테스트

```bash
# 전체 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_auth.py

# 커버리지 포함
pytest --cov=src tests/
```

---

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 있습니다.

---

## 👥 기여

기여를 환영합니다! Pull Request를 보내주세요.

---

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 등록해주세요.
