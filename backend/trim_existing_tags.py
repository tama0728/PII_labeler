#!/usr/bin/env python
"""
기존 PII 태그들의 공백을 트림하고 offset을 조정하는 스크립트
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pii_labeler.settings')
django.setup()

from main.models import PIITag

def trim_existing_tags():
    """기존 태그들의 공백을 트림하고 offset을 조정"""
    print("기존 PII 태그들의 공백 트림을 시작합니다...")
    
    # 공백이 있는 태그들 찾기
    tags_with_spaces = PIITag.objects.exclude(span_text__regex=r'^\S.*\S$').exclude(span_text__regex=r'^\S+$')
    
    print(f"공백이 있는 태그 수: {tags_with_spaces.count()}")
    
    updated_count = 0
    for tag in tags_with_spaces:
        original_span_text = tag.span_text
        trimmed_span_text = original_span_text.strip()
        
        # 트림된 텍스트가 원본과 다르면 업데이트
        if trimmed_span_text != original_span_text:
            left_trim_count = len(original_span_text) - len(original_span_text.lstrip())
            right_trim_count = len(original_span_text) - len(original_span_text.rstrip())
            
            # 원본 offset 저장
            original_start_offset = tag.start_offset
            original_end_offset = tag.end_offset
            
            # offset 조정
            new_start_offset = tag.start_offset + left_trim_count
            new_end_offset = tag.end_offset - right_trim_count
            
            # end_offset이 start_offset보다 작아지지 않도록 보정
            if new_end_offset <= new_start_offset:
                new_end_offset = new_start_offset + len(trimmed_span_text)
            
            # 업데이트
            tag.span_text = trimmed_span_text
            tag.start_offset = new_start_offset
            tag.end_offset = new_end_offset
            tag.save()
            
            updated_count += 1
            print(f"태그 ID {tag.id}: '{original_span_text}' -> '{trimmed_span_text}' (offset: {original_start_offset}-{original_end_offset} -> {new_start_offset}-{new_end_offset})")
    
    print(f"총 {updated_count}개의 태그가 업데이트되었습니다.")
    print("공백 트림 작업이 완료되었습니다.")

if __name__ == '__main__':
    trim_existing_tags()
