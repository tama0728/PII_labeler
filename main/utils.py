"""
유틸리티 함수들
"""
from .models import PIITag


def get_next_span_id(document):
    """문서의 다음 span_id 반환"""
    existing_spans = PIITag.objects.filter(document=document).exclude(
        span_id=''
    ).exclude(span_id__isnull=True)
    
    max_span_id = 0
    for tag in existing_spans:
        try:
            span_num = int(tag.span_id)
            max_span_id = max(max_span_id, span_num)
        except (ValueError, TypeError):
            continue
    
    return str(max_span_id + 1)


def get_next_entity_id(document):
    """문서의 다음 entity_id 반환"""
    existing_entities = PIITag.objects.filter(document=document).exclude(
        entity_id=''
    ).exclude(entity_id__isnull=True)
    
    max_entity_id = 0
    for tag in existing_entities:
        try:
            entity_num = int(tag.entity_id)
            max_entity_id = max(max_entity_id, entity_num)
        except (ValueError, TypeError):
            continue
    
    return str(max_entity_id + 1)


def sanitize_metadata_field(value, default=''):
    """메타데이터 필드 정리"""
    if value is None:
        return default
    return str(value)


def parse_numeric_field(value, default=0):
    """숫자 필드 파싱"""
    try:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            if value.replace('.', '').isdigit():
                return int(float(value))
        return default
    except (ValueError, TypeError):
        return default


def validate_pii_tag_data(data):
    """PII 태그 데이터 검증"""
    required_fields = ['document_id', 'pii_category', 'span_text', 'start_offset', 'end_offset']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f'{field}은(는) 필수 필드입니다.'
    
    try:
        start_offset = int(data['start_offset'])
        end_offset = int(data['end_offset'])
        
        if start_offset < 0 or end_offset < 0:
            return False, '오프셋은 음수가 될 수 없습니다.'
        
        if start_offset >= end_offset:
            return False, '시작 오프셋은 끝 오프셋보다 작아야 합니다.'
            
    except (ValueError, TypeError):
        return False, '오프셋은 정수여야 합니다.'
    
    return True, None