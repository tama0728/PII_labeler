"""
비즈니스 로직을 처리하는 서비스 레이어
"""
import json
from typing import List, Dict, Tuple, Optional
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Document, PIITag, PIICategory
from .utils import (
    get_next_span_id, 
    get_next_entity_id, 
    sanitize_metadata_field,
    parse_numeric_field,
    validate_pii_tag_data
)


class DocumentService:
    """문서 관련 비즈니스 로직"""
    
    @staticmethod
    def get_navigation_documents(document_pk: int) -> Tuple[Optional[Document], Optional[Document]]:
        """이전/다음 문서 찾기"""
        all_documents = Document.objects.all().order_by('id')
        document_ids = list(all_documents.values_list('id', flat=True))
        
        try:
            current_index = document_ids.index(document_pk)
            prev_document = all_documents[current_index - 1] if current_index > 0 else None
            next_document = all_documents[current_index + 1] if current_index < len(document_ids) - 1 else None
            return prev_document, next_document
        except ValueError:
            return None, None

    @staticmethod
    def process_jsonl_upload(file_content: str, user: User) -> Tuple[int, int]:
        """JSONL 파일 처리"""
        lines = file_content.strip().split('\n')
        created_count = 0
        total_tags = 0
        
        for line in lines:
            if line.strip():
                try:
                    data = json.loads(line)
                    document, tags_count = DocumentService._create_document_from_json(data, user)
                    if document:
                        created_count += 1
                        total_tags += tags_count
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue
        
        return created_count, total_tags

    @staticmethod
    @transaction.atomic
    def _create_document_from_json(data: Dict, user: User) -> Tuple[Optional[Document], int]:
        """JSON 데이터로부터 문서 생성"""
        metadata = data.get('metadata', {})
        provenance = metadata.get('provenance', {})
        
        # Document 생성
        document = Document.objects.create(
            data_id=sanitize_metadata_field(metadata.get('data_id')),
            number_of_subjects=str(metadata.get('number_of_subjects', '')),
            dialog_type=sanitize_metadata_field(provenance.get('dialog_type')),
            turn_cnt=str(provenance.get('turn_cnt', '')),
            doc_id=sanitize_metadata_field(provenance.get('doc_id')),
            text=data.get('text', ''),
            created_by=user
        )
        
        # PII 태그 생성
        entities = data.get('entities', [])
        tags_count = 0
        
        for entity in entities:
            if DocumentService._create_pii_tag_from_entity(document, entity, user):
                tags_count += 1
        
        return document, tags_count

    @staticmethod
    def _create_pii_tag_from_entity(document: Document, entity: Dict, user: User) -> bool:
        """Entity 데이터로부터 PII 태그 생성"""
        try:
            pii_category = PIICategory.objects.filter(
                value=entity.get('entity_type')
            ).first()
            
            if not pii_category:
                return False
            
            # 기본값 처리
            span_id = entity.get('span_id', '') or get_next_span_id(document)
            entity_id = entity.get('entity_id', '') or get_next_entity_id(document)
            annotator = entity.get('annotator', '') or "Anonymous"
            identifier_type = entity.get('identifier_type', '') or 'default'

            PIITag.objects.create(
                document=document,
                pii_category=pii_category,
                span_text=entity.get('span_text', ''),
                start_offset=entity.get('start_offset', 0),
                end_offset=entity.get('end_offset', 0),
                span_id=span_id,
                entity_id=entity_id,
                annotator=annotator,
                identifier_type=identifier_type,
                confidence=1.0,
                created_by=user
            )
            return True
        except Exception:
            return False

    @staticmethod
    def generate_jsonl_data(documents: List[Document]) -> str:
        """문서들을 JSONL 형식으로 변환"""
        jsonl_lines = []
        
        for document in documents:
            pii_tags = document.pii_tags.all()
            
            # entities 배열 생성
            entities = []
            for tag in pii_tags:
                entity = {
                    "span_text": tag.span_text,
                    "entity_type": tag.pii_category.value,
                    "start_offset": tag.start_offset,
                    "end_offset": tag.end_offset,
                    "span_id": tag.span_id,
                    "entity_id": tag.entity_id,
                    "annotator": tag.annotator,
                    "identifier_type": tag.identifier_type
                }
                entities.append(entity)
            
            # JSON 객체 생성
            json_obj = {
                "metadata": {
                    "data_id": document.data_id,
                    "number_of_subjects": parse_numeric_field(document.number_of_subjects),
                    "provenance": {
                        "dialog_type": document.dialog_type,
                        "turn_cnt": parse_numeric_field(document.turn_cnt),
                        "doc_id": document.doc_id
                    }
                },
                "text": document.text,
                "entities": entities
            }
            
            jsonl_lines.append(json.dumps(json_obj, ensure_ascii=False))
        
        return '\n'.join(jsonl_lines)


class PIITagService:
    """PII 태그 관련 비즈니스 로직"""
    
    @staticmethod
    def create_pii_tag(data: Dict, user: User) -> Tuple[bool, Optional[PIITag], str]:
        """PII 태그 생성"""
        # 데이터 검증
        is_valid, error_message = validate_pii_tag_data(data)
        if not is_valid:
            return False, None, error_message
        
        try:
            document = get_object_or_404(Document, pk=data['document_id'])
            pii_category = get_object_or_404(PIICategory, value=data['pii_category'])
            
            # 중복 태그 검사
            existing_tag = PIITag.objects.filter(
                document=document,
                start_offset=data['start_offset'],
                end_offset=data['end_offset'],
                pii_category=pii_category
            ).first()
            
            if existing_tag:
                return False, None, '해당 위치에 이미 같은 태그가 존재합니다.'
            
            # 기본값 처리
            span_id = data.get('span_id', '') or get_next_span_id(document)
            entity_id = data.get('entity_id', '') or get_next_entity_id(document)
            annotator = data.get('annotator', '') or "Anonymous"
            identifier_type = data.get('identifier_type', '') or 'default'
            confidence = data.get('confidence', 0.0)

            # PII 태그 생성
            pii_tag = PIITag.objects.create(
                document=document,
                pii_category=pii_category,
                span_text=data['span_text'],
                start_offset=int(data['start_offset']),
                end_offset=int(data['end_offset']),
                span_id=span_id,
                entity_id=entity_id,
                annotator=annotator,
                identifier_type=identifier_type,
                confidence=confidence,
                created_by=user
            )
            
            return True, pii_tag, 'PII 태그가 추가되었습니다.'
            
        except Exception as e:
            return False, None, f'오류가 발생했습니다: {str(e)}'

    @staticmethod
    def update_pii_tag(tag_id: int, data: Dict, user: User) -> Tuple[bool, Optional[PIITag], str]:
        """PII 태그 업데이트"""
        try:
            pii_tag = get_object_or_404(PIITag, id=tag_id)
            
            # 권한 확인
            if pii_tag.created_by != user and not user.is_staff:
                return False, None, '수정 권한이 없습니다.'
            
            # PII 카테고리 업데이트
            if 'pii_category_value' in data:
                pii_category = get_object_or_404(PIICategory, value=data['pii_category_value'])
                pii_tag.pii_category = pii_category
            
            # 기타 필드 업데이트
            if 'identifier_type' in data:
                pii_tag.identifier_type = data['identifier_type'] or 'default'
            
            if 'entity_id' in data and data['entity_id']:
                pii_tag.entity_id = data['entity_id']
            
            # 어노테이터 업데이트
            pii_tag.annotator = user.username
            pii_tag.save()
            
            return True, pii_tag, 'PII 태그가 업데이트되었습니다.'
            
        except Exception as e:
            return False, None, f'오류가 발생했습니다: {str(e)}'

    @staticmethod
    def delete_pii_tag(tag_id: int, user: User) -> Tuple[bool, str]:
        """PII 태그 삭제"""
        try:
            pii_tag = get_object_or_404(PIITag, id=tag_id)
            
            # 권한 확인
            if pii_tag.created_by != user and not user.is_staff:
                return False, '삭제 권한이 없습니다.'
            
            pii_tag.delete()
            return True, 'PII 태그가 삭제되었습니다.'
            
        except Exception as e:
            return False, f'오류가 발생했습니다: {str(e)}'

    @staticmethod
    def delete_document(document_id: int, user: User) -> Tuple[bool, str]:
        """문서 삭제"""
        try:
            document = get_object_or_404(Document, id=document_id)
            
            # 권한 확인
            if document.created_by != user and not user.is_staff:
                return False, '삭제 권한이 없습니다.'
            
            # 관련 PII 태그들도 함께 삭제 (CASCADE로 자동 삭제되지만 명시적 처리)
            document.pii_tags.all().delete()
            document.delete()
            
            return True, '문서가 삭제되었습니다.'
            
        except Exception as e:
            return False, f'오류가 발생했습니다: {str(e)}'

    @staticmethod
    @transaction.atomic
    def bulk_delete_documents(document_ids: List[int], user: User) -> Tuple[int, str]:
        """여러 문서 일괄 삭제"""
        deleted_count = 0
        
        for document_id in document_ids:
            try:
                document = get_object_or_404(Document, pk=document_id)
                
                # 권한 확인
                if document.created_by == user or user.is_staff:
                    document.pii_tags.all().delete()
                    document.delete()
                    deleted_count += 1
            except Exception:
                continue
        
        return deleted_count, f'{deleted_count}개 문서가 삭제되었습니다.'