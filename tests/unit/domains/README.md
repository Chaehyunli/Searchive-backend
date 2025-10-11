# 도메인 단위 테스트 (Unit Tests)

이 디렉토리에는 각 도메인의 **단위 테스트(Unit Tests)**가 포함되어 있습니다.

## 🎯 단위 테스트 특징

### Mock 사용 - 실제 인프라 사용 안함 ✅

단위 테스트는 **Mock(모의 객체)**을 사용하여 다음을 방지합니다:

- ❌ **실제 MinIO에 파일 업로드 안됨**
- ❌ **실제 Elasticsearch에 색인 안됨**
- ❌ **실제 PostgreSQL에 데이터 저장 안됨** (Repository는 Mock)
- ❌ **실제 Redis에 캐시 저장 안됨**

### 장점

- ⚡ **빠른 실행 속도**: 네트워크 I/O 없음
- 🔒 **격리된 테스트**: 외부 의존성 없이 순수 로직만 테스트
- 🧹 **테스트 데이터 오염 없음**: 실제 인프라에 흔적 안 남음
- 🎯 **비즈니스 로직 검증**: Service 레이어의 로직만 집중 테스트

---

## 📂 테스트 구조

```
tests/
├── fixtures/                            # 테스트용 샘플 파일
│   ├── README.md
│   ├── test_elasticsearch_keywords.txt
│   └── sample_documents/
│       ├── sample.pdf               # 샘플 PDF 파일
│       ├── sample.docx              # 샘플 DOCX 파일
│       └── sample.txt               # 샘플 TXT 파일
├── conftest.py                      # Pytest 픽스처 설정
└── unit/domains/
    ├── documents/
    │   ├── __init__.py
    │   ├── test_document_service.py         # Mock 전용 테스트
    │   └── test_document_with_fixtures.py   # 실제 파일 + Mock 테스트 ✨
    └── tags/
        ├── __init__.py
        └── test_tag_service.py              # TagService 단위 테스트
```

---

## 🧪 테스트 케이스

### Documents 도메인

#### `test_document_service.py` - Mock 전용 테스트

**1. `TestDocumentServiceUpload` - 문서 업로드 테스트**
- `test_upload_document_success`: 문서 업로드 성공 (Mock 사용)
- `test_upload_document_invalid_file_type`: 잘못된 파일 형식 검증
- `test_upload_document_empty_text`: 텍스트 추출 실패 시 처리

**2. `TestDocumentServiceRetrieval` - 문서 조회 테스트**
- `test_get_user_documents`: 사용자 문서 목록 조회
- `test_get_document_by_id`: 문서 상세 조회

**3. `TestDocumentServiceDeletion` - 문서 삭제 테스트**
- `test_delete_document_success`: 문서 삭제 성공 (Mock 사용)
- `test_delete_document_not_found`: 존재하지 않는 문서 삭제

#### `test_document_with_fixtures.py` - 실제 파일 + Mock 테스트 ✨

**1. `TestDocumentServiceWithRealFiles` - 실제 샘플 파일 업로드 테스트**
- `test_upload_pdf_file_with_real_content`: 실제 PDF 파일 업로드 (MinIO는 Mock)
- `test_upload_docx_file_with_real_content`: 실제 DOCX 파일 업로드
- `test_upload_txt_file_with_real_content`: 실제 TXT 파일 업로드

**2. `TestTextExtractorWithRealFiles` - 실제 파일 텍스트 추출 테스트**
- `test_extract_text_from_real_pdf`: PDF에서 실제 텍스트 추출
- `test_extract_text_from_real_docx`: DOCX에서 실제 텍스트 추출
- `test_extract_text_from_real_txt`: TXT에서 실제 텍스트 추출

**3. `TestKeywordExtractionWithRealContent` - 실제 내용으로 키워드 추출 테스트**
- `test_keybert_extraction_with_sample_text`: 실제 샘플 텍스트로 KeyBERT 테스트

### Tags 도메인 (`test_tag_service.py`)

#### 1. `TestTagServiceGetOrCreate` - 태그 생성/조회 테스트
- `test_get_or_create_tag_existing`: 기존 태그 조회
- `test_get_or_create_tags_bulk`: 여러 태그 일괄 처리 (N+1 방지)
- `test_get_or_create_tags_with_duplicates`: 중복 태그 제거
- `test_get_or_create_tags_empty_list`: 빈 리스트 처리

#### 2. `TestTagServiceAttachment` - 태그 연결 테스트
- `test_attach_tags_to_document`: 문서에 태그 연결
- `test_attach_tags_empty_list`: 빈 태그 리스트 처리

#### 3. `TestTagServiceRetrieval` - 태그 조회 테스트
- `test_get_tags_by_document_id`: 문서 ID로 태그 조회
- `test_find_tag_by_name`: 태그 이름으로 조회
- `test_find_tag_by_name_not_found`: 존재하지 않는 태그 조회

---

## 🚀 테스트 실행 방법

### 1. 전체 단위 테스트 실행
```bash
pytest tests/unit/ -v
```

### 2. 특정 도메인 테스트 실행
```bash
# Documents 도메인만
pytest tests/unit/domains/documents/ -v

# Tags 도메인만
pytest tests/unit/domains/tags/ -v
```

### 3. 특정 테스트 클래스 실행
```bash
# 문서 업로드 테스트만
pytest tests/unit/domains/documents/test_document_service.py::TestDocumentServiceUpload -v

# 태그 생성 테스트만
pytest tests/unit/domains/tags/test_tag_service.py::TestTagServiceGetOrCreate -v
```

### 4. 특정 테스트 함수 실행
```bash
pytest tests/unit/domains/documents/test_document_service.py::TestDocumentServiceUpload::test_upload_document_success -v
```

### 5. 커버리지 포함 실행
```bash
pytest tests/unit/domains/ --cov=src/domains --cov-report=html
```

---

## 📝 Fixture 사용법

`conftest.py`에 정의된 픽스처들:

### Mock 픽스처 (실제 인프라 사용 안함)

#### 1. `mock_minio_client`
```python
def test_something(mock_minio_client):
    # MinIO 업로드 Mock (실제 업로드 안됨)
    mock_minio_client.upload_file.return_value = "path/to/file"
```

#### 2. `mock_elasticsearch_client`
```python
async def test_something(mock_elasticsearch_client):
    # Elasticsearch 색인 Mock (실제 색인 안됨)
    mock_elasticsearch_client.index_document.return_value = True
```

#### 3. `mock_text_extractor`
```python
def test_something(mock_text_extractor):
    # 텍스트 추출 Mock (실제 추출 안됨)
    mock_text_extractor.extract_text_from_bytes.return_value = "Test content"
```

#### 4. `mock_keyword_extraction_service`
```python
async def test_something(mock_keyword_extraction_service):
    # 키워드 추출 Mock
    mock_keyword_extraction_service.extract_keywords.return_value = (
        ["keyword1", "keyword2"],
        "keybert"
    )
```

#### 5. `mock_upload_file`
```python
async def test_something(mock_upload_file):
    # FastAPI UploadFile Mock (더미 데이터)
    # mock_upload_file.filename = "test.pdf"
    # mock_upload_file.content_type = "application/pdf"
```

### 실제 파일 픽스처 ✨ (실제 샘플 파일 사용)

#### 6. `sample_pdf_file` / `sample_docx_file` / `sample_txt_file`
```python
async def test_upload_with_real_file(sample_pdf_file, mock_minio_client):
    # 실제 PDF 파일 내용을 읽어서 UploadFile Mock 생성
    # sample_pdf_file.filename = "sample.pdf"
    # sample_pdf_file.content_type = "application/pdf"
    # 실제 PDF 바이트 데이터 포함

    # MinIO는 Mock이므로 실제 업로드 안됨
    with patch('src.domains.documents.service.minio_client', mock_minio_client):
        result = await service.upload_document(file=sample_pdf_file)
```

#### 7. `sample_pdf_path` / `sample_docx_path` / `sample_txt_path`
```python
def test_read_file(sample_pdf_path):
    # 샘플 파일 경로만 반환
    with open(sample_pdf_path, "rb") as f:
        file_content = f.read()
```

#### 8. `sample_text_content`
```python
async def test_keyword_extraction(sample_text_content):
    # 샘플 TXT 파일의 텍스트 내용 반환
    keywords = await extractor.extract_keywords(text=sample_text_content)
    assert "machine learning" in keywords
```

---

## 🎯 테스트 전략: Mock + 실제 파일

### 전략 1: 순수 Mock 테스트 (`test_document_service.py`)
```python
# 모든 것이 Mock - 가장 빠름
def test_upload(mock_minio_client, mock_text_extractor, mock_upload_file):
    # mock_upload_file: 더미 데이터
    # mock_text_extractor: 가짜 텍스트 반환
    # mock_minio_client: 실제 업로드 안함
```

**장점:** ⚡ 매우 빠름, 완전 격리
**단점:** 실제 파일 형식 검증 불가

### 전략 2: 실제 파일 + Mock 인프라 (`test_document_with_fixtures.py`) ✨ 추천
```python
# 실제 샘플 파일 + Mock 인프라
def test_upload(sample_pdf_file, mock_minio_client, mock_elasticsearch_client):
    # sample_pdf_file: 실제 PDF 파일 내용
    # TextExtractor: 실제로 PDF 파싱
    # mock_minio_client: 실제 업로드는 안함 (Mock)
```

**장점:** 실제 파일 형식 검증 가능, MinIO 업로드는 안함
**단점:** TextExtractor 실행으로 약간 느림

### 전략 3: 완전 통합 테스트 (Integration Test)
```python
# 실제 파일 + 실제 인프라
def test_upload(sample_pdf_file):
    # sample_pdf_file: 실제 PDF
    # MinIO: 실제 업로드됨 ⚠️
    # Elasticsearch: 실제 색인됨 ⚠️
```

**장점:** 완전한 E2E 검증
**단점:** 느림, 실제 데이터 오염, 인프라 필요

---

## ⚠️ 주의사항

### 1. Mock vs 실제 연결
- **Unit Test (이 디렉토리)**: Mock 사용 → 실제 인프라 안 씀
- **Integration Test**: 실제 MinIO, Elasticsearch, PostgreSQL 연결

### 2. 테스트 격리
- 각 테스트는 독립적으로 실행됩니다
- Mock 픽스처는 `@pytest.fixture`로 자동 주입됩니다
- 테스트 간 상태 공유 없음

### 3. 비동기 테스트
- `@pytest.mark.asyncio` 데코레이터 필수
- `async def test_*` 형식 사용

---

## 🔍 통합 테스트와 비교

| 항목 | Unit Test (여기) | Integration Test |
|-----|-----------------|------------------|
| **MinIO** | Mock (업로드 안됨) | 실제 연결 (업로드됨) |
| **Elasticsearch** | Mock (색인 안됨) | 실제 연결 (색인됨) |
| **PostgreSQL** | Mock Repository | 실제 DB 연결 |
| **실행 속도** | ⚡ 빠름 | 🐢 느림 |
| **데이터 오염** | ❌ 없음 | ✅ 있음 (테스트 후 정리 필요) |
| **목적** | 비즈니스 로직 검증 | 전체 통합 검증 |

---

## 📖 관련 문서

- [Pytest 공식 문서](https://docs.pytest.org/)
- [unittest.mock 문서](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-asyncio 문서](https://pytest-asyncio.readthedocs.io/)
