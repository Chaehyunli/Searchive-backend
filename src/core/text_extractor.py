# -*- coding: utf-8 -*-
"""문서 파일에서 텍스트 추출 유틸리티"""
from typing import Optional
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class TextExtractor:
    """다양한 파일 형식에서 텍스트를 추출하는 유틸리티"""

    @staticmethod
    def extract_text_from_bytes(
        file_data: bytes,
        file_type: str,
        filename: str
    ) -> Optional[str]:
        """
        파일 바이트 데이터에서 텍스트 추출

        Args:
            file_data: 파일 바이트 데이터
            file_type: 파일 MIME 타입
            filename: 파일명

        Returns:
            추출된 텍스트 또는 None
        """
        try:
            if file_type == "application/pdf":
                return TextExtractor._extract_from_pdf(file_data)
            elif file_type == "text/plain":
                return TextExtractor._extract_from_txt(file_data)
            elif file_type in [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"
            ]:
                return TextExtractor._extract_from_docx(file_data)
            elif file_type in [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel"
            ]:
                return TextExtractor._extract_from_excel(file_data)
            elif file_type in [
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "application/vnd.ms-powerpoint"
            ]:
                return TextExtractor._extract_from_pptx(file_data)
            else:
                logger.warning(f"지원하지 않는 파일 형식: {file_type}")
                return None

        except Exception as e:
            logger.error(f"텍스트 추출 실패: {e}", exc_info=True)
            return None

    @staticmethod
    def _extract_from_pdf(file_data: bytes) -> Optional[str]:
        """PDF 파일에서 텍스트 추출"""
        try:
            import pypdf
            pdf_reader = pypdf.PdfReader(BytesIO(file_data))
            text_parts = []

            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            full_text = "\n".join(text_parts)
            logger.info(f"PDF 텍스트 추출 완료: {len(full_text)} 문자")
            return full_text

        except ImportError:
            logger.error("pypdf 라이브러리가 설치되지 않았습니다. 'pip install pypdf' 실행 필요")
            return None
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {e}", exc_info=True)
            return None

    @staticmethod
    def _extract_from_txt(file_data: bytes) -> Optional[str]:
        """TXT 파일에서 텍스트 추출"""
        try:
            # UTF-8로 디코딩 시도, 실패 시 CP949(한글) 시도
            try:
                text = file_data.decode('utf-8')
            except UnicodeDecodeError:
                text = file_data.decode('cp949', errors='ignore')

            logger.info(f"TXT 텍스트 추출 완료: {len(text)} 문자")
            return text

        except Exception as e:
            logger.error(f"TXT 텍스트 추출 실패: {e}", exc_info=True)
            return None

    @staticmethod
    def _extract_from_docx(file_data: bytes) -> Optional[str]:
        """DOCX/DOC 파일에서 텍스트 추출"""
        try:
            from docx import Document
            doc = Document(BytesIO(file_data))
            text_parts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            full_text = "\n".join(text_parts)

            logger.info(f"DOCX 텍스트 추출 완료: {len(full_text)} 문자")
            return full_text

        except ImportError:
            logger.error("python-docx 라이브러리가 설치되지 않았습니다. 'pip install python-docx' 실행 필요")
            return None
        except Exception as e:
            logger.error(f"DOCX 텍스트 추출 실패: {e}", exc_info=True)
            return None

    @staticmethod
    def _extract_from_excel(file_data: bytes) -> Optional[str]:
        """Excel 파일에서 텍스트 추출"""
        try:
            import openpyxl
            workbook = openpyxl.load_workbook(BytesIO(file_data), data_only=True)
            text_parts = []

            for sheet in workbook.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_text = " ".join(str(cell) for cell in row if cell is not None)
                    if row_text.strip():
                        text_parts.append(row_text)

            full_text = "\n".join(text_parts)
            logger.info(f"Excel 텍스트 추출 완료: {len(full_text)} 문자")
            return full_text

        except ImportError:
            logger.error("openpyxl 라이브러리가 설치되지 않았습니다. 'pip install openpyxl' 실행 필요")
            return None
        except Exception as e:
            logger.error(f"Excel 텍스트 추출 실패: {e}", exc_info=True)
            return None

    @staticmethod
    def _extract_from_pptx(file_data: bytes) -> Optional[str]:
        """PowerPoint 파일에서 텍스트 추출"""
        try:
            from pptx import Presentation
            prs = Presentation(BytesIO(file_data))
            text_parts = []

            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        text_parts.append(shape.text)

            full_text = "\n".join(text_parts)
            logger.info(f"PPTX 텍스트 추출 완료: {len(full_text)} 문자")
            return full_text

        except ImportError:
            logger.error("python-pptx 라이브러리가 설치되지 않았습니다. 'pip install python-pptx' 실행 필요")
            return None
        except Exception as e:
            logger.error(f"PPTX 텍스트 추출 실패: {e}", exc_info=True)
            return None


# 전역 텍스트 추출기 인스턴스
text_extractor = TextExtractor()
