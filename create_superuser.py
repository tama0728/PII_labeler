#!/usr/bin/env python
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pii_labeler.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
    
    if User.objects.filter(username=username).exists():
        print(f'슈퍼유저 {username}이 이미 존재합니다.')
    else:
        User.objects.create_superuser(username, email, password)
        print(f'슈퍼유저 {username}이 생성되었습니다.')
        print(f'사용자명: {username}')
        print(f'비밀번호: {password}')

if __name__ == '__main__':
    create_superuser()
