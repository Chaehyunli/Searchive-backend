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

    async def check_nori_plugin(self) -> bool:
        """Nori 플러그인 설치 여부 확인"""
        if not self.client:
            await self.connect()

        try:
            # 노드 정보를 통해 설치된 플러그인 확인
            nodes_info = await self.client.nodes.info()
            for node_id, node_info in nodes_info["nodes"].items():
                plugins = node_info.get("plugins", [])
                for plugin in plugins:
                    if plugin.get("name") == "analysis-nori":
                        logger.info("Nori 플러그인이 설치되어 있습니다.")
                        return True

            logger.warning("Nori 플러그인이 설치되어 있지 않습니다. 기본 분석기를 사용합니다.")
            return False

        except Exception as e:
            logger.error(f"플러그인 확인 중 오류: {e}")
            return False

    async def create_index_if_not_exists(self):
        """인덱스가 없으면 생성"""
        if not self.client:
            await self.connect()

        exists = await self.client.indices.exists(index=self.index_name)

        if not exists:
            # Nori 플러그인 설치 여부 확인
            has_nori = await self.check_nori_plugin()

            # 한국어 분석을 위한 인덱스 설정
            if has_nori:
                # Nori 분석기 사용 (조사, 어미 필터링)
                index_settings = {
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
                                    "stoptags": [
                                        # 조사 (모든 유형)
                                        "J",      # 조사 전체
                                        "JKS",    # 주격 조사 (이, 가)
                                        "JKC",    # 보격 조사 (이)
                                        "JKG",    # 관형격 조사 (의)
                                        "JKO",    # 목적격 조사 (을, 를)
                                        "JKB",    # 부사격 조사 (에, 에서, 로)
                                        "JKV",    # 호격 조사 (아, 야)
                                        "JKQ",    # 인용격 조사 (고, 라고)
                                        "JX",     # 보조사 (은, 는, 도, 만, 까지)
                                        "JC",     # 접속 조사 (와, 과, 하고)

                                        # 어미 (모든 유형)
                                        "E",      # 어미 전체
                                        "EP",     # 선어말 어미
                                        "EF",     # 종결 어미 (다, 요)
                                        "EC",     # 연결 어미 (고, 어서, 며, 면서, 데)
                                        "ETN",    # 명사형 전성 어미 (음, 기)
                                        "ETM",    # 관형형 전성 어미 (는, 은, ㄴ, ㄹ)

                                        # 접사
                                        "XPN",    # 접두사
                                        "XSA",    # 형용사 파생 접미사 (적, 스럽)
                                        "XSN",    # 명사 파생 접미사 (성, 화)
                                        "XSV",    # 동사 파생 접미사
                                        "XR",     # 어근

                                        # 부호 및 기호
                                        "SF",     # 마침표, 물음표, 느낌표
                                        "SP",     # 쉼표, 가운뎃점, 콜론, 빗금
                                        "SSC",    # 닫는 괄호
                                        "SSO",    # 여는 괄호
                                        "SC",     # 구분자 (·, /, :)
                                        "SE",     # 줄임표 (…)
                                        "SO",     # 외국어 기호
                                        "SW",     # 기타 기호

                                        # 기타 불필요한 품사
                                        "IC",     # 감탄사 (아, 아이고)
                                        "MAJ",    # 접속 부사 (그리고, 그러나)
                                        "MAG",    # 일반 부사
                                        "MM",     # 관형사 (이, 그, 저, 모든)
                                        "VCP",    # 긍정 지정사 (이다)
                                        "VCN",    # 부정 지정사 (아니다)
                                        "VX",     # 보조 용언
                                        "UNA",    # 알 수 없는 품사
                                        "NA",     # 미지정
                                        "VSV"     # 통계 기반 미등록어
                                    ]
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
                                "analyzer": "korean_nori_analyzer",
                                "fielddata": True  # TF-IDF 기반 키워드 추출을 위해 필요
                            },
                            "filename": {"type": "keyword"},
                            "file_type": {"type": "keyword"},
                            "uploaded_at": {"type": "date"}
                        }
                    }
                }
                logger.info("Nori 분석기를 사용한 인덱스 설정을 적용합니다.")
            else:
                # 기본 분석기 사용 (Nori 미설치 시)
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
                                "fielddata": True
                            },
                            "filename": {"type": "keyword"},
                            "file_type": {"type": "keyword"},
                            "uploaded_at": {"type": "date"}
                        }
                    }
                }
                logger.warning("기본 분석기를 사용한 인덱스 설정을 적용합니다.")

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
        file_type: str,
        uploaded_at: Optional[str] = None
    ) -> bool:
        """
        문서를 Elasticsearch에 색인

        Args:
            document_id: 문서 ID
            user_id: 사용자 ID
            content: 문서 텍스트 내용
            filename: 파일명
            file_type: 파일 타입
            uploaded_at: 업로드 일시 (ISO format string)

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
                "uploaded_at": uploaded_at
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

    async def recreate_index_with_nori(self) -> bool:
        """
        기존 인덱스를 삭제하고 Nori 분석기로 재생성

        Warning: 기존 데이터가 모두 삭제됩니다!

        Returns:
            성공 여부
        """
        if not self.client:
            await self.connect()

        try:
            # Nori 플러그인 확인
            has_nori = await self.check_nori_plugin()
            if not has_nori:
                logger.error("Nori 플러그인이 설치되어 있지 않습니다. 인덱스를 재생성할 수 없습니다.")
                return False

            # 기존 인덱스 존재 확인
            exists = await self.client.indices.exists(index=self.index_name)

            if exists:
                # 기존 인덱스 삭제
                await self.client.indices.delete(index=self.index_name)
                logger.info(f"기존 인덱스 삭제 완료: {self.index_name}")

            # 새 인덱스 생성 (Nori 분석기 적용)
            await self.create_index_if_not_exists()
            logger.info(f"Nori 분석기가 적용된 새 인덱스 생성 완료: {self.index_name}")

            return True

        except Exception as e:
            logger.error(f"인덱스 재생성 실패: {e}", exc_info=True)
            return False

    async def reindex_all_documents(self, documents_data: List[Dict[str, Any]]) -> bool:
        """
        모든 문서를 재색인

        Args:
            documents_data: 재색인할 문서 데이터 리스트
                [{
                    "document_id": int,
                    "user_id": int,
                    "content": str,
                    "filename": str,
                    "file_type": str,
                    "uploaded_at": str
                }, ...]

        Returns:
            성공 여부
        """
        if not self.client:
            await self.connect()

        try:
            success_count = 0
            failed_count = 0

            for doc in documents_data:
                try:
                    success = await self.index_document(
                        document_id=doc["document_id"],
                        user_id=doc["user_id"],
                        content=doc["content"],
                        filename=doc["filename"],
                        file_type=doc["file_type"],
                        uploaded_at=doc.get("uploaded_at")
                    )

                    if success:
                        success_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"문서 재색인 실패: document_id={doc.get('document_id')}, error={e}")
                    failed_count += 1

            logger.info(f"재색인 완료: 성공={success_count}, 실패={failed_count}")
            return failed_count == 0

        except Exception as e:
            logger.error(f"재색인 실패: {e}", exc_info=True)
            return False


# 전역 Elasticsearch 클라이언트 인스턴스
elasticsearch_client = ElasticsearchClient()
