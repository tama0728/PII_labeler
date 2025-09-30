#!/usr/bin/env python
import os
import django
import json
import argparse

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pii_labeler.settings')
django.setup()

from main.models import PIICategory

def load_pii_categories(clear_existing: bool = False, path: str = './tag.json'):
    """tag.json 파일에서 PII 카테고리 데이터를 로드

    Args:
        clear_existing (bool): True면 기존 카테고리를 모두 삭제 후 로드합니다. False면 삭제하지 않고 upsert 합니다.
        path (str): 카테고리 JSON 파일 경로
    """

    # tag.json 파일 읽기
    with open(path, 'r', encoding='utf-8') as f:
        categories_data = json.load(f)

    if clear_existing:
        print("기존 카테고리를 모두 삭제합니다...")
        PIICategory.objects.all().delete()

    created_or_updated_count = 0
    for category_data in categories_data:
        value = category_data['value']
        background_color = category_data['background']
        description = category_data['description']

        category, created = PIICategory.objects.update_or_create(
            value=value,
            defaults={
                'background_color': background_color,
                'description': description,
            },
        )

        if created:
            print(f'PII 카테고리 생성: {value}')
        else:
            print(f'PII 카테고리 업데이트: {value}')

        created_or_updated_count += 1

    print(f'총 {created_or_updated_count}개의 PII 카테고리를 처리했습니다.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PII 카테고리를 tag.json 파일에서 로드합니다.')
    parser.add_argument('--path', default='./tag.json', help='카테고리 JSON 파일 경로 (기본: ./tag.json)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--clear', dest='clear_existing', action='store_true', help='기존 카테고리를 모두 삭제 후 로드')
    parser.set_defaults(clear_existing=False)

    args = parser.parse_args()

    print("PII 카테고리를 로드합니다...")
    load_pii_categories(clear_existing=args.clear_existing, path=args.path)
