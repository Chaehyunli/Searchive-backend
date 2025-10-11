# 테스트 픽스처 (Test Fixtures)

이 디렉토리에는 테스트에 사용되는 샘플 데이터와 파일들이 포함되어 있습니다.

## 📁 파일 목록

### `test_elasticsearch_keywords.txt`
- **용도**: Elasticsearch 키워드 추출 테스트용 샘플 텍스트
- **내용**: Machine learning과 AI에 관한 간단한 영문 텍스트
- **사용처**:
  - `tests/integration/test_elasticsearch_extraction.py`
  - Keyword extraction 기능 테스트

## 📝 사용 방법

### 1. 테스트 코드에서 픽스처 읽기

```python
import os
from pathlib import Path

# 픽스처 파일 경로
fixtures_dir = Path(__file__).parent.parent / "fixtures"
test_file = fixtures_dir / "test_elasticsearch_keywords.txt"

# 파일 읽기
with open(test_file, "r", encoding="utf-8") as f:
    test_content = f.read()
```

### 2. Pytest 픽스처로 등록

`conftest.py`에 추가:
```python
@pytest.fixture
def sample_text_for_elasticsearch():
    """Elasticsearch 테스트용 샘플 텍스트"""
    fixtures_dir = Path(__file__).parent / "fixtures"
    test_file = fixtures_dir / "test_elasticsearch_keywords.txt"

    with open(test_file, "r", encoding="utf-8") as f:
        return f.read()
```

사용:
```python
def test_keyword_extraction(sample_text_for_elasticsearch):
    # 샘플 텍스트 사용
    keywords = extract_keywords(sample_text_for_elasticsearch)
    assert "machine learning" in keywords
```

## 🗂️ 추가 가능한 픽스처

향후 추가할 수 있는 테스트 파일들:

```
tests/fixtures/
├── README.md
├── test_elasticsearch_keywords.txt       # ✅ 현재
├── sample_documents/                     # 샘플 문서 파일들
│   ├── sample.pdf                        # PDF 테스트용
│   ├── sample.docx                       # DOCX 테스트용
│   ├── sample.xlsx                       # XLSX 테스트용
│   └── sample.txt                        # TXT 테스트용
├── mock_responses/                       # API Mock 응답
│   ├── kakao_oauth_response.json
│   └── elasticsearch_response.json
└── test_data/                            # 테스트 데이터
    ├── users.json
    ├── documents.json
    └── tags.json
```

## ⚠️ 주의사항

1. **민감한 정보 포함 금지**
   - API 키, 비밀번호, 토큰 등 절대 포함하지 말 것
   - Git에 커밋되므로 공개 데이터만 사용

2. **파일 크기**
   - 큰 파일은 Git LFS 사용 고려
   - 가능한 작은 샘플 파일 사용

3. **인코딩**
   - 텍스트 파일은 UTF-8 인코딩 사용
   - BOM 없는 UTF-8 권장

4. **파일 이름 규칙**
   - `test_` 또는 `sample_` 접두사 사용
   - 소문자와 언더스코어(_) 사용
   - 명확한 이름 (용도 파악 가능)
