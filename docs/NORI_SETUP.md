# Elasticsearch Nori 형태소 분석기 설정 가이드

## 개요

이 가이드는 Elasticsearch에 Nori 형태소 분석기를 설정하여 한국어 키워드 추출 품질을 개선하는 방법을 설명합니다.

### 문제점

기본 분석기를 사용하면 "을", "를", "것이"와 같은 **조사**와 **어미**가 키워드로 추출되는 문제가 발생합니다.

### 해결책

Nori 형태소 분석기를 사용하여 텍스트를 품사 단위로 분석하고, 조사(J), 어미(E) 등 불필요한 품사를 필터링합니다.

---

## 1단계: Nori 플러그인 설치

### Docker Compose를 사용하는 경우

`docker-compose.yml` 파일에서 Elasticsearch 서비스에 플러그인 설치 명령 추가:

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  container_name: searchive-elasticsearch
  environment:
    - discovery.type=single-node
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    - xpack.security.enabled=true
    - ELASTIC_PASSWORD=your_password
  volumes:
    - elasticsearch-data:/usr/share/elasticsearch/data
  # 플러그인 설치 후 재시작
  command: >
    bash -c "
      bin/elasticsearch-plugin install analysis-nori || true &&
      /usr/local/bin/docker-entrypoint.sh
    "
  ports:
    - "9200:9200"
  networks:
    - searchive-network
```

그런 다음 컨테이너를 재시작합니다:

```bash
docker-compose down
docker-compose up -d
```

### 직접 설치하는 경우 (Elasticsearch 서버에서 실행)

```bash
# Elasticsearch 설치 경로로 이동
cd /usr/share/elasticsearch

# Nori 플러그인 설치
bin/elasticsearch-plugin install analysis-nori

# Elasticsearch 재시작 (필수!)
sudo systemctl restart elasticsearch
```

### 설치 확인

```bash
curl -X GET "localhost:9200/_nodes/plugins?pretty"
```

출력에서 `"name": "analysis-nori"`를 확인합니다.

---

## 2단계: 인덱스 재생성 및 데이터 재색인

### Python 스크립트 실행

프로젝트에서 제공하는 재색인 스크립트를 실행합니다:

```bash
# 가상환경 활성화
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# 재색인 스크립트 실행
python scripts/reindex_with_nori.py
```

### 스크립트가 수행하는 작업

1. **Nori 플러그인 확인**: 설치 여부를 확인합니다.
2. **기존 데이터 로드**: PostgreSQL에서 모든 문서 메타데이터를 가져옵니다.
3. **텍스트 추출**: MinIO에서 파일을 다운로드하고 텍스트를 추출합니다.
4. **인덱스 재생성**: 기존 인덱스를 삭제하고 Nori 분석기가 적용된 새 인덱스를 생성합니다.
5. **데이터 재색인**: 추출한 텍스트를 Elasticsearch에 재색인합니다.

### 주의사항

⚠️ **이 작업은 기존 Elasticsearch 인덱스를 삭제합니다!**

- 작업 전에 중요한 데이터를 백업하세요.
- PostgreSQL과 MinIO에 원본 데이터가 있으므로 재색인이 가능합니다.

---

## 3단계: 동작 확인

### 테스트 문서 업로드

```bash
# 테스트 문서를 업로드합니다 (API 사용)
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@test_document.pdf"
```

### 키워드 추출 확인

문서 상세 조회 시 tags 필드를 확인합니다:

```json
{
  "document_id": 1,
  "tags": [
    {"tag_id": 1, "name": "머신러닝"},
    {"tag_id": 2, "name": "인공지능"},
    {"tag_id": 3, "name": "데이터"}
  ]
}
```

**개선 전**: `["연구를", "것이", "분석"]`
**개선 후**: `["연구", "분석", "모델"]`

---

## Nori 분석기 설정 상세

### 필터링되는 품사 (stoptags)

| 품사 코드 | 의미 | 예시 |
|----------|------|------|
| `J` | 조사 | 을, 를, 이, 가, 은, 는 |
| `E` | 어미 | 다, 어, 요 |
| `IC` | 감탄사 | 아, 아이고 |
| `MAJ` | 접속 부사 | 그리고, 그러나 |
| `MM` | 관형사 | 이, 그, 저 |
| `SP` | 쉼표, 콜론 등 | `,`, `:` |
| `SSC`, `SSO` | 괄호 | `(`, `)` |
| `SC` | 구분자 | |
| `SE` | 생략 기호 | `...` |
| `XPN` | 접두사 | 재-, 비- |
| `XSA`, `XSN`, `XSV` | 파생 접미사 | -적, -화, -성 |

### 인덱스 설정 예시

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "korean_nori_analyzer": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": [
            "nori_pos_filter",
            "lowercase"
          ]
        }
      },
      "filter": {
        "nori_pos_filter": {
          "type": "nori_part_of_speech",
          "stoptags": ["J", "E", "IC", "MAJ", "MM", "SP", "SSC", "SSO", "SC", "SE"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "analyzer": "korean_nori_analyzer",
        "fielddata": true
      }
    }
  }
}
```

---

## 트러블슈팅

### 문제: "Nori 플러그인이 설치되어 있지 않습니다"

**해결책**: 1단계를 다시 수행하여 플러그인을 설치하고 Elasticsearch를 재시작합니다.

### 문제: 재색인 중 일부 문서 실패

**원인**: MinIO에서 파일을 찾을 수 없거나 텍스트 추출 실패

**해결책**: 로그를 확인하여 실패한 문서를 파악하고, 해당 문서를 다시 업로드합니다.

### 문제: 여전히 조사가 키워드로 추출됨

**원인**:
1. 인덱스 재생성이 제대로 되지 않았을 수 있습니다.
2. 새 문서가 아닌 기존 문서를 조회하고 있을 수 있습니다.

**해결책**:
```bash
# 인덱스 설정 확인
curl -X GET "localhost:9200/documents/_settings?pretty"

# 분석기 테스트
curl -X POST "localhost:9200/documents/_analyze?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "analyzer": "korean_nori_analyzer",
    "text": "머신러닝을 연구하는 것이 중요합니다"
  }'
```

---

## 추가 최적화

### 1. 사용자 사전 추가

특정 도메인의 전문 용어를 정확히 분석하려면 사용자 사전을 추가할 수 있습니다:

```json
{
  "settings": {
    "analysis": {
      "tokenizer": {
        "nori_user_dict": {
          "type": "nori_tokenizer",
          "user_dictionary": "user_dictionary.txt"
        }
      }
    }
  }
}
```

`user_dictionary.txt`:
```
머신러닝
딥러닝
자연어처리
```

### 2. 동의어 처리

키워드의 동의어를 처리하려면 동의어 필터를 추가합니다:

```json
{
  "settings": {
    "analysis": {
      "filter": {
        "korean_synonym": {
          "type": "synonym",
          "synonyms": [
            "머신러닝, 기계학습",
            "딥러닝, 심층학습"
          ]
        }
      }
    }
  }
}
```

---

## 참고 자료

- [Elasticsearch Nori 공식 문서](https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-nori.html)
- [Nori 품사 태그 목록](https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-nori-speech.html)
- [Elasticsearch 한국어 분석 가이드](https://esbook.kimjmin.net/06-text-analysis/6.7-stemming/6.7.2-nori)

---

## 문의

문제가 발생하면 GitHub Issues에 문의하거나 개발팀에 연락하세요.
