# -*- coding: utf-8 -*-
"""Test script for Elasticsearch keyword extraction"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.elasticsearch_client import elasticsearch_client


async def test_keyword_extraction():
    """Test the new Term Vectors-based keyword extraction"""
    try:
        # Connect to Elasticsearch
        await elasticsearch_client.connect()
        print("✓ Connected to Elasticsearch")

        # Get document count
        count = await elasticsearch_client.get_document_count()
        print(f"✓ Total documents in index: {count}")

        if count == 0:
            print("✗ No documents in index to test with")
            return

        # Test with document ID 11 (or adjust based on your data)
        test_doc_id = 11
        print(f"\n--- Testing keyword extraction for document_id={test_doc_id} ---")

        keywords = await elasticsearch_client.extract_significant_terms(
            document_id=test_doc_id,
            size=3
        )

        if keywords:
            print(f"✓ Keywords extracted successfully:")
            for i, keyword in enumerate(keywords, 1):
                print(f"  {i}. {keyword}")
        else:
            print("✗ No keywords extracted")

        # Close connection
        await elasticsearch_client.close()
        print("\n✓ Test completed")

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_keyword_extraction())
