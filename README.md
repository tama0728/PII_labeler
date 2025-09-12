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

프로젝트는 `.env` 파일을 통해 환경변수를 관리합니다:

```bash
# .env 파일 복사 및 설정
cp .env.example .env

# .env 파일 편집 (필요시 데이터베이스 설정 수정)
nano .env
```

**주요 환경변수:**
- `DEBUG`: 디버그 모드 활성화 (개발: True, 운영: False)
- `SECRET_KEY`: Django 암호화 키 (운영환경에서는 반드시 변경)
- `DB_*`: PostgreSQL 데이터베이스 연결 정보
- `ALLOWED_HOSTS`: 허용된 호스트 목록

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

리팩토링된 구조로 코드가 모듈화되어 유지보수성이 향상되었습니다:

```
PII_labeler/
├── main/                    # 메인 Django 앱
│   ├── models.py           # 데이터 모델 (Document, PIITag, PIICategory)
│   ├── views.py            # 메인 뷰 (임포트 허브)
│   ├── web_views.py        # 웹 페이지 뷰들 (템플릿 렌더링)
│   ├── api_views.py        # API 뷰들 (JSON 응답)
│   ├── services.py         # 비즈니스 로직 서비스 레이어
│   ├── forms.py            # Django Forms (데이터 검증)
│   ├── utils.py            # 유틸리티 함수들
│   ├── urls.py             # URL 라우팅
│   ├── admin.py            # Django Admin 설정
│   ├── templates/          # HTML 템플릿들
│   └── migrations/         # 데이터베이스 마이그레이션
├── pii_labeler/            # Django 프로젝트 설정
│   ├── settings.py         # 프로젝트 설정 (환경변수 지원)
│   ├── urls.py             # 메인 URL 설정
│   └── wsgi.py             # WSGI 설정
├── requirements.txt        # Python 의존성
├── docker-compose.yml      # Docker Compose 설정
├── Dockerfile              # Docker 이미지 설정
├── .env                    # 환경변수 (개발용)
├── .env.example            # 환경변수 템플릿
├── .gitignore              # Git 무시 파일 목록
└── README.md               # 프로젝트 문서
```

## 아키텍처

프로젝트는 **레이어드 아키텍처**를 따르며, 각 레이어는 명확한 책임을 가집니다:

### 레이어 구조

1. **프레젠테이션 레이어**
   - `web_views.py`: 웹 페이지 렌더링 (HTML 응답)
   - `api_views.py`: REST API 엔드포인트 (JSON 응답)
   - `forms.py`: 입력 데이터 검증

2. **서비스 레이어**
   - `services.py`: 비즈니스 로직 처리
   - 트랜잭션 관리 및 복합 연산 처리

3. **데이터 레이어**
   - `models.py`: 데이터 모델 정의
   - `utils.py`: 데이터 처리 유틸리티

### 주요 개선사항

- ✅ **단일 책임 원칙**: 각 모듈이 하나의 명확한 역할
- ✅ **관심사 분리**: 비즈니스 로직과 프레젠테이션 로직 분리
- ✅ **재사용성**: 공통 기능들의 모듈화
- ✅ **테스트 용이성**: 각 레이어별 독립적 테스트 가능
- ✅ **확장성**: 새로운 기능 추가 시 기존 코드 영향 최소화

## 데이터베이스 모델

### PIICategory
- PII 카테고리 정보 (이름, 배경색, 설명)

### Document
- 문서 메타데이터 (data_id, dialog_type, turn_cnt 등)
- 문서 텍스트 내용
- 생성자 및 생성/수정 시간

### PIITag
- PII 태그 정보 (span_text, start/end_offset)
- 메타데이터 (span_id, entity_id, annotator, identifier_type)
- 신뢰도 점수 및 생성 정보

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

# 특정 앱 테스트
python3 manage.py test main

# 커버리지와 함께 테스트 (coverage 패키지 설치 필요)
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### 코드 품질 관리

```bash
# 코드 스타일 검사 (flake8)
pip install flake8
flake8 main/ pii_labeler/

# 코드 포맷팅 (black)
pip install black
black main/ pii_labeler/

# Import 정리 (isort)
pip install isort
isort main/ pii_labeler/
```

### 개발 워크플로우

1. **기능 개발**
   - 새로운 기능은 서비스 레이어(`services.py`)에 비즈니스 로직 구현
   - 필요시 유틸리티 함수는 `utils.py`에 추가
   - 폼 검증이 필요하면 `forms.py`에 정의

2. **뷰 개발**
   - 웹 페이지: `web_views.py`에 템플릿 렌더링 뷰 추가
   - API: `api_views.py`에 JSON 응답 뷰 추가

3. **URL 라우팅**
   - `urls.py`에 새로운 URL 패턴 추가

4. **데이터베이스 변경**
   - `models.py` 수정 후 마이그레이션 생성 및 적용

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
