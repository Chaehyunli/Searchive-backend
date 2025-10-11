# Core 모듈 (핵심 인프라)

`src/core/` 폴더는 프로젝트 전반에서 사용되는 핵심 인프라 모듈들을 포함합니다.

---

## 📂 모듈 구조

```
src/core/
├── config.py                    # 환경 변수 설정
├── security.py                  # JWT 보안 유틸리티
├── exception.py                 # 전역 예외 처리
├── redis.py                     # Redis 세션 관리
├── minio_client.py              # MinIO 객체 스토리지 클라이언트
├── elasticsearch_client.py      # Elasticsearch 검색 엔진 클라이언트
├── text_extractor.py            # 파일 → 텍스트 추출기
└── keyword_extraction.py        # AI 키워드 추출 서비스
```

---

## 🗄️ MinIO (객체 스토리지)

### 개요

MinIO는 Amazon S3 호환 API를 제공하는 오픈소스 객체 스토리지입니다. Searchive에서는 사용자 업로드 문서를 저장하는 데 사용됩니다.

### 버킷 구조

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

- 각 사용자는 `user_id` 폴더로 격리됩니다.
- 파일명은 **UUID(고유 랜덤값)**로 저장되어 충돌과 추측을 방지합니다.
- 원본 파일명은 PostgreSQL의 `original_filename` 컬럼에 저장됩니다.

### MinIO Client 구현 (`minio_client.py`)

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

### 개요

Elasticsearch는 분산형 검색 및 분석 엔진입니다. Searchive에서는 문서 전문 검색과 TF-IDF 기반 키워드 추출에 사용됩니다.

### 인덱스 구조

**인덱스 이름:** `documents`

**매핑 (Mapping):**
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "korean_nori_analyzer": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": ["nori_pos_filter", "lowercase"]
        }
      },
      "filter": {
        "nori_pos_filter": {
          "type": "nori_part_of_speech",
          "stoptags": ["J", "E", "IC", "MAJ", "MM", "SP", "SSC", "SSO", ...]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "document_id": {"type": "long"},
      "user_id": {"type": "long"},
      "content": {
        "type": "text",
        "analyzer": "korean_nori_analyzer",
        "fielddata": true
      },
      "filename": {"type": "keyword"},
      "file_type": {"type": "keyword"},
      "uploaded_at": {"type": "date"}
    }
  }
}
```

### Nori 형태소 분석기 설정

Elasticsearch에서 한국어 키워드 추출 품질을 개선하기 위해 **Nori 형태소 분석기**를 사용합니다.

**문제점:**
- 기본 분석기 사용 시 "을", "를", "과", "와", "것이" 같은 조사와 어미가 키워드로 추출됨

**해결책:**
- Nori 플러그인을 설치하고 39개의 품사 태그를 필터링하여 불필요한 조사, 어미, 접사, 기호 등을 제거

**자세한 설정 가이드:** [`docs/NORI_SETUP.md`](../../docs/NORI_SETUP.md) 참고

### Elasticsearch Client 구현 (`elasticsearch_client.py`)

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
        "content": content,
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
    # Term Vectors API 호출
    tv_response = await client.termvectors(
        index="documents",
        id=str(document_id),
        fields=["content"],
        term_statistics=True,
        field_statistics=True
    )

    # TF-IDF 점수 계산 및 상위 N개 반환
    # ... (상세 구현은 elasticsearch_client.py:269-340 참고)
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
                    {"match": {"content": query}},
                    {"term": {"user_id": user_id}}
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

### 환경 변수 설정

```bash
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=changeme
KEYWORD_EXTRACTION_THRESHOLD=10  # 하이브리드 전환 임계값
```

---

## 📄 TextExtractor (텍스트 추출기)

### 개요

`text_extractor.py`는 다양한 파일 형식(PDF, DOCX, XLSX, PPTX, TXT, HWP 등)에서 텍스트를 추출하는 모듈입니다.

### 지원 파일 형식

| 형식 | MIME Type | 라이브러리 |
|------|-----------|-----------|
| PDF | `application/pdf` | `pypdf` |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `python-docx` |
| XLSX | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | `openpyxl` |
| PPTX | `application/vnd.openxmlformats-officedocument.presentationml.presentation` | `python-pptx` |
| TXT | `text/plain` | UTF-8/CP949 디코딩 |
| HWP | `application/x-hwp`, `application/haansofthwp` | `olefile` |

### 구현 (`text_extractor.py`)

#### 메인 엔트리 포인트

```python
@staticmethod
def extract_text_from_bytes(file_data: bytes, file_type: str, filename: str) -> Optional[str]:
    """
    파일 타입에 따라 적절한 추출기 호출
    """
    if file_type == "application/pdf":
        return TextExtractor._extract_from_pdf(file_data)
    elif file_type == "text/plain":
        return TextExtractor._extract_from_txt(file_data)
    elif "wordprocessing" in file_type:
        return TextExtractor._extract_from_docx(file_data)
    elif "spreadsheet" in file_type:
        return TextExtractor._extract_from_excel(file_data)
    elif "presentation" in file_type:
        return TextExtractor._extract_from_pptx(file_data)
    elif "hwp" in file_type or "haansoft" in file_type:
        return TextExtractor._extract_from_hwp(file_data)
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {file_type}")
```

#### HWP 파일 처리

HWP 파일은 OLE 구조를 가지며, 내부적으로 zlib 압축된 BodyText 섹션을 포함합니다.

```python
@staticmethod
def _extract_from_hwp(file_data: bytes) -> Optional[str]:
    """
    HWP 파일에서 텍스트 추출

    1. OLE 파일 열기
    2. BodyText/* 섹션 찾기 및 정렬
    3. zlib 압축 해제
    4. 레코드 파싱 (Record ID 67 = HWPTAG_PARA_TEXT)
    5. UTF-16LE 디코딩
    """
    import olefile, zlib, struct

    ole = olefile.OleFileIO(BytesIO(file_data))

    # BodyText 섹션 추출 및 정렬
    bodytext_streams = sorted(
        [s for s in ole.listdir() if s[0] == "BodyText"],
        key=lambda x: int(x[1].replace("Section", ""))
    )

    text_parts = []
    for stream in bodytext_streams:
        compressed_data = ole.openstream(stream).read()
        unpacked = zlib.decompress(compressed_data, -15)
        text_parts.append(TextExtractor._parse_hwp_text(unpacked))

    return "\n".join(text_parts)

@staticmethod
def _parse_hwp_text(data: bytes) -> str:
    """
    HWP 바이너리에서 텍스트 레코드 파싱

    레코드 구조:
    - 4 bytes: 헤더 (하위 10비트 = Record ID)
    - 4 bytes: 레코드 크기
    - N bytes: 레코드 데이터
    """
    text_parts = []
    pos = 0

    while pos < len(data):
        record_header = struct.unpack("<I", data[pos:pos+4])[0]
        record_id = record_header & 0x3FF
        record_size = struct.unpack("<I", data[pos+4:pos+8])[0]

        if record_id == 67:  # HWPTAG_PARA_TEXT
            record_data = data[pos+8:pos+8+record_size]
            text = record_data.decode('utf-16le', errors='ignore')
            text_parts.append(text.replace('\x00', ''))

        pos += 8 + record_size

    return "".join(text_parts)
```

---

## 🤖 KeyBERT (AI 키워드 추출)

### 개요

KeyBERT는 BERT 임베딩을 사용하여 문서에서 의미 있는 키워드를 추출하는 Python 라이브러리입니다.

### 동작 원리

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

### 하이브리드 키워드 추출 전략 (`keyword_extraction.py`)

Searchive는 **Cold Start → Normal** 전환 전략을 사용합니다.

#### 1. Cold Start 모드 (문서 수 < 10개)

- **추출 방법**: KeyBERT (BERT 기반 임베딩)
- **장점**: 문서 간 비교 데이터 부족 시에도 단일 문서에서 의미 있는 키워드 추출
- **추출 과정**:

```python
class KeyBERTExtractor(KeywordExtractor):
    async def extract_keywords(self, text, document_id=None):
        self._load_model()  # Lazy Loading

        keywords_with_scores = self.model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),  # 1~2 단어 구문까지
            stop_words='english',          # 불용어 제거
            top_n=3,                        # 상위 3개
            use_maxsum=True,                # 다양성 증가
            nr_candidates=20                # 후보 20개 생성
        )

        return [kw[0] for kw in keywords_with_scores]
```

#### 2. Normal 모드 (문서 수 >= 10개)

- **추출 방법**: Elasticsearch TF-IDF
- **장점**: 전체 문서 컬렉션과 비교하여 상대적 중요도 계산

```python
class ElasticsearchExtractor(KeywordExtractor):
    async def extract_keywords(self, text, document_id):
        keywords = await elasticsearch_client.extract_significant_terms(
            document_id=document_id,
            size=3
        )
        return keywords
```

#### 3. Hybrid Orchestrator

```python
class HybridKeywordExtractionService:
    async def extract_keywords(self, text, document_id):
        # 1. 현재 Elasticsearch 문서 수 확인
        document_count = await elasticsearch_client.get_document_count()

        # 2. 임계값 기반 전략 선택
        if document_count < self.threshold:
            keywords = await keybert_extractor.extract_keywords(text)
            method = "keybert"
        else:
            keywords = await elasticsearch_extractor.extract_keywords(text, document_id)
            method = "elasticsearch"

        # 3. 정규화 (소문자, 중복 제거)
        keywords = list(set(kw.strip().lower() for kw in keywords))

        return keywords, method
```

### KeyBERT vs Elasticsearch 비교

| 항목 | KeyBERT | Elasticsearch TF-IDF |
|-----|---------|---------------------|
| **사용 시점** | Cold Start (문서 < 10개) | Normal (문서 >= 10개) |
| **원리** | BERT 임베딩 + 코사인 유사도 | TF-IDF 통계 |
| **장점** | 의미론적 정확도 높음 | 상대적 중요도 반영 |
| **단점** | 계산 비용 높음 | 문서 간 비교 데이터 필요 |

### 환경 변수 설정

```bash
KEYWORD_EXTRACTION_COUNT=3              # 추출할 키워드 개수
KEYWORD_EXTRACTION_THRESHOLD=10         # 하이브리드 전환 임계값
```

---

## 📚 참고 자료

- [MinIO 공식 문서](https://min.io/docs/minio/kubernetes/upstream/)
- [Elasticsearch Python Client](https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/index.html)
- [KeyBERT 공식 문서](https://maartengr.github.io/KeyBERT/)
- [Nori 형태소 분석기 설정 가이드](../../docs/NORI_SETUP.md)
