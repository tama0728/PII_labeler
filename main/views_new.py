"""
메인 뷰 모듈 - 기존 뷰들을 새로운 구조로 리팩토링
"""

# 웹 페이지 뷰들
from .web_views import (
    index,
    document_list,
    document_detail,
    document_create,
    register,
    download_jsonl
)

# API 뷰들
from .api_views import (
    add_pii_tag,
    delete_pii_tag,
    update_pii_tag,
    delete_document,
    bulk_delete_documents
)

# 기존 import 구문들을 호환성을 위해 유지
__all__ = [
    # 웹 뷰들
    'index',
    'document_list', 
    'document_detail',
    'document_create',
    'register',
    'download_jsonl',
    
    # API 뷰들
    'add_pii_tag',
    'delete_pii_tag', 
    'update_pii_tag',
    'delete_document',
    'bulk_delete_documents'
]