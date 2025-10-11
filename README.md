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
    │   ├── security.py     # 보안 관련 유틸리티 (JWT 등)
    │   └── minio_client.py # MinIO 클라이언트 유틸리티
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
        │   ├── models.py       # User 엔티티 모델
        │   ├── schema.py       # User Pydantic 스키마
        │   ├── repository.py   # User 데이터 접근 계층
        │   └── service.py      # User 비즈니스 로직
        ├── documents/      # 문서 관리 도메인
        │   ├── __init__.py
        │   ├── models.py       # Document 엔티티 모델
        │   ├── schema.py       # Document Pydantic 스키마
        │   ├── repository.py   # Document 데이터 접근 계층
        │   ├── service.py      # Document 비즈니스 로직 (파일 검증, MinIO 업로드, AI 태깅)
        │   └── controller.py   # Document API 엔드포인트
        └── tags/           # 태그 도메인
            ├── __init__.py
            ├── models.py       # Tag, DocumentTag 엔티티 모델
            ├── schema.py       # Tag Pydantic 스키마
            ├── repository.py   # Tag 데이터 접근 계층
            └── service.py      # Tag 비즈니스 로직
```

---

## 🛠️ 기술 스택

-   **Framework**: FastAPI
-   **Database**: PostgreSQL (SQLAlchemy ORM, Alembic)
-   **Cache**: Redis
-   **Search**: Elasticsearch
-   **Object Storage**: MinIO
-   **Data Validation**: Pydantic
-   **AI Frameworks**:
    -   LangChain, LangGraph (RAG 파이프라인)
    -   KeyBERT (키워드 추출)
    -   Sentence Transformers (임베딩)
    -   OpenAI API (LLM)
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

**필수 환경 변수:**
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: PostgreSQL 설정
- `REDIS_HOST`, `REDIS_PORT`: Redis 설정
- `ELASTICSEARCH_HOST`, `ELASTICSEARCH_PORT`: Elasticsearch 설정
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`: MinIO 설정
- `OPENAI_API_KEY`: OpenAI API 키 (LLM 사용)
- `KEYWORD_EXTRACTION_COUNT`: 자동 태그 추출 개수 (기본값: 3)
- `KAKAO_CLIENT_ID`, `KAKAO_CLIENT_SECRET`: 카카오 OAuth 설정

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

## 📄 Documents API (문서 관리)

Documents 도메인은 사용자의 파일 업로드, 조회, 삭제 기능을 제공합니다.

### API 엔드포인트

#### 1. 문서 업로드 (POST /api/v1/documents/upload)
사용자가 문서를 MinIO에 업로드하고 메타데이터를 PostgreSQL에 저장합니다. **AI 기반 자동 태그 생성** 기능이 포함되어 있습니다.

**요청:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (파일)
- Headers: `Cookie: session_id` (인증 필요)

**허용된 파일 형식:**
- PDF (`.pdf`)
- 텍스트 (`.txt`)
- Excel (`.xlsx`, `.xls`)
- Word (`.doc`, `.docx`)
- PowerPoint (`.ppt`, `.pptx`)

**응답 (201 Created):**
```json
{
  "document_id": 101,
  "user_id": 1,
  "original_filename": "my_report.pdf",
  "storage_path": "1/a1b2c3d4-...-uuid.pdf",
  "file_type": "application/pdf",
  "file_size_kb": 1234,
  "uploaded_at": "2025-10-08T15:30:00Z",
  "updated_at": "2025-10-08T15:30:00Z",
  "tags": [
    {"tag_id": 1, "name": "machine learning"},
    {"tag_id": 2, "name": "deep learning"},
    {"tag_id": 3, "name": "neural network"}
  ],
  "extraction_method": "keybert"
}
```

**AI 자동 태깅:**
- 문서 업로드 시 AI가 텍스트를 분석하여 자동으로 키워드를 추출합니다
- 추출 방법: KeyBERT (기본) 또는 Elasticsearch TF-IDF (백업)
- 추출된 키워드는 `tags` 테이블에 저장되고, `document_tags` 연결 테이블을 통해 문서와 연결됩니다

#### 2. 문서 목록 조회 (GET /api/v1/documents)
현재 로그인된 사용자의 모든 문서 목록을 조회합니다. 각 문서에 연결된 태그 정보도 함께 반환됩니다.

**응답 (200 OK):**
```json
[
  {
    "document_id": 101,
    "original_filename": "report.pdf",
    "file_type": "application/pdf",
    "file_size_kb": 1234,
    "uploaded_at": "2025-10-08T15:30:00Z",
    "updated_at": "2025-10-08T15:30:00Z",
    "tags": [
      {"tag_id": 1, "name": "machine learning"},
      {"tag_id": 2, "name": "deep learning"}
    ]
  }
]
```

#### 3. 문서 상세 조회 (GET /api/v1/documents/{document_id})
특정 문서의 상세 정보를 조회합니다. (권한 검증 포함)

**응답 (200 OK):**
```json
{
  "document_id": 101,
  "user_id": 1,
  "original_filename": "my_report.pdf",
  "storage_path": "1/a1b2c3d4-...-uuid.pdf",
  "file_type": "application/pdf",
  "file_size_kb": 1234,
  "uploaded_at": "2025-10-08T15:30:00Z",
  "updated_at": "2025-10-08T15:30:00Z",
  "tags": [
    {"tag_id": 1, "name": "machine learning"},
    {"tag_id": 2, "name": "deep learning"}
  ]
}
```

#### 4. 문서 삭제 (DELETE /api/v1/documents/{document_id})
문서를 MinIO와 PostgreSQL에서 완전히 삭제합니다. (관련 태그도 CASCADE 삭제)

**응답 (200 OK):**
```json
{
  "message": "문서가 성공적으로 삭제되었습니다.",
  "document_id": 101
}
```

### 파일 저장 구조

**MinIO 버킷 구조:**
```
user-documents/
  ├── 1/                          # user_id=1의 폴더
  │   ├── a1b2c3d4-uuid.pdf
  │   ├── e5f6g7h8-uuid.docx
  │   └── i9j0k1l2-uuid.xlsx
  ├── 2/                          # user_id=2의 폴더
  │   ├── m3n4o5p6-uuid.pdf
  │   └── q7r8s9t0-uuid.txt
```

- 각 사용자는 `user_id` 폴더로 격리됩니다.
- 파일명은 **UUID(고유 랜덤값)**로 저장되어 충돌과 추측을 방지합니다.
- 원본 파일명은 PostgreSQL의 `original_filename` 컬럼에 저장됩니다.

### 보안 및 권한

- **인증 필수:** 모든 API는 `get_current_user_id` 의존성을 통해 로그인된 사용자만 접근 가능합니다.
- **권한 검증:** 사용자는 자신이 업로드한 문서만 조회/삭제할 수 있습니다.
- **파일 형식 검증:** MIME 타입 기반으로 허용된 형식만 업로드 가능합니다.

### 아키텍처 (계층 분리)

Documents 도메인은 SOLID 원칙을 따라 계층이 분리되어 있습니다:

1. **Controller (`controller.py`)**: HTTP 요청/응답 처리, 인증 검증
2. **Service (`service.py`)**: 비즈니스 로직 (파일 검증, MinIO 업로드, 에러 처리)
3. **Repository (`repository.py`)**: DB CRUD 연산 (N+1 문제 방지)
4. **Schema (`schema.py`)**: Pydantic 모델 (요청/응답 검증)
5. **Models (`models.py`)**: SQLAlchemy ORM 모델 (DB 테이블)

---

## 🏷️ Tags & DocumentTags (태그 시스템)

Tags 도메인은 문서 분류와 검색을 위한 태그 관리 기능을 제공합니다. **다대다(Many-to-Many) 관계**를 지원하여 하나의 문서에 여러 태그를 연결할 수 있습니다.

### 데이터베이스 구조

#### 1. `tags` 테이블
```sql
CREATE TABLE tags (
    tag_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

- **tag_id**: 태그 고유 ID (자동 증가)
- **name**: 태그 이름 (중복 불가, 인덱스)
- **created_at**: 태그 생성 일시

#### 2. `document_tags` 테이블 (연결 테이블)
```sql
CREATE TABLE document_tags (
    document_id BIGINT REFERENCES documents(document_id) ON DELETE CASCADE,
    tag_id BIGINT REFERENCES tags(tag_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (document_id, tag_id)
);
```

- **document_id**: 문서 ID (외래 키, CASCADE 삭제)
- **tag_id**: 태그 ID (외래 키, CASCADE 삭제)
- **created_at**: 연결 생성 일시
- **복합 기본 키**: (document_id, tag_id) - 중복 연결 방지

### AI 기반 자동 태깅 (Keyword Extraction)

문서 업로드 시 AI가 자동으로 키워드를 추출하고 태그를 생성합니다. 이 시스템은 **하이브리드 추출 전략**을 사용하여 데이터 양에 따라 최적의 방법을 선택합니다.

#### 하이브리드 추출 전략 (Cold Start → Normal)

**1. Cold Start 모드 (문서 수 < 임계값)**
- **사용 조건**: Elasticsearch 색인 문서 수 < 10개 (기본 임계값)
- **추출 방법**: KeyBERT (BERT 기반 임베딩)
- **장점**:
  - 문서 간 비교 데이터가 부족해도 단일 문서에서 의미 있는 키워드 추출
  - 문맥을 고려한 의미론적 키워드 추출
- **추출 과정**:
  ```python
  # KeyBERT 모델 로드 (Lazy Loading)
  model = KeyBERT()

  # 키워드 추출
  keywords = model.extract_keywords(
      text,
      keyphrase_ngram_range=(1, 2),  # 1~2 단어 구문까지 키워드로 고려
      stop_words='english',          # 영어 불용어 제거 (is, a, the 등)
      top_n=3,                        # 상위 3개 키워드 추출
      use_maxsum=True,                # 다양성 증가 (키워드 중복 방지)
      nr_candidates=20                # 내부 후보 키워드 20개 생성 후 필터링
  )
  # 결과: [("machine learning", 0.85), ("deep learning", 0.78), ...]
  ```

**2. Normal 모드 (문서 수 >= 임계값)**
- **사용 조건**: Elasticsearch 색인 문서 수 >= 10개
- **추출 방법**: Elasticsearch TF-IDF (Term Vectors API)
- **장점**:
  - 전체 문서 컬렉션과 비교하여 상대적 중요도 계산
  - 다른 문서에는 없지만 해당 문서에서 중요한 키워드 추출
- **추출 과정**:
  ```python
  # Term Vectors API로 TF-IDF 계산
  tv_response = await client.termvectors(
      index="documents",
      id=str(document_id),
      fields=["content"],
      term_statistics=True,
      field_statistics=True
  )

  # TF-IDF 점수 계산
  for term, term_info in terms.items():
      tf = term_info["term_freq"]        # 해당 문서에서 단어 빈도
      df = term_info["doc_freq"]         # 전체 문서에서 단어 빈도
      idf = log((total_docs + 1) / (df + 1)) + 1
      tfidf = tf * idf

  # 상위 N개 추출 (점수 기준 정렬)
  keywords = sorted(scores, reverse=True)[:3]
  ```

#### 전체 추출 프로세스 (9단계)

```
[1] 사용자 파일 업로드 (Controller)
    ↓
[2] 파일 형식 검증 (Service)
    - MIME 타입 검증 (PDF, DOCX, PPTX, XLSX, TXT만 허용)
    ↓
[3] 고유 경로 생성 (Service)
    - UUID 기반 파일명 생성: {user_id}/{uuid}.확장자
    - 예: 123/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf
    ↓
[4] MinIO 업로드 (MinIO Client)
    - 버킷: user-documents
    - 객체 스토리지에 실제 파일 저장
    ↓
[5] PostgreSQL 메타데이터 저장 (Repository)
    - 테이블: documents
    - 컬럼: document_id, user_id, original_filename, storage_path, file_type, file_size_kb
    ↓
[6] 텍스트 추출 (TextExtractor)
    - PDF → pypdf 라이브러리
    - DOCX → python-docx 라이브러리
    - XLSX → openpyxl 라이브러리
    - PPTX → python-pptx 라이브러리
    - TXT → UTF-8/CP949 디코딩
    ↓
[7] Elasticsearch 색인 (Elasticsearch Client)
    - 인덱스: documents
    - 필드: document_id, user_id, content, filename, file_type, uploaded_at
    - 한국어 분석기 적용 (korean_analyzer)
    ↓
[8] 하이브리드 키워드 추출 (Keyword Extraction Service)
    ├─ 문서 수 확인: await elasticsearch_client.get_document_count()
    ├─ 문서 < 10: KeyBERT 사용 (Cold Start)
    └─ 문서 >= 10: Elasticsearch TF-IDF 사용 (Normal)
    ↓
[9] 태그 생성 및 문서 연결 (TagService)
    - tags 테이블: Get-or-Create 패턴 (중복 방지)
    - document_tags 테이블: Bulk Insert (N+1 방지)
```

#### 코드 흐름 (파일 → 함수 단위)

**Controller Layer** (`documents/controller.py:34-78`)
```python
@router.post("/upload")
async def upload_document(file: UploadFile, user_id: int, document_service: DocumentService):
    # 1. Service 호출
    document, tags, extraction_method = await document_service.upload_document(
        user_id=user_id,
        file=file
    )

    # 2. 응답 생성
    return DocumentUploadResponse(
        document_id=document.document_id,
        tags=[TagSchema(tag_id=tag.tag_id, name=tag.name) for tag in tags],
        extraction_method=extraction_method  # "keybert" or "elasticsearch"
    )
```

**Service Layer** (`documents/service.py:48-158`)
```python
async def upload_document(user_id: int, file: UploadFile):
    # Step 1-3: 검증 및 경로 생성
    unique_filename = f"{uuid.uuid4()}{file.suffix}"  # UUID 생성
    storage_path = f"{user_id}/{unique_filename}"

    # Step 4: MinIO 업로드
    minio_client.upload_file(storage_path, file_data, file_size, content_type)

    # Step 5: PostgreSQL 저장
    document = await document_repository.create(
        user_id, original_filename, storage_path, file_type, file_size_kb
    )

    # Step 6: 텍스트 추출
    extracted_text = text_extractor.extract_text_from_bytes(
        file_data, file_type, filename
    )

    # Step 7: Elasticsearch 색인
    await elasticsearch_client.index_document(
        document_id=document.document_id,
        user_id=user_id,
        content=extracted_text,
        filename=filename,
        file_type=file_type,
        uploaded_at=document.uploaded_at.isoformat()
    )

    # Step 8: 하이브리드 키워드 추출
    keywords, extraction_method = await keyword_extraction_service.extract_keywords(
        text=extracted_text,
        document_id=document.document_id
    )

    # Step 9: 태그 생성 및 연결
    tags = await tag_service.attach_tags_to_document(
        document_id=document.document_id,
        tag_names=keywords
    )

    return document, tags, extraction_method
```

**TextExtractor** (`core/text_extractor.py:14-56`)
```python
@staticmethod
def extract_text_from_bytes(file_data: bytes, file_type: str, filename: str):
    # 파일 타입에 따라 적절한 라이브러리 사용
    if file_type == "application/pdf":
        return TextExtractor._extract_from_pdf(file_data)
    elif file_type == "text/plain":
        return TextExtractor._extract_from_txt(file_data)
    elif "wordprocessing" in file_type:  # DOCX
        return TextExtractor._extract_from_docx(file_data)
    elif "spreadsheet" in file_type:     # XLSX
        return TextExtractor._extract_from_excel(file_data)
    elif "presentation" in file_type:    # PPTX
        return TextExtractor._extract_from_pptx(file_data)

@staticmethod
def _extract_from_pdf(file_data: bytes):
    """PDF에서 텍스트 추출 (pypdf 라이브러리)"""
    import pypdf
    pdf_reader = pypdf.PdfReader(BytesIO(file_data))
    text_parts = [page.extract_text() for page in pdf_reader.pages]
    return "\n".join(text_parts)
```

**Elasticsearch Client** (`core/elasticsearch_client.py:83-127`)
```python
async def index_document(document_id, user_id, content, filename, file_type, uploaded_at):
    """Elasticsearch에 문서 색인"""
    doc_body = {
        "document_id": document_id,
        "user_id": user_id,
        "content": content,              # 추출된 텍스트
        "filename": filename,
        "file_type": file_type,
        "uploaded_at": uploaded_at
    }

    await self.client.index(
        index="documents",
        id=str(document_id),
        document=doc_body
    )

async def extract_significant_terms(document_id, size=3):
    """Elasticsearch TF-IDF 기반 키워드 추출"""
    tv_response = await self.client.termvectors(
        index="documents",
        id=str(document_id),
        fields=["content"],
        term_statistics=True,
        field_statistics=True
    )

    # TF-IDF 계산
    terms = tv_response["term_vectors"]["content"]["terms"]
    term_scores = []
    for term, term_info in terms.items():
        tf = term_info["term_freq"]
        df = term_info["doc_freq"]
        total_docs = tv_response["term_vectors"]["content"]["field_statistics"]["doc_count"]
        idf = math.log((total_docs + 1) / (df + 1)) + 1
        tfidf = tf * idf

        if 2 <= len(term) <= 30:  # 단어 길이 필터
            term_scores.append((term, tfidf))

    # 상위 N개 반환
    term_scores.sort(key=lambda x: x[1], reverse=True)
    return [term for term, score in term_scores[:size]]
```

**Keyword Extraction Service** (`core/keyword_extraction.py:142-178`)
```python
class HybridKeywordExtractionService:
    """하이브리드 키워드 추출 서비스 (Orchestrator)"""

    async def extract_keywords(text, document_id):
        # 1. 현재 Elasticsearch 문서 수 확인
        document_count = await elasticsearch_client.get_document_count()

        # 2. 임계값 기반 전략 선택
        if document_count < self.threshold:  # 기본값: 10
            # Cold Start: KeyBERT 사용
            keywords = await keybert_extractor.extract_keywords(text)
            method = "keybert"
        else:
            # Normal: Elasticsearch TF-IDF 사용
            keywords = await elasticsearch_extractor.extract_keywords(text, document_id)
            method = "elasticsearch"

        # 3. 키워드 정규화 (소문자, 중복 제거)
        keywords = list(set(kw.strip().lower() for kw in keywords))

        return keywords, method

class KeyBERTExtractor(KeywordExtractor):
    """KeyBERT 기반 키워드 추출기"""

    async def extract_keywords(text, document_id=None):
        # KeyBERT 모델 로드 (최초 1회)
        if self.model is None:
            from keybert import KeyBERT
            self.model = KeyBERT()

        # 키워드 추출
        keywords_with_scores = self.model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=3,
            use_maxsum=True,
            nr_candidates=20
        )

        return [kw[0] for kw in keywords_with_scores]

class ElasticsearchExtractor(KeywordExtractor):
    """Elasticsearch TF-IDF 기반 키워드 추출기"""

    async def extract_keywords(text, document_id):
        keywords = await elasticsearch_client.extract_significant_terms(
            document_id=document_id,
            size=3
        )
        return keywords
```

**Tag Service** (`tags/service.py:59-87`)
```python
async def attach_tags_to_document(document_id, tag_names):
    """태그 생성 및 문서 연결"""
    # 1. 태그 조회 또는 생성 (Get-or-Create, N+1 방지)
    tags = await self.get_or_create_tags(tag_names)

    # 2. 문서-태그 연결 생성 (Bulk Insert)
    tag_ids = [tag.tag_id for tag in tags]
    await self.document_tag_repository.bulk_create(document_id, tag_ids)

    return tags
```

**Tag Repository** (`tags/repository.py:121-147`)
```python
async def bulk_get_or_create(names):
    """여러 태그를 한 번에 조회 또는 생성 (N+1 방지)"""
    # 1. 기존 태그 조회 (한 번의 쿼리)
    existing_tags = await find_all_by_names(names)
    existing_tag_names = {tag.name for tag in existing_tags}

    # 2. 신규 태그 필터링
    new_tag_names = [name for name in names if name not in existing_tag_names]

    # 3. 신규 태그 생성 (Bulk Insert)
    new_tags = await bulk_create(new_tag_names) if new_tag_names else []

    # 4. 기존 + 신규 반환
    return existing_tags + new_tags

async def bulk_create(names):
    """여러 태그를 한 번에 생성"""
    tags = [Tag(name=name) for name in names]
    self.db.add_all(tags)
    await self.db.commit()
    return tags
```

**Document Tag Repository** (`tags/repository.py:182-207`)
```python
async def bulk_create(document_id, tag_ids):
    """문서-태그 연결 생성 (Bulk Insert)"""
    document_tags = [
        DocumentTag(document_id=document_id, tag_id=tag_id)
        for tag_id in tag_ids
    ]
    self.db.add_all(document_tags)
    await self.db.commit()
    return document_tags
```

### 태그 관리 기능

#### 1. Get-or-Create 패턴
- 태그가 이미 존재하면 재사용, 없으면 신규 생성
- 중복 태그 방지 및 데이터 일관성 유지

```python
# 예시: "machine learning" 태그
tag = await tag_service.get_or_create_tag("machine learning")
```

#### 2. N+1 문제 방지
- 여러 태그를 한 번의 쿼리로 조회/생성
- `bulk_get_or_create()` 메서드 사용

```python
# 예시: 3개 태그를 한 번에 처리
tags = await tag_service.get_or_create_tags(
    ["machine learning", "deep learning", "neural network"]
)
```

#### 3. CASCADE 삭제
- 문서 삭제 시 연결된 `document_tags` 자동 삭제
- 태그는 다른 문서에서도 사용될 수 있으므로 유지

### 아키텍처 (계층 분리)

Tags 도메인도 SOLID 원칙을 따라 계층이 분리되어 있습니다:

1. **Models (`models.py`)**:
   - `Tag`: 태그 엔티티
   - `DocumentTag`: 문서-태그 연결 엔티티

2. **Repository (`repository.py`)**:
   - `TagRepository`: 태그 CRUD 연산
   - `DocumentTagRepository`: 문서-태그 연결 CRUD 연산

3. **Service (`service.py`)**:
   - `TagService`: 태그 비즈니스 로직 (Get-or-Create, 문서 연결)

4. **Schema (`schema.py`)**:
   - `TagResponse`: 태그 응답 스키마
   - `DocumentTagResponse`: 문서-태그 연결 응답 스키마
   - `ExtractedKeywordsResponse`: 키워드 추출 결과 스키마

### 성능 최적화

- **인덱스**: `tags.name` 컬럼에 인덱스 설정 (빠른 조회)
- **Bulk Operations**: 여러 태그를 한 번에 처리하여 DB 쿼리 최소화
- **Eager Loading**: `selectinload()`를 사용하여 N+1 문제 방지
- **트랜잭션**: 태그 생성/연결을 하나의 트랜잭션으로 처리

---

## 🗄️ MinIO (객체 스토리지)

MinIO는 Amazon S3 호환 API를 제공하는 오픈소스 객체 스토리지입니다. Searchive에서는 사용자 업로드 문서를 저장하는 데 사용됩니다.

### MinIO 구조

**버킷 구조:**
```
user-documents/              # 버킷 이름
  ├── 1/                     # user_id=1
  │   ├── a1b2c3d4-uuid.pdf
  │   ├── e5f6g7h8-uuid.docx
  │   └── i9j0k1l2-uuid.xlsx
  ├── 2/                     # user_id=2
  │   ├── m3n4o5p6-uuid.pdf
  │   └── q7r8s9t0-uuid.txt
  └── 3/                     # user_id=3
      └── u1v2w3x4-uuid.pptx
```

### MinIO Client 구현 (`core/minio_client.py`)

**주요 기능:**

#### 1. 파일 업로드
```python
def upload_file(file_path: str, file_data: BytesIO, file_size: int, content_type: str):
    """
    MinIO에 파일 업로드

    Args:
        file_path: 저장 경로 (예: "1/uuid.pdf")
        file_data: 파일 바이트 스트림
        file_size: 파일 크기 (bytes)
        content_type: MIME 타입 (예: "application/pdf")
    """
    client.put_object(
        bucket_name=BUCKET_NAME,
        object_name=file_path,
        data=file_data,
        length=file_size,
        content_type=content_type
    )
```

#### 2. 파일 다운로드
```python
def download_file(file_path: str) -> bytes:
    """
    MinIO에서 파일 다운로드

    Returns:
        파일 바이트 데이터
    """
    response = client.get_object(
        bucket_name=BUCKET_NAME,
        object_name=file_path
    )
    return response.read()
```

#### 3. 파일 삭제
```python
def delete_file(file_path: str):
    """
    MinIO에서 파일 삭제
    """
    client.remove_object(
        bucket_name=BUCKET_NAME,
        object_name=file_path
    )
```

### MinIO 장점

1. **확장성**: 수평 확장으로 대용량 파일 저장 가능
2. **비용 효율**: 오픈소스로 무료 사용 가능
3. **S3 호환**: AWS S3 API와 호환되어 마이그레이션 용이
4. **보안**: 접근 제어 및 암호화 지원
5. **성능**: 높은 처리량과 낮은 지연시간

### 환경 변수 설정

```bash
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=user-documents
MINIO_SECURE=False  # HTTPS 사용 여부
```

---

## 🔍 Elasticsearch (검색 엔진)

Elasticsearch는 분산형 검색 및 분석 엔진입니다. Searchive에서는 문서 전문 검색과 TF-IDF 기반 키워드 추출에 사용됩니다.

### Elasticsearch 인덱스 구조

**인덱스 이름:** `documents`

**매핑 (Mapping):**
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "korean_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase"]
        }
      }
    },
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "document_id": {"type": "long"},
      "user_id": {"type": "long"},
      "content": {
        "type": "text",
        "analyzer": "korean_analyzer",
        "fielddata": true  # TF-IDF 계산을 위해 필요
      },
      "filename": {"type": "keyword"},
      "file_type": {"type": "keyword"},
      "uploaded_at": {"type": "date"}
    }
  }
}
```

### Elasticsearch Client 구현 (`core/elasticsearch_client.py`)

**주요 기능:**

#### 1. 문서 색인 (Indexing)
```python
async def index_document(document_id, user_id, content, filename, file_type, uploaded_at):
    """
    Elasticsearch에 문서 색인

    - 전문 검색을 위한 역색인 생성
    - TF-IDF 계산을 위한 통계 수집
    """
    doc_body = {
        "document_id": document_id,
        "user_id": user_id,
        "content": content,              # 추출된 텍스트
        "filename": filename,
        "file_type": file_type,
        "uploaded_at": uploaded_at
    }

    await client.index(
        index="documents",
        id=str(document_id),
        document=doc_body
    )
```

#### 2. TF-IDF 기반 키워드 추출
```python
async def extract_significant_terms(document_id, size=3):
    """
    Term Vectors API를 사용한 TF-IDF 키워드 추출

    TF-IDF (Term Frequency - Inverse Document Frequency):
    - TF: 해당 문서에서 단어가 나타난 빈도
    - IDF: 전체 문서에서 단어의 희소성 (흔하지 않을수록 높음)
    - TF-IDF = TF × IDF

    높은 TF-IDF 점수를 가진 단어 = 해당 문서를 잘 대표하는 키워드
    """
    # 1. Term Vectors API 호출
    tv_response = await client.termvectors(
        index="documents",
        id=str(document_id),
        fields=["content"],
        term_statistics=True,      # DF (전체 문서에서 단어 빈도)
        field_statistics=True      # 전체 문서 수
    )

    # 2. TF-IDF 점수 계산
    terms = tv_response["term_vectors"]["content"]["terms"]
    term_scores = []

    for term, term_info in terms.items():
        # TF (Term Frequency)
        tf = term_info["term_freq"]

        # DF (Document Frequency)
        df = term_info["doc_freq"]

        # 전체 문서 수
        total_docs = tv_response["term_vectors"]["content"]["field_statistics"]["doc_count"]

        # IDF (Inverse Document Frequency) 계산
        import math
        idf = math.log((total_docs + 1) / (df + 1)) + 1

        # TF-IDF 점수
        tfidf = tf * idf

        # 단어 길이 필터 (너무 짧거나 긴 단어 제외)
        if 2 <= len(term) <= 30:
            term_scores.append((term, tfidf))

    # 3. 상위 N개 키워드 반환
    term_scores.sort(key=lambda x: x[1], reverse=True)
    keywords = [term for term, score in term_scores[:size]]

    return keywords
```

#### 3. 전문 검색 (Full-Text Search)
```python
async def search_documents(user_id, query, size=10):
    """
    사용자 문서 전문 검색

    - 한국어 분석기를 사용한 토큰화
    - BM25 랭킹 알고리즘 적용
    """
    search_body = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"content": query}},  # 전문 검색
                    {"term": {"user_id": user_id}}  # 사용자 필터
                ]
            }
        },
        "size": size
    }

    response = await client.search(
        index="documents",
        body=search_body
    )

    return response["hits"]["hits"]
```

### Elasticsearch 장점

1. **확장성**: 분산 아키텍처로 대용량 데이터 처리 가능
2. **실시간 검색**: Near Real-Time 검색 지원
3. **다양한 분석**: TF-IDF, BM25, 형태소 분석 등 지원
4. **RESTful API**: 간단한 HTTP 요청으로 사용 가능
5. **풍부한 쿼리 DSL**: 복잡한 검색 조건 표현 가능

### 환경 변수 설정

```bash
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=changeme
KEYWORD_EXTRACTION_THRESHOLD=10  # 하이브리드 전환 임계값
```

---

## 🤖 KeyBERT (AI 키워드 추출)

KeyBERT는 BERT 임베딩을 사용하여 문서에서 의미 있는 키워드를 추출하는 Python 라이브러리입니다.

### KeyBERT 동작 원리

**1. BERT 임베딩 생성**
```
문서 텍스트 → BERT 모델 → 문서 임베딩 (768차원 벡터)
각 단어/구문 → BERT 모델 → 단어 임베딩 (768차원 벡터)
```

**2. 코사인 유사도 계산**
```
similarity(문서, 키워드) = cosine(문서 임베딩, 키워드 임베딩)
```

**3. 상위 N개 키워드 선택**
```
유사도가 높은 키워드 = 문서와 의미적으로 관련성이 높은 키워드
```

### KeyBERT Extractor 구현 (`core/keyword_extraction.py`)

```python
class KeyBERTExtractor(KeywordExtractor):
    """KeyBERT 기반 키워드 추출기"""

    def __init__(self):
        self.model = None

    def _load_model(self):
        """
        KeyBERT 모델 로드 (Lazy Loading)

        - 최초 1회만 로드 (메모리 절약)
        - sentence-transformers 기반
        """
        if self.model is None:
            from keybert import KeyBERT
            self.model = KeyBERT()
            logger.info("KeyBERT 모델 로드 성공")

    async def extract_keywords(self, text, document_id=None):
        """
        KeyBERT를 사용한 키워드 추출

        Args:
            text: 대상 텍스트
            document_id: 사용하지 않음

        Returns:
            추출된 키워드 리스트
        """
        self._load_model()

        # KeyBERT 키워드 추출
        keywords_with_scores = self.model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),  # 1~2 단어 구문까지 키워드로 고려
            stop_words='english',          # 영어 불용어 제거 (is, a, the 등)
            top_n=3,                        # 상위 3개 키워드 추출
            use_maxsum=True,                # 다양성 증가 (키워드 중복 방지)
            nr_candidates=20                # 내부 후보 키워드 20개 생성 후 필터링
        )

        # (키워드, 점수) 튜플에서 키워드만 추출
        keywords = [kw[0] for kw in keywords_with_scores]

        return keywords
```

### KeyBERT 파라미터 설명

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| `keyphrase_ngram_range` | 키워드 단어 수 범위 | `(1, 2)` → "machine", "machine learning" |
| `stop_words` | 불용어 리스트 | `'english'` → "is", "a", "the" 제거 |
| `top_n` | 추출할 키워드 개수 | `3` → 상위 3개만 추출 |
| `use_maxsum` | 다양성 증가 | `True` → 중복된 의미 키워드 제거 |
| `nr_candidates` | 후보 키워드 수 | `20` → 20개 후보 중 best 선택 |

### KeyBERT 장점

1. **의미론적 이해**: BERT 임베딩으로 문맥 고려
2. **Cold Start 문제 해결**: 단일 문서만으로 키워드 추출 가능
3. **다국어 지원**: 한국어, 영어 등 다양한 언어 지원
4. **사전 학습 모델**: 추가 학습 없이 바로 사용 가능
5. **커스터마이징**: 다양한 파라미터로 조정 가능

### 환경 변수 설정

```bash
KEYWORD_EXTRACTION_COUNT=3              # 추출할 키워드 개수
KEYWORD_EXTRACTION_THRESHOLD=10         # 하이브리드 전환 임계값
```

### KeyBERT vs Elasticsearch 비교

| 항목 | KeyBERT | Elasticsearch TF-IDF |
|-----|---------|---------------------|
| **사용 시점** | Cold Start (문서 < 10개) | Normal (문서 >= 10개) |
| **원리** | BERT 임베딩 + 코사인 유사도 | TF-IDF 통계 |
| **장점** | 의미론적 정확도 높음 | 상대적 중요도 반영 |
| **단점** | 계산 비용 높음 | 문서 간 비교 데이터 필요 |
| **적합한 상황** | 초기 데이터 부족 시 | 충분한 문서 축적 후 |

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
