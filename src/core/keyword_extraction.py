# -*- coding: utf-8 -*-
"""키워드 추출 서비스 (Hybrid: KeyBERT + Elasticsearch Significant Text)"""
from typing import List, Tuple
from abc import ABC, abstractmethod
from src.core.config import settings
from src.core.elasticsearch_client import elasticsearch_client
import logging

logger = logging.getLogger(__name__)


class KeywordExtractor(ABC):
    """키워드 추출 인터페이스 (Strategy Pattern)"""

    @abstractmethod
    async def extract_keywords(self, text: str, document_id: int = None) -> List[str]:
        """
        텍스트에서 키워드 추출

        Args:
            text: 대상 텍스트
            document_id: 문서 ID (Elasticsearch 사용 시 필요)

        Returns:
            추출된 키워드 리스트
        """
        pass

    @abstractmethod
    def get_method_name(self) -> str:
        """추출 방법 이름 반환"""
        pass


class KeyBERTExtractor(KeywordExtractor):
    """KeyBERT 기반 키워드 추출기 (Cold Start용)"""

    def __init__(self):
        """KeyBERTExtractor 초기화"""
        self.model = None

    def _load_model(self):
        """KeyBERT 모델 로드 (Lazy Loading)"""
        if self.model is None:
            try:
                from keybert import KeyBERT
                self.model = KeyBERT()
                logger.info("KeyBERT 모델 로드 성공")
            except ImportError:
                logger.error("KeyBERT 라이브러리가 설치되지 않았습니다. 'pip install keybert' 실행 필요")
                raise ImportError("keybert 라이브러리가 필요합니다.")

    async def extract_keywords(self, text: str, document_id: int = None) -> List[str]:
        """
        KeyBERT를 사용하여 키워드 추출

        Args:
            text: 대상 텍스트
            document_id: 사용하지 않음 (인터페이스 일관성 유지)

        Returns:
            추출된 키워드 리스트
        """
        self._load_model()

        try:
            # KeyBERT로 키워드 추출 (상위 N개)
            keyword_count = settings.KEYWORD_EXTRACTION_COUNT
            keywords_with_scores = self.model.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 2),  # 1~2 단어 구문
                stop_words='english',  # 영어 불용어 제거
                top_n=keyword_count,
                use_maxsum=True,  # 다양성 증가
                nr_candidates=20  # 후보 키워드 수
            )

            # (키워드, 점수) 튜플에서 키워드만 추출
            keywords = [kw[0] for kw in keywords_with_scores]

            logger.info(f"KeyBERT 키워드 추출 완료: {keywords}")
            return keywords

        except Exception as e:
            logger.error(f"KeyBERT 키워드 추출 실패: {e}", exc_info=True)
            return []

    def get_method_name(self) -> str:
        return "keybert"


class ElasticsearchExtractor(KeywordExtractor):
    """Elasticsearch Significant Text 기반 키워드 추출기 (Normal용)"""

    async def extract_keywords(self, text: str, document_id: int = None) -> List[str]:
        """
        Elasticsearch Significant Text Aggregation을 사용하여 키워드 추출

        Args:
            text: 사용하지 않음 (Elasticsearch에서 직접 조회)
            document_id: 문서 ID (필수)

        Returns:
            추출된 키워드 리스트
        """
        if document_id is None:
            logger.error("ElasticsearchExtractor는 document_id가 필요합니다.")
            return []

        try:
            keyword_count = settings.KEYWORD_EXTRACTION_COUNT
            keywords = await elasticsearch_client.extract_significant_terms(
                document_id=document_id,
                size=keyword_count
            )

            logger.info(f"Elasticsearch Significant Text 추출 완료: {keywords}")
            return keywords

        except Exception as e:
            logger.error(f"Elasticsearch 키워드 추출 실패: {e}", exc_info=True)
            return []

    def get_method_name(self) -> str:
        return "elasticsearch"


class HybridKeywordExtractionService:
    """
    하이브리드 키워드 추출 서비스 (Orchestrator)

    - Cold Start (문서 < 임계값): KeyBERT 사용
    - Normal (문서 >= 임계값): Elasticsearch Significant Text 사용
    """

    def __init__(self):
        """HybridKeywordExtractionService 초기화"""
        self.keybert_extractor = KeyBERTExtractor()
        self.elasticsearch_extractor = ElasticsearchExtractor()
        self.threshold = settings.KEYWORD_EXTRACTION_THRESHOLD

    async def extract_keywords(
        self,
        text: str,
        document_id: int = None
    ) -> Tuple[List[str], str]:
        """
        하이브리드 방식으로 키워드 추출

        Args:
            text: 대상 텍스트
            document_id: 문서 ID (Elasticsearch 사용 시 필요)

        Returns:
            (추출된 키워드 리스트, 사용된 추출 방법)
        """
        # 1. Elasticsearch의 전체 문서 수 확인
        document_count = await elasticsearch_client.get_document_count()

        logger.info(f"현재 Elasticsearch 문서 수: {document_count}, 임계값: {self.threshold}")

        # 2. 임계값 기반 추출 전략 선택
        if document_count < self.threshold:
            # Cold Start: KeyBERT 사용
            logger.info(f"Cold Start 모드: KeyBERT 사용 (문서 수: {document_count} < {self.threshold})")
            keywords = await self.keybert_extractor.extract_keywords(text)
            method = self.keybert_extractor.get_method_name()
        else:
            # Normal: Elasticsearch Significant Text 사용
            logger.info(f"Normal 모드: Elasticsearch 사용 (문서 수: {document_count} >= {self.threshold})")
            keywords = await self.elasticsearch_extractor.extract_keywords(text, document_id)
            method = self.elasticsearch_extractor.get_method_name()

        # 3. 키워드 정규화 (소문자 변환, 중복 제거)
        keywords = list(set(kw.strip().lower() for kw in keywords if kw.strip()))

        logger.info(f"최종 키워드: {keywords}, 추출 방법: {method}")
        return keywords, method


# 전역 키워드 추출 서비스 인스턴스
keyword_extraction_service = HybridKeywordExtractionService()
