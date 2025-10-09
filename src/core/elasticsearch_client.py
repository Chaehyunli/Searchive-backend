# -*- coding: utf-8 -*-
"""Elasticsearch 클라이언트 유틸리티"""
from typing import Optional, Dict, Any, List
from elasticsearch import AsyncElasticsearch
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Elasticsearch 클라이언트 래퍼"""

    def __init__(self):
        """ElasticsearchClient 초기화"""
        self.client: Optional[AsyncElasticsearch] = None
        self.index_name = "documents"

    async def connect(self):
        """Elasticsearch 연결"""
        if self.client is None:
            self.client = AsyncElasticsearch(
                hosts=[settings.ELASTICSEARCH_URL],
                basic_auth=(settings.ELASTICSEARCH_USER, settings.ELASTICSEARCH_PASSWORD),
                verify_certs=False
            )
            logger.info(f"Elasticsearch 연결 성공: {settings.ELASTICSEARCH_URL}")

            # 인덱스가 없으면 생성
            await self.create_index_if_not_exists()

    async def close(self):
        """Elasticsearch 연결 종료"""
        if self.client:
            await self.client.close()
            logger.info("Elasticsearch 연결 종료")

    async def create_index_if_not_exists(self):
        """인덱스가 없으면 생성"""
        if not self.client:
            await self.connect()

        exists = await self.client.indices.exists(index=self.index_name)

        if not exists:
            # 한국어 분석을 위한 인덱스 설정
            index_settings = {
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
                            "fielddata": True  # Significant Text Aggregation을 위해 필요
                        },
                        "filename": {"type": "keyword"},
                        "file_type": {"type": "keyword"},
                        "uploaded_at": {"type": "date"}
                    }
                }
            }

            await self.client.indices.create(
                index=self.index_name,
                body=index_settings
            )
            logger.info(f"Elasticsearch 인덱스 생성: {self.index_name}")

    async def index_document(
        self,
        document_id: int,
        user_id: int,
        content: str,
        filename: str,
        file_type: str
    ) -> bool:
        """
        문서를 Elasticsearch에 색인

        Args:
            document_id: 문서 ID
            user_id: 사용자 ID
            content: 문서 텍스트 내용
            filename: 파일명
            file_type: 파일 타입

        Returns:
            색인 성공 여부
        """
        if not self.client:
            await self.connect()

        try:
            doc_body = {
                "document_id": document_id,
                "user_id": user_id,
                "content": content,
                "filename": filename,
                "file_type": file_type,
                "uploaded_at": None  # 필요시 추가
            }

            await self.client.index(
                index=self.index_name,
                id=str(document_id),
                document=doc_body
            )
            logger.info(f"문서 색인 성공: document_id={document_id}")
            return True

        except Exception as e:
            logger.error(f"문서 색인 실패: {e}", exc_info=True)
            return False

    async def get_document_count(self) -> int:
        """
        Elasticsearch에 색인된 전체 문서 수 조회

        Returns:
            전체 문서 수
        """
        if not self.client:
            await self.connect()

        try:
            result = await self.client.count(index=self.index_name)
            count = result["count"]
            logger.info(f"Elasticsearch 전체 문서 수: {count}")
            return count

        except Exception as e:
            logger.error(f"문서 수 조회 실패: {e}", exc_info=True)
            return 0

    async def extract_significant_terms(
        self,
        document_id: int,
        size: int = 3
    ) -> List[str]:
        """
        More Like This Query를 사용하여 문서의 핵심 키워드 추출

        Args:
            document_id: 대상 문서 ID
            size: 추출할 키워드 개수

        Returns:
            추출된 키워드 리스트
        """
        if not self.client:
            await self.connect()

        try:
            # 1. 대상 문서 조회
            doc_response = await self.client.get(index=self.index_name, id=str(document_id))
            doc_content = doc_response["_source"]["content"]

            # 2. 텍스트가 너무 길면 앞부분만 사용 (성능 최적화)
            max_length = 5000  # 최대 5000 글자까지만 사용
            if len(doc_content) > max_length:
                doc_content = doc_content[:max_length]

            # 3. Term Vectors API 사용하여 TF-IDF 기반 키워드 추출
            tv_response = await self.client.termvectors(
                index=self.index_name,
                id=str(document_id),
                fields=["content"],
                term_statistics=True,
                field_statistics=True
            )

            # 4. 결과 파싱: TF-IDF 점수가 높은 상위 N개 추출
            if "term_vectors" not in tv_response or "content" not in tv_response["term_vectors"]:
                logger.warning(f"문서 {document_id}에서 term vectors를 찾을 수 없습니다.")
                return []

            terms = tv_response["term_vectors"]["content"]["terms"]

            # TF-IDF 계산 및 정렬
            term_scores = []
            for term, term_info in terms.items():
                # TF (Term Frequency)
                tf = term_info.get("term_freq", 1)
                # DF (Document Frequency)
                df = term_info.get("doc_freq", 1)
                # IDF 계산
                total_docs = tv_response["term_vectors"]["content"]["field_statistics"]["doc_count"]
                import math
                idf = math.log((total_docs + 1) / (df + 1)) + 1
                # TF-IDF 점수
                tfidf = tf * idf

                # 단어 길이 필터 (너무 짧거나 긴 단어 제외)
                if 2 <= len(term) <= 30:
                    term_scores.append((term, tfidf))

            # 점수 기준 정렬 후 상위 N개 추출
            term_scores.sort(key=lambda x: x[1], reverse=True)
            keywords = [term for term, score in term_scores[:size]]

            logger.info(f"TF-IDF 키워드 추출 완료: document_id={document_id}, keywords={keywords}")
            return keywords

        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}", exc_info=True)
            return []

    async def delete_document(self, document_id: int) -> bool:
        """
        Elasticsearch에서 문서 삭제

        Args:
            document_id: 문서 ID

        Returns:
            삭제 성공 여부
        """
        if not self.client:
            await self.connect()

        try:
            await self.client.delete(
                index=self.index_name,
                id=str(document_id)
            )
            logger.info(f"Elasticsearch 문서 삭제 성공: document_id={document_id}")
            return True

        except Exception as e:
            logger.error(f"Elasticsearch 문서 삭제 실패: {e}", exc_info=True)
            return False


# 전역 Elasticsearch 클라이언트 인스턴스
elasticsearch_client = ElasticsearchClient()
