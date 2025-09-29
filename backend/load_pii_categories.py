#!/usr/bin/env python
import os
import django
import json
import argparse

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pii_labeler.settings')
django.setup()

from main.models import PIICategory

def load_pii_categories():
    """tag.json 파일에서 PII 카테고리 데이터를 로드
    
    Args:
        overwrite (bool): True이면 기존 카테고리를 덮어쓰기, False이면 새로운 카테고리만 생성
    """
    
    # tag.json 파일 읽기
    with open('./tag.json', 'r', encoding='utf-8') as f:
        categories_data = json.load(f)
    
    created_count = 0
    
    PIICategory.objects.all().delete()
    
    for category_data in categories_data:
        value = category_data['value']
        background_color = category_data['background']
        description = category_data['description']
        

            
        category, created = PIICategory.objects.update_or_create(
            value=value,
            defaults={
                'background_color': background_color,
                'description': description
            }
        )
        
        created_count += 1
        print(f'PII 카테고리 생성: {value}')
        
    
    print(f'총 {created_count}개의 새로운 PII 카테고리가 생성되었습니다.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PII 카테고리를 tag.json 파일에서 로드합니다.')
    

    
    print("PII 카테고리를 로드합니다...")
    
    load_pii_categories()
