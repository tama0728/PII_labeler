# PII Labeler

Django와 PostgreSQL을 사용한 개인정보 식별 및 라벨링 도구입니다.

## 주요 기능

- 📄 문서 업로드 및 관리
- 🏷️ 개인정보(PII) 태깅 시스템
- 👤 사용자 인증 및 권한 관리
- 📊 PII 태그 통계 및 관리
- 🐳 Docker 지원

## 기술 스택

- **Backend**: Django 4.2.7
- **Database**: PostgreSQL 15
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Deployment**: Docker, Docker Compose

## 설치 및 실행

### 1. 저장소 클론

```bash
git clone <repository-url>
cd PII_labeler
```

### 2. 환경 설정

```bash
# .env 파일 복사
cp .env.example .env

# .env 파일 편집 (필요시 데이터베이스 설정 수정)
nano .env
```

### 3. Docker를 사용한 실행 (권장)

```bash
# PostgreSQL 데이터베이스와 Django 앱 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build
```

### 4. 로컬 실행

```bash
# Python 가상환경 생성 (선택사항)
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성 및 설정
cp .env.example .env
# .env 파일에서 데이터베이스 연결 정보 확인 (포트 5433 사용)

# 마이그레이션 실행
python3 manage.py makemigrations
python3 manage.py migrate

# 슈퍼유저 생성
python3 manage.py createsuperuser

# 개발 서버 실행
python3 manage.py runserver
```

## 사용법

1. **회원가입/로그인**: 웹 인터페이스에서 계정을 생성하고 로그인합니다.

2. **문서 생성**: "새 문서" 버튼을 클릭하여 분석할 텍스트 문서를 생성합니다.

3. **PII 태깅**: 문서 상세 페이지에서 개인정보를 식별하고 태그를 추가합니다.

4. **관리**: Django Admin 인터페이스(`/admin/`)에서 모든 데이터를 관리할 수 있습니다.

## 프로젝트 구조

```
PII_labeler/
├── main/                    # 메인 Django 앱
│   ├── models.py           # 데이터 모델 (Document, PIITag)
│   ├── views.py            # 뷰 함수들
│   ├── urls.py             # URL 라우팅
│   ├── admin.py            # Django Admin 설정
│   └── templates/          # HTML 템플릿들
├── pii_labeler/            # Django 프로젝트 설정
│   ├── settings.py         # 프로젝트 설정 (PostgreSQL 설정 포함)
│   ├── urls.py             # 메인 URL 설정
│   └── wsgi.py             # WSGI 설정
├── requirements.txt        # Python 의존성
├── docker-compose.yml      # Docker Compose 설정
├── Dockerfile              # Docker 이미지 설정
├── .env.example            # 환경변수 예시
└── README.md               # 프로젝트 문서
```

## 데이터베이스 모델

### Document
- 문서 제목, 내용, 생성자, 생성/수정 시간

### PIITag
- PII 유형 (이름, 이메일, 전화번호 등)
- 태그된 텍스트와 위치 정보
- 신뢰도 점수

## 환경변수

`.env` 파일에서 다음 설정을 관리할 수 있습니다:

```env
# Django 설정
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL 데이터베이스 설정 (포트 충돌 방지를 위해 5433 사용)
DB_NAME=pii_labeler_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5433
```

## 포트 정보

- **웹 애플리케이션**: `http://localhost:8001`
- **PostgreSQL 데이터베이스**: `localhost:5433`
- **Django Admin**: `http://localhost:8001/admin/`

## 개발

### 마이그레이션

```bash
# 모델 변경 후 마이그레이션 생성
python3 manage.py makemigrations

# 마이그레이션 적용
python3 manage.py migrate
```

### 테스트

```bash
# 테스트 실행
python3 manage.py test
```

## 라이선스

MIT License

## 기여

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.
