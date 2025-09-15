# PII Labeler

PII(Personally Identifiable Information) 태깅을 위한 웹 애플리케이션입니다.

## 프로젝트 구조

```
PII_labeler/
├── backend/                 # Django 백엔드
│   ├── main/               # Django 앱
│   ├── pii_labeler/        # Django 프로젝트 설정
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── entrypoint.sh
├── frontend/               # Nginx 프론트엔드
│   ├── static/            # 정적 파일
│   ├── templates/         # HTML 템플릿
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml     # 전체 서비스 오케스트레이션
└── .env                   # 환경 변수
```

## 서비스 구성

- **Database (PostgreSQL)**: 포트 5433 (외부) → 5432 (내부)
- **Backend (Django)**: 포트 8008
- **Frontend (Nginx)**: 포트 8000

## 환경 변수 설정

`.env` 파일에서 다음 변수들을 설정할 수 있습니다:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database Configuration
DB_NAME=pii_labeler_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5433

# Service Ports
FRONTEND_PORT=8000
BACKEND_PORT=8008

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 실행 방법

1. **전체 서비스 시작**:
   ```bash
   docker compose up -d
   ```

2. **개별 서비스 시작**:
   ```bash
   # 데이터베이스만
   docker compose up -d db
   
   # 백엔드만
   docker compose up -d backend
   
   # 프론트엔드만
   docker compose up -d frontend
   ```

3. **서비스 중지**:
   ```bash
   docker compose down
   ```

## 접속 정보

- **웹 애플리케이션**: http://localhost:8000
- **Django 관리자**: http://localhost:8000/admin
- **백엔드 API**: http://localhost:8008 (직접 접속)

## 기본 계정

- **사용자명**: admin
- **비밀번호**: admin123

## 개발 모드

개발 중에는 볼륨 마운트를 통해 코드 변경사항이 실시간으로 반영됩니다.

```bash
# 개발 모드로 실행
docker-compose up
```

## 포트 충돌 해결

서버에서 포트가 충돌하는 경우 `.env` 파일에서 포트를 변경할 수 있습니다:

```env
DB_PORT=5434        # 데이터베이스 외부 포트
FRONTEND_PORT=8001  # 프론트엔드 포트
BACKEND_PORT=8009   # 백엔드 포트
```