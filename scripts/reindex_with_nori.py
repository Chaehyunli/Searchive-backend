# -*- coding: utf-8 -*-
"""
Elasticsearch 인덱스를 Nori 분석기로 재생성하고 데이터를 재색인하는 스크립트

사용법:
    python scripts/reindex_with_nori.py

주의: 이 스크립트는 기존 Elasticsearch 인덱스를 삭제하고 재생성합니다!
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 경로를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.core.elasticsearch_client import elasticsearch_client
from src.core.text_extractor import text_extractor
from src.core.minio_client import minio_client
from src.domains.documents.models import Document


async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("Elasticsearch 인덱스 Nori 분석기 재설정 스크립트")
    print("=" * 60)
    print()

    # 1. Elasticsearch 연결
    print("[1/5] Elasticsearch 연결 중...")
    await elasticsearch_client.connect()

    # 2. Nori 플러그인 확인
    print("[2/5] Nori 플러그인 확인 중...")
    has_nori = await elasticsearch_client.check_nori_plugin()

    if not has_nori:
        print("❌ Nori 플러그인이 설치되어 있지 않습니다!")
        print()
        print("Nori 플러그인을 설치하려면 Elasticsearch 서버에서 다음 명령을 실행하세요:")
        print("  cd /usr/share/elasticsearch")
        print("  bin/elasticsearch-plugin install analysis-nori")
        print("  sudo systemctl restart elasticsearch")
        print()
        await elasticsearch_client.close()
        return

    print("✅ Nori 플러그인이 설치되어 있습니다.")

    # 3. 기존 데이터 로드
    print("[3/5] PostgreSQL에서 기존 문서 데이터 로드 중...")

    # AsyncEngine 생성
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    documents_data = []

    async with async_session() as session:
        # 모든 문서 조회
        result = await session.execute(select(Document))
        documents = result.scalars().all()

        print(f"📄 총 {len(documents)}개의 문서를 발견했습니다.")

        if len(documents) == 0:
            print("⚠️  재색인할 문서가 없습니다. 인덱스만 재생성합니다.")
        else:
            print("📥 문서 내용을 MinIO에서 다운로드 중...")

            for idx, doc in enumerate(documents, 1):
                try:
                    # MinIO에서 파일 다운로드
                    file_data = minio_client.download_file(doc.storage_path)

                    # 텍스트 추출
                    content = text_extractor.extract_text_from_bytes(
                        file_data=file_data,
                        file_type=doc.file_type,
                        filename=doc.original_filename
                    )

                    if content and len(content.strip()) >= 10:
                        documents_data.append({
                            "document_id": doc.document_id,
                            "user_id": doc.user_id,
                            "content": content,
                            "filename": doc.original_filename,
                            "file_type": doc.file_type,
                            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
                        })
                        print(f"  ✓ [{idx}/{len(documents)}] {doc.original_filename}")
                    else:
                        print(f"  ⚠️  [{idx}/{len(documents)}] {doc.original_filename} - 텍스트 추출 실패 또는 너무 짧음")

                except Exception as e:
                    print(f"  ❌ [{idx}/{len(documents)}] {doc.original_filename} - 오류: {e}")

            print(f"✅ {len(documents_data)}개 문서의 텍스트 추출 완료")

    await engine.dispose()

    # 4. 인덱스 재생성
    print()
    print("[4/5] Elasticsearch 인덱스 재생성 중...")
    print("⚠️  주의: 기존 인덱스가 삭제됩니다!")

    # 사용자 확인
    response = input("계속하시겠습니까? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ 작업이 취소되었습니다.")
        await elasticsearch_client.close()
        return

    success = await elasticsearch_client.recreate_index_with_nori()

    if not success:
        print("❌ 인덱스 재생성 실패!")
        await elasticsearch_client.close()
        return

    print("✅ Nori 분석기가 적용된 인덱스 생성 완료")

    # 5. 데이터 재색인
    if len(documents_data) > 0:
        print()
        print(f"[5/5] {len(documents_data)}개 문서 재색인 중...")

        success = await elasticsearch_client.reindex_all_documents(documents_data)

        if success:
            print("✅ 모든 문서 재색인 완료!")
        else:
            print("⚠️  일부 문서 재색인 실패. 로그를 확인하세요.")
    else:
        print()
        print("[5/5] 재색인할 문서가 없습니다.")

    # 종료
    await elasticsearch_client.close()

    print()
    print("=" * 60)
    print("작업 완료!")
    print("=" * 60)
    print()
    print("이제 Nori 분석기가 적용되었습니다.")
    print("새로 업로드되는 문서부터 '을', '것이' 같은 조사가 키워드에서 제외됩니다.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
