# Tags 도메인 (태그 시스템)

Tags 도메인은 문서 분류와 검색을 위한 태그 관리 기능을 제공합니다. **다대다(Many-to-Many) 관계**를 지원하여 하나의 문서에 여러 태그를 연결할 수 있습니다.

---

## 📂 모듈 구조

```
src/domains/tags/
├── models.py           # Tag, DocumentTag 엔티티 모델
├── schema.py           # Tag Pydantic 스키마
├── repository.py       # Tag, DocumentTag 데이터 접근 계층
└── service.py          # Tag 비즈니스 로직
```

---

## 🗄️ 데이터베이스 모델

### 1. Tag 테이블 (`models.py`)

```sql
CREATE TABLE tags (
    tag_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tags_name ON tags(name);
```

**컬럼 설명**:
- `tag_id`: 태그 고유 ID (자동 증가)
- `name`: 태그 이름 (중복 불가, 인덱스)
- `created_at`: 태그 생성 일시

**특징**:
- `name` 컬럼에 **UNIQUE 제약** 및 **인덱스** 설정
- 중복 태그 방지 및 빠른 조회

### 2. DocumentTag 테이블 (연결 테이블)

```sql
CREATE TABLE document_tags (
    document_id BIGINT REFERENCES documents(document_id) ON DELETE CASCADE,
    tag_id BIGINT REFERENCES tags(tag_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (document_id, tag_id)
);
```

**컬럼 설명**:
- `document_id`: 문서 ID (외래 키)
- `tag_id`: 태그 ID (외래 키)
- `created_at`: 연결 생성 일시

**특징**:
- **복합 기본 키**: `(document_id, tag_id)` - 중복 연결 방지
- **CASCADE 삭제**: 문서 삭제 시 연결도 자동 삭제
- **다대다 관계**: 하나의 문서에 여러 태그, 하나의 태그에 여러 문서 연결 가능

**관계 매핑** (`models.py`):
```python
class Tag(Base):
    __tablename__ = "tags"

    tag_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())

    # 관계
    document_tags = relationship("DocumentTag", back_populates="tag", cascade="all, delete-orphan")


class DocumentTag(Base):
    __tablename__ = "document_tags"

    document_id = Column(BigInteger, ForeignKey("documents.document_id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(BigInteger, ForeignKey("tags.tag_id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())

    # 관계
    document = relationship("Document", back_populates="document_tags")
    tag = relationship("Tag", back_populates="document_tags")
```

---

## 🔄 태그 생성 및 연결 워크플로우

### AI 자동 태깅 프로세스

문서 업로드 시 AI가 자동으로 키워드를 추출하고 태그를 생성합니다.

```
[1] 문서 업로드 완료 (DocumentService)
    ↓
[2] 텍스트 추출 (TextExtractor)
    ↓
[3] Elasticsearch 색인
    ↓
[4] 키워드 추출 (Hybrid Strategy)
    ├─ 문서 < 10개: KeyBERT
    └─ 문서 >= 10개: Elasticsearch TF-IDF
    ↓ ["machine learning", "deep learning", "neural network"]
[5] 태그 생성 및 연결 (TagService)
    ├─ Get-or-Create 패턴 (중복 방지)
    │   ├─ "machine learning" → 기존 tag_id=1 반환
    │   ├─ "deep learning" → 신규 tag_id=2 생성
    │   └─ "neural network" → 신규 tag_id=3 생성
    └─ Bulk Insert (N+1 방지)
        └─ document_tags 테이블에 (document_id=101, tag_id=[1,2,3]) 일괄 삽입
```

---

## 💻 코드 구현 (계층별)

### Service Layer (`service.py`)

#### 1. 태그 생성 및 문서 연결 (`service.py:59-87`)

```python
class TagService:
    """태그 비즈니스 로직"""

    async def attach_tags_to_document(
        self,
        document_id: int,
        tag_names: List[str]
    ) -> List[Tag]:
        """
        태그 생성 및 문서 연결

        Args:
            document_id: 문서 ID
            tag_names: 태그 이름 리스트

        Returns:
            생성/조회된 태그 리스트
        """
        if not tag_names:
            return []

        # 1. 태그 조회 또는 생성 (Get-or-Create, Bulk)
        tags = await self.get_or_create_tags(tag_names)

        # 2. 문서-태그 연결 생성 (Bulk Insert)
        tag_ids = [tag.tag_id for tag in tags]
        await self.document_tag_repository.bulk_create(document_id, tag_ids)

        return tags
```

#### 2. Get-or-Create 패턴 (`service.py:31-57`)

```python
async def get_or_create_tags(self, tag_names: List[str]) -> List[Tag]:
    """
    여러 태그를 한 번에 조회 또는 생성 (N+1 방지)

    Args:
        tag_names: 태그 이름 리스트 (예: ["python", "fastapi", "redis"])

    Returns:
        조회/생성된 태그 리스트
    """
    if not tag_names:
        return []

    # 중복 제거 및 정규화 (소문자 변환)
    unique_names = list(set(name.strip().lower() for name in tag_names if name.strip()))

    if not unique_names:
        return []

    # Repository에서 Bulk Get-or-Create
    tags = await self.tag_repository.bulk_get_or_create(unique_names)

    return tags
```

### Repository Layer (`repository.py`)

#### 1. Bulk Get-or-Create (`repository.py:121-147`)

```python
class TagRepository:
    """태그 데이터 접근 계층"""

    async def bulk_get_or_create(self, names: List[str]) -> List[Tag]:
        """
        여러 태그를 한 번에 조회 또는 생성 (N+1 방지)

        예시:
            names = ["python", "fastapi", "redis"]

            1단계: 기존 태그 조회 (1 query)
            - "python" (tag_id=1), "fastapi" (tag_id=2) 조회

            2단계: 신규 태그 필터링
            - "redis"는 DB에 없음

            3단계: 신규 태그 생성 (1 query)
            - "redis" (tag_id=3) 생성

            4단계: 결과 반환
            - [Tag(id=1, name="python"), Tag(id=2, name="fastapi"), Tag(id=3, name="redis")]

        총 쿼리 수: 2번
        (N+1 문제 발생 시: 3+1 = 4번)
        """
        # 1. 기존 태그 조회 (한 번의 쿼리)
        existing_tags = await self.find_all_by_names(names)
        existing_tag_names = {tag.name for tag in existing_tags}

        # 2. 신규 태그 필터링
        new_tag_names = [name for name in names if name not in existing_tag_names]

        # 3. 신규 태그 생성 (Bulk Insert)
        new_tags = []
        if new_tag_names:
            new_tags = await self.bulk_create(new_tag_names)

        # 4. 기존 + 신규 반환
        return existing_tags + new_tags
```

#### 2. Bulk Insert 태그 생성 (`repository.py:97-119`)

```python
async def bulk_create(self, names: List[str]) -> List[Tag]:
    """
    여러 태그를 한 번에 생성 (Bulk Insert)

    Args:
        names: 생성할 태그 이름 리스트

    Returns:
        생성된 태그 리스트
    """
    tags = [Tag(name=name) for name in names]

    self.db.add_all(tags)
    await self.db.commit()

    # 생성된 태그들의 ID를 Refresh
    for tag in tags:
        await self.db.refresh(tag)

    return tags
```

#### 3. DocumentTag 연결 생성 (`repository.py:182-207`)

```python
class DocumentTagRepository:
    """문서-태그 연결 데이터 접근 계층"""

    async def bulk_create(self, document_id: int, tag_ids: List[int]) -> List[DocumentTag]:
        """
        문서-태그 연결 일괄 생성 (Bulk Insert)

        Args:
            document_id: 문서 ID
            tag_ids: 태그 ID 리스트

        Returns:
            생성된 DocumentTag 리스트

        예시:
            document_id = 101
            tag_ids = [1, 2, 3]

            결과:
            - DocumentTag(document_id=101, tag_id=1)
            - DocumentTag(document_id=101, tag_id=2)
            - DocumentTag(document_id=101, tag_id=3)

            쿼리 수: 1번 (Bulk Insert)
            (N+1 문제 발생 시: 3번)
        """
        document_tags = [
            DocumentTag(document_id=document_id, tag_id=tag_id)
            for tag_id in tag_ids
        ]

        self.db.add_all(document_tags)
        await self.db.commit()

        return document_tags
```

---

## 🚀 성능 최적화 전략

### 1. N+1 문제 방지

#### 문제 상황

**N+1 문제**는 관련 데이터를 조회할 때 추가 쿼리가 N번 발생하는 문제입니다.

**예시**: 태그 3개를 조회/생성할 때
```python
# ❌ N+1 문제 발생 (총 4번 쿼리)
for tag_name in ["python", "fastapi", "redis"]:
    tag = await tag_repository.get_or_create(tag_name)  # 각 태그마다 1번씩
```

#### 해결 방법

**Bulk Operations** 사용:
```python
# ✅ Bulk 처리 (총 2번 쿼리)
tags = await tag_repository.bulk_get_or_create(["python", "fastapi", "redis"])
```

**쿼리 최소화**:
1. 기존 태그 조회 (1 query)
2. 신규 태그 생성 (1 query)

### 2. Eager Loading (문서 조회 시)

#### 문제 상황

문서 목록 조회 시 각 문서의 태그를 가져오기 위해 추가 쿼리 발생:
```python
# ❌ N+1 문제 (10개 문서 → 11번 쿼리)
documents = await db.execute(select(Document).where(Document.user_id == user_id))
for document in documents:
    tags = document.document_tags  # 각 문서마다 추가 쿼리 발생
```

#### 해결 방법

**selectinload()** 사용 (`documents/repository.py:61-101`):
```python
# ✅ Eager Loading (총 2번 쿼리)
stmt = (
    select(Document)
    .where(Document.user_id == user_id)
    .options(
        selectinload(Document.document_tags).selectinload(DocumentTag.tag)
    )
)

documents = await db.execute(stmt)
```

**쿼리 최소화**:
1. 문서 조회 (1 query)
2. 모든 문서의 태그 조회 (1 query)

### 3. 인덱스 최적화

**인덱스 설정** (`models.py`):
```python
class Tag(Base):
    name = Column(String(100), unique=True, nullable=False, index=True)
```

**효과**:
- `name` 컬럼 조회 시 O(log N) 시간 복잡도
- `find_all_by_names()` 성능 향상

### 4. 중복 제거 및 정규화

**Service Layer에서 중복 제거** (`service.py:31-57`):
```python
# 입력: ["Python", "python", "PYTHON", "FastAPI", "fastapi"]
unique_names = list(set(name.strip().lower() for name in tag_names))
# 결과: ["python", "fastapi"]
```

**효과**:
- 불필요한 DB 쿼리 방지
- 데이터 일관성 유지

---

## 🏷️ Get-or-Create 패턴

### 개념

**Get-or-Create 패턴**은 데이터가 존재하면 조회하고, 없으면 생성하는 패턴입니다.

### 구현 방식

#### 1. 단일 태그 Get-or-Create

```python
async def get_or_create(self, name: str) -> Tag:
    """
    태그 조회 또는 생성

    1. name으로 태그 조회
    2. 존재하면 반환
    3. 없으면 생성 후 반환
    """
    # 조회
    existing_tag = await self.find_by_name(name)

    if existing_tag:
        return existing_tag

    # 생성
    new_tag = Tag(name=name)
    self.db.add(new_tag)
    await self.db.commit()
    await self.db.refresh(new_tag)

    return new_tag
```

#### 2. Bulk Get-or-Create (최적화)

```python
async def bulk_get_or_create(self, names: List[str]) -> List[Tag]:
    """
    여러 태그를 한 번에 조회 또는 생성

    - N+1 문제 방지
    - 트랜잭션 처리
    """
    # 1. 기존 태그 조회 (1 query)
    existing_tags = await self.find_all_by_names(names)
    existing_tag_names = {tag.name for tag in existing_tags}

    # 2. 신규 태그 필터링
    new_tag_names = [name for name in names if name not in existing_tag_names]

    # 3. 신규 태그 생성 (1 query, Bulk Insert)
    new_tags = []
    if new_tag_names:
        new_tags = await self.bulk_create(new_tag_names)

    # 4. 기존 + 신규 반환
    return existing_tags + new_tags
```

### 장점

1. **중복 방지**: 같은 이름의 태그가 여러 개 생성되지 않음
2. **데이터 일관성**: `name` 컬럼의 UNIQUE 제약과 함께 사용
3. **성능 향상**: Bulk 처리로 쿼리 수 최소화

---

## 🗑️ CASCADE 삭제

### 동작 방식

**문서 삭제 시**:
1. `documents` 테이블에서 문서 삭제
2. `document_tags` 테이블에서 관련 연결 자동 삭제 (CASCADE)
3. `tags` 테이블의 태그는 유지 (다른 문서에서 사용 가능)

**SQL 외래 키 설정**:
```sql
CREATE TABLE document_tags (
    document_id BIGINT REFERENCES documents(document_id) ON DELETE CASCADE,
    tag_id BIGINT REFERENCES tags(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, tag_id)
);
```

**SQLAlchemy 설정**:
```python
class Document(Base):
    document_tags = relationship(
        "DocumentTag",
        back_populates="document",
        cascade="all, delete-orphan"  # 문서 삭제 시 연결도 삭제
    )
```

### 예시

```
초기 상태:
- Document(id=101) → Tags: [machine learning, deep learning]
- Document(id=102) → Tags: [machine learning, data science]

문서 101 삭제 후:
- Document(id=101) → 삭제됨
- document_tags(document_id=101, tag_id=1) → 삭제됨 (CASCADE)
- document_tags(document_id=101, tag_id=2) → 삭제됨 (CASCADE)
- Tag(name="machine learning") → 유지 (문서 102에서 사용 중)
- Tag(name="deep learning") → 유지 (다른 문서에서 사용 가능)
```

---

## 📊 데이터 흐름 예시

### 시나리오: 문서 업로드 후 태그 생성

```
입력:
- document_id = 101
- 추출된 키워드 = ["machine learning", "deep learning", "neural network"]

데이터베이스 초기 상태:
- tags 테이블:
  - tag_id=1, name="machine learning" (기존)
  - tag_id=2, name="python" (기존)

Step 1: 기존 태그 조회
Query: SELECT * FROM tags WHERE name IN ('machine learning', 'deep learning', 'neural network')
결과: [Tag(id=1, name="machine learning")]

Step 2: 신규 태그 필터링
신규 태그: ["deep learning", "neural network"]

Step 3: 신규 태그 생성 (Bulk Insert)
Query: INSERT INTO tags (name) VALUES ('deep learning'), ('neural network')
결과:
- tag_id=3, name="deep learning"
- tag_id=4, name="neural network"

Step 4: 문서-태그 연결 생성 (Bulk Insert)
Query: INSERT INTO document_tags (document_id, tag_id) VALUES (101, 1), (101, 3), (101, 4)

최종 결과:
- Document(id=101) → Tags: [machine learning, deep learning, neural network]
- 총 쿼리 수: 3번
```

---

## 🧪 테스트

### 단위 테스트 (`tests/unit/domains/tags/`)

#### 1. Get-or-Create 테스트

```python
@pytest.mark.asyncio
async def test_get_or_create_tags_bulk():
    """여러 태그 일괄 조회/생성 테스트 (N+1 방지)"""
    # Mock Repository
    mock_tag_repository = AsyncMock()
    mock_tag1 = MagicMock()
    mock_tag1.tag_id = 1
    mock_tag1.name = "python"
    mock_tag2 = MagicMock()
    mock_tag2.tag_id = 2
    mock_tag2.name = "fastapi"
    mock_tags = [mock_tag1, mock_tag2]
    mock_tag_repository.bulk_get_or_create.return_value = mock_tags

    # TagService 생성
    tag_service = TagService(db=MagicMock())
    tag_service.tag_repository = mock_tag_repository

    # 테스트 실행
    tag_names = ["python", "fastapi", "redis"]
    tags = await tag_service.get_or_create_tags(tag_names)

    # 검증
    assert len(tags) == 2
    assert tags[0].name == "python"
    assert tags[1].name == "fastapi"
    assert mock_tag_repository.bulk_get_or_create.called
```

#### 2. 중복 제거 테스트

```python
@pytest.mark.asyncio
async def test_get_or_create_tags_with_duplicates():
    """중복 태그 이름으로 조회 시 중복 제거 테스트"""
    mock_tag_repository = AsyncMock()
    mock_tags = [MagicMock(), MagicMock()]
    mock_tag_repository.bulk_get_or_create.return_value = mock_tags

    tag_service = TagService(db=MagicMock())
    tag_service.tag_repository = mock_tag_repository

    # 중복 포함된 태그 이름 리스트
    tag_names = ["python", "Python", "PYTHON", "fastapi", "FastAPI"]
    tags = await tag_service.get_or_create_tags(tag_names)

    # 검증: 중복 제거되어 2개만 조회됨
    assert len(tags) == 2
```

#### 3. 문서 연결 테스트

```python
@pytest.mark.asyncio
async def test_attach_tags_to_document():
    """문서에 태그 연결 테스트"""
    # Mock Repository
    mock_tag_repository = AsyncMock()
    mock_tags = [MagicMock(), MagicMock(), MagicMock()]
    mock_tag_repository.bulk_get_or_create.return_value = mock_tags

    mock_document_tag_repository = AsyncMock()
    mock_document_tag_repository.bulk_create.return_value = [
        MagicMock(document_id=1, tag_id=1),
        MagicMock(document_id=1, tag_id=2),
        MagicMock(document_id=1, tag_id=3)
    ]

    # TagService 생성
    tag_service = TagService(db=MagicMock())
    tag_service.tag_repository = mock_tag_repository
    tag_service.document_tag_repository = mock_document_tag_repository

    # 테스트 실행
    tag_names = ["machine learning", "deep learning", "neural network"]
    tags = await tag_service.attach_tags_to_document(
        document_id=1,
        tag_names=tag_names
    )

    # 검증
    assert len(tags) == 3
    assert mock_tag_repository.bulk_get_or_create.called
    assert mock_document_tag_repository.bulk_create.called
```

---

## 📚 참고 자료

- [SQLAlchemy Many-to-Many Relationships](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#many-to-many)
- [Get-or-Create Pattern in Django](https://docs.djangoproject.com/en/4.2/ref/models/querysets/#get-or-create)
- [Solving N+1 Problem with SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#selectin-eager-loading)
- [Documents 도메인 가이드](../documents/README.md)
