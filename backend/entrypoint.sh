#!/bin/bash

# 데이터베이스 연결 대기
echo "데이터베이스 연결을 기다리는 중..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  echo "PostgreSQL이 준비될 때까지 기다리는 중..."
  sleep 2
done

echo "데이터베이스 연결 완료!"

# Django 마이그레이션 실행
echo "Django 마이그레이션 실행 중..."
python manage.py migrate

# 슈퍼유저 생성
echo "슈퍼유저 생성 중..."
python create_superuser.py

# PII 카테고리 로드
echo "PII 카테고리 로드 중..."
python load_pii_categories.py

# Django 개발 서버 시작
echo "Django 서버 시작 중..."
python manage.py runserver 0.0.0.0:8008
