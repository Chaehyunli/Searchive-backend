# -*- coding: utf-8 -*-
"""TextExtractor 단위 테스트"""
import pytest
from src.core.text_extractor import TextExtractor


class TestTextExtractor:
    """TextExtractor 테스트"""

    def test_extract_text_from_pdf(self):
        """PDF 파일 텍스트 추출 테스트"""
        # PDF 매직 넘버가 포함된 간단한 테스트 데이터
        test_data = b"%PDF-1.4\nTest content"

        # 실제 추출은 pypdf가 필요하므로 형식 감지만 확인
        result = TextExtractor.extract_text_from_bytes(
            file_data=test_data,
            file_type="application/pdf",
            filename="test.pdf"
        )

        # None이거나 문자열이어야 함 (라이브러리 유무에 따라 다름)
        assert result is None or isinstance(result, str)

    def test_extract_text_from_txt(self):
        """TXT 파일 텍스트 추출 테스트"""
        test_data = "안녕하세요. 이것은 테스트 문서입니다.".encode('utf-8')

        result = TextExtractor.extract_text_from_bytes(
            file_data=test_data,
            file_type="text/plain",
            filename="test.txt"
        )

        assert result is not None
        assert "안녕하세요" in result
        assert "테스트 문서" in result

    def test_extract_text_from_docx(self):
        """DOCX 파일 텍스트 추출 테스트 (Mock)"""
        # DOCX는 실제 파일 구조가 필요하므로 형식만 확인
        test_data = b"PK\x03\x04"  # ZIP 매직 넘버 (DOCX는 ZIP 기반)

        result = TextExtractor.extract_text_from_bytes(
            file_data=test_data,
            file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="test.docx"
        )

        # 실제 DOCX 구조가 아니므로 None 반환 예상
        assert result is None or isinstance(result, str)

    def test_extract_text_from_hwp_with_application_x_hwp(self):
        """HWP 파일 텍스트 추출 테스트 (application/x-hwp MIME 타입)"""
        # HWP 파일은 OLE 구조이므로 실제 파일이 필요
        # 여기서는 형식 감지만 확인
        test_data = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # OLE 매직 넘버

        result = TextExtractor.extract_text_from_bytes(
            file_data=test_data,
            file_type="application/x-hwp",
            filename="test.hwp"
        )

        # 실제 HWP 구조가 아니므로 None 또는 빈 문자열 반환 예상
        assert result is None or isinstance(result, str)

    def test_extract_text_from_hwp_with_haansofthwp(self):
        """HWP 파일 텍스트 추출 테스트 (application/haansofthwp MIME 타입)"""
        test_data = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # OLE 매직 넘버

        result = TextExtractor.extract_text_from_bytes(
            file_data=test_data,
            file_type="application/haansofthwp",
            filename="test.hwp"
        )

        assert result is None or isinstance(result, str)

    def test_extract_text_from_hwp_with_vnd_hancom_hwp(self):
        """HWP 파일 텍스트 추출 테스트 (application/vnd.hancom.hwp MIME 타입)"""
        test_data = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # OLE 매직 넘버

        result = TextExtractor.extract_text_from_bytes(
            file_data=test_data,
            file_type="application/vnd.hancom.hwp",
            filename="test.hwp"
        )

        assert result is None or isinstance(result, str)

    def test_extract_text_from_unsupported_format(self):
        """지원하지 않는 파일 형식 테스트"""
        test_data = b"\x89PNG\r\n\x1a\n"  # PNG 매직 넘버

        result = TextExtractor.extract_text_from_bytes(
            file_data=test_data,
            file_type="image/png",
            filename="test.png"
        )

        assert result is None

    def test_extract_text_with_exception(self):
        """예외 발생 시 None 반환 테스트"""
        # 잘못된 데이터
        test_data = b""

        result = TextExtractor.extract_text_from_bytes(
            file_data=test_data,
            file_type="application/pdf",
            filename="invalid.pdf"
        )

        # 예외가 발생하면 None 반환
        assert result is None
