FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /code

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# Django 마이그레이션 및 서버 실행을 위한 스크립트
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# 포트 노출
EXPOSE 8008

# 엔트리포인트 실행
ENTRYPOINT ["./entrypoint.sh"]
