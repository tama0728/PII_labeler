#!/usr/bin/env python
import os
import django
import json

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pii_labeler.settings')
django.setup()

from main.models import PIICategory

def load_pii_categories():
    """tag.json 파일에서 PII 카테고리 데이터를 로드"""
    
    # tag.json 파일 읽기
    with open('tag.json', 'r', encoding='utf-8') as f:
        categories_data = json.load(f)
    
    created_count = 0
    for category_data in categories_data:
        value = category_data['value']
        background_color = category_data['background']
        
        # 기존 카테고리가 있는지 확인
        category, created = PIICategory.objects.get_or_create(
            value=value,
            defaults={
                'background_color': background_color,
                'description': f'{value} 관련 개인정보'
            }
        )
        
        if created:
            created_count += 1
            print(f'PII 카테고리 생성: {value}')
        else:
            print(f'PII 카테고리 이미 존재: {value}')
    
    print(f'총 {created_count}개의 새로운 PII 카테고리가 생성되었습니다.')

if __name__ == '__main__':
    load_pii_categories()
