# Domains (도메인 레이어)

`src/domains/` 폴더는 비즈니스 로직을 도메인별로 그룹화한 모듈들을 포함합니다.

---

## ✨ 도메인 주도 설계 (Domain-Driven Design)

본 프로젝트는 **도메인 주도 설계(DDD)**의 개념을 도입하여 유지보수성과 확장성을 극대화합니다. 각 도메인은 독립적인 비즈니스 기능을 담당하며, 계층형 아키텍처를 따릅니다.

---

## 📂 도메인 구조

```
src/domains/
├── auth/                   # 인증 도메인
│   ├── controller.py       # API 엔드포인트 (라우터)
│   ├── schema/             # Pydantic 스키마
│   │   ├── request.py      # 요청 스키마
│   │   └── response.py     # 응답 스키마
│   └── service/            # 비즈니스 로직
│       ├── kakao_service.py
│       └── session_service.py
│
├── users/                  # 사용자 도메인
│   ├── models.py           # User 엔티티 모델
│   ├── schema.py           # User Pydantic 스키마
│   ├── repository.py       # User 데이터 접근 계층
│   └── service.py          # User 비즈니스 로직
│
├── documents/              # 문서 관리 도메인 (상세 가이드: documents/README.md)
│   ├── models.py
│   ├── schema.py
│   ├── repository.py
│   ├── service.py
│   └── controller.py
│
└── tags/                   # 태그 시스템 도메인 (상세 가이드: tags/README.md)
    ├── models.py
    ├── schema.py
    ├── repository.py
    └── service.py
```

---

## 🏗️ 계층형 아키텍처

각 도메인은 다음 계층으로 구성됩니다:

### 1. Controller Layer (API 엔드포인트)
**파일**: `controller.py` 또는 `router.py`

**역할**:
- HTTP 요청/응답 처리
- 인증 및 권한 검증
- 입력 유효성 검사 (Pydantic 스키마)
- Service Layer 호출

**예시**:
```python
@router.post("/upload")
async def upload_document(
    file: UploadFile,
    user_id: int = Depends(get_current_user_id),
    document_service: DocumentService = Depends()
):
    document, tags, method = await document_service.upload_document(
        user_id=user_id,
        file=file
    )
    return DocumentUploadResponse(...)
```

### 2. Schema Layer (DTO)
**파일**: `schema.py` 또는 `schema/request.py`, `schema/response.py`

**역할**:
- API 요청/응답 데이터 구조 정의
- Pydantic 모델을 사용한 자동 검증
- 타입 안정성 보장

**예시**:
```python
class DocumentUploadResponse(BaseModel):
    document_id: int
    original_filename: str
    file_size_kb: int
    tags: List[TagSchema]
    extraction_method: str
```

### 3. Service Layer (비즈니스 로직)
**파일**: `service.py`

**역할**:
- 핵심 비즈니스 로직 구현
- 여러 Repository 조합
- 외부 시스템 연동 (MinIO, Elasticsearch 등)
- 트랜잭션 관리

**예시**:
```python
class DocumentService:
    async def upload_document(self, user_id: int, file: UploadFile):
        # 1. 파일 검증
        # 2. MinIO 업로드
        # 3. PostgreSQL 메타데이터 저장
        # 4. Elasticsearch 색인
        # 5. AI 키워드 추출
        # 6. 태그 연결
        return document, tags, extraction_method
```

### 4. Repository Layer (데이터 접근)
**파일**: `repository.py`

**역할**:
- 데이터베이스 CRUD 연산
- SQLAlchemy ORM 쿼리
- N+1 문제 방지 (Eager Loading)
- 데이터 접근 추상화

**예시**:
```python
class DocumentRepository:
    async def create(self, user_id, filename, storage_path, file_type, file_size_kb):
        document = Document(
            user_id=user_id,
            original_filename=filename,
            storage_path=storage_path,
            file_type=file_type,
            file_size_kb=file_size_kb
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document
```

### 5. Model Layer (도메인 엔티티)
**파일**: `models.py`

**역할**:
- SQLAlchemy ORM 모델 정의
- 데이터베이스 테이블 구조
- 관계(Relationship) 정의

**예시**:
```python
class Document(Base):
    __tablename__ = "documents"

    document_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False, unique=True)
    file_type = Column(String(100), nullable=False)
    file_size_kb = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 관계
    user = relationship("User", back_populates="documents")
    document_tags = relationship("DocumentTag", back_populates="document", cascade="all, delete-orphan")
```

---

## 🔗 도메인 간 의존성

도메인 간 의존성은 Service Layer에서만 발생하며, 단방향 의존성을 유지합니다.

```
┌─────────────┐
│  Documents  │
│   Service   │
└──────┬──────┘
       │ depends on
       ▼
┌─────────────┐
│    Tags     │
│   Service   │
└─────────────┘
```

**예시**:
```python
class DocumentService:
    def __init__(self, repository, db):
        self.repository = repository
        self.db = db
        self.tag_service = TagService(db)  # 태그 서비스 의존성
```

---

## 📋 SOLID 원칙 준수

### 1. Single Responsibility Principle (단일 책임 원칙)
- 각 계층은 하나의 책임만 가짐
- Controller: HTTP 처리, Service: 비즈니스 로직, Repository: 데이터 접근

### 2. Open/Closed Principle (개방-폐쇄 원칙)
- 새로운 기능 추가 시 기존 코드 수정 최소화
- 예: 새로운 파일 형식 추가 시 `TextExtractor`에 메서드만 추가

### 3. Liskov Substitution Principle (리스코프 치환 원칙)
- 인터페이스 기반 설계 (예: `KeywordExtractor` 추상 클래스)

### 4. Interface Segregation Principle (인터페이스 분리 원칙)
- 각 Repository는 필요한 기능만 노출

### 5. Dependency Inversion Principle (의존성 역전 원칙)
- Service는 Repository 인터페이스에 의존 (구현체 아님)
- FastAPI Depends를 사용한 의존성 주입

---

## 🚀 새로운 도메인 추가하기

### 1단계: 폴더 및 파일 생성

```bash
src/domains/
└── my_domain/
    ├── __init__.py
    ├── models.py           # SQLAlchemy 모델
    ├── schema.py           # Pydantic 스키마
    ├── repository.py       # 데이터 접근
    ├── service.py          # 비즈니스 로직
    └── controller.py       # API 엔드포인트
```

### 2단계: 모델 정의 (`models.py`)

```python
from sqlalchemy import Column, BigInteger, String
from src.db.session import Base

class MyEntity(Base):
    __tablename__ = "my_entities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
```

### 3단계: 스키마 정의 (`schema.py`)

```python
from pydantic import BaseModel

class MyEntityResponse(BaseModel):
    id: int
    name: str
```

### 4단계: Repository 구현 (`repository.py`)

```python
class MyEntityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str):
        entity = MyEntity(name=name)
        self.db.add(entity)
        await self.db.commit()
        return entity
```

### 5단계: Service 구현 (`service.py`)

```python
class MyEntityService:
    def __init__(self, repository: MyEntityRepository, db: AsyncSession):
        self.repository = repository
        self.db = db

    async def create_entity(self, name: str):
        return await self.repository.create(name)
```

### 6단계: Controller 구현 (`controller.py`)

```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/")
async def create_entity(
    name: str,
    service: MyEntityService = Depends()
):
    entity = await service.create_entity(name)
    return MyEntityResponse(id=entity.id, name=entity.name)
```

### 7단계: 라우터 등록 (`src/main.py`)

```python
from src.domains.my_domain.controller import router as my_domain_router

app.include_router(my_domain_router, prefix="/api/v1/my-domain", tags=["MyDomain"])
```

---

## 📚 하위 도메인 가이드

각 도메인에 대한 상세 가이드:

- **Documents 도메인**: [`documents/README.md`](./documents/README.md) - 문서 업로드, AI 태깅, 텍스트 추출 워크플로우
- **Tags 도메인**: [`tags/README.md`](./tags/README.md) - 태그 시스템, N+1 방지, Get-or-Create 패턴

---

## 🧪 테스트 전략

각 계층별 테스트 가이드:

### 1. Unit Tests (단위 테스트)
- **대상**: Service, Repository
- **위치**: `tests/unit/domains/{domain_name}/`
- **Mock 사용**: 외부 의존성(DB, Elasticsearch, MinIO) Mock 처리

```python
@pytest.mark.asyncio
async def test_document_upload():
    mock_repository = AsyncMock()
    mock_minio = MagicMock()

    service = DocumentService(mock_repository, db=MagicMock())

    with patch('src.domains.documents.service.minio_client', mock_minio):
        document, tags, method = await service.upload_document(...)

    assert document.document_id == 1
    assert mock_minio.upload_file.called
```

### 2. Integration Tests (통합 테스트)
- **대상**: Controller, End-to-End 워크플로우
- **위치**: `tests/integration/domains/{domain_name}/`
- **실제 DB 사용**: TestContainer 또는 Test DB 사용

---

## 🛡️ 보안 및 권한

### 인증
- 모든 API는 `get_current_user_id` 의존성을 통해 인증 검증
- Redis 기반 세션 관리

### 권한 검증
- 사용자는 자신이 생성한 리소스만 접근 가능
- Repository/Service 레벨에서 `user_id` 필터링

**예시**:
```python
async def get_document_by_id(self, document_id: int, user_id: int):
    stmt = select(Document).where(
        Document.document_id == document_id,
        Document.user_id == user_id  # 권한 검증
    )
    result = await self.db.execute(stmt)
    return result.scalar_one_or_none()
```

---

## 📖 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 문서](https://docs.sqlalchemy.org/en/20/)
- [Domain-Driven Design (Eric Evans)](https://www.domainlanguage.com/ddd/)
