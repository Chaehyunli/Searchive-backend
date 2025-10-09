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
        Significant Text Aggregation을 사용하여 문서의 핵심 키워드 추출

        Args:
            document_id: 대상 문서 ID
            size: 추출할 키워드 개수

        Returns:
            추출된 키워드 리스트
        """
        if not self.client:
            await self.connect()

        try:
            # 1. 대상 문서의 내용 조회
            doc = await self.client.get(index=self.index_name, id=str(document_id))
            doc_content = doc["_source"]["content"]

            # 2. Significant Text Aggregation 실행
            # "배경(background)"은 전체 문서, "대상(foreground)"은 현재 문서
            query = {
                "size": 0,
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"content": doc_content}}
                        ]
                    }
                },
                "aggs": {
                    "significant_keywords": {
                        "significant_text": {
                            "field": "content",
                            "size": size * 2,  # 여유있게 추출
                            "min_doc_count": 1
                        }
                    }
                }
            }

            response = await self.client.search(
                index=self.index_name,
                body=query
            )

            # 3. 결과 파싱
            buckets = response["aggregations"]["significant_keywords"]["buckets"]
            keywords = [bucket["key"] for bucket in buckets[:size]]

            logger.info(f"Significant Text 추출 완료: document_id={document_id}, keywords={keywords}")
            return keywords

        except Exception as e:
            logger.error(f"Significant Text 추출 실패: {e}", exc_info=True)
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
