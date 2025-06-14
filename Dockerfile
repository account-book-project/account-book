FROM python:3.12-slim

RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /app

# 1) requirements.txt만 복사
COPY requirements.txt ./

# 2) 패키지 설치
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 3) 나머지 코드 복사
COPY . .

# 4) 정적 파일 모으기
RUN python manage.py collectstatic --noinput

# 4) 마이그레이트 후 실행
ENTRYPOINT [ "sh", "-c", "python manage.py migrate && gunicorn config.wsgi:application -b 0.0.0.0:8000" ]



