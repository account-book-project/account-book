FROM python:3.13

RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /app

RUN pip install --upgrade pip

COPY ./ /app

RUN pip install -r requirements.txt

# Gunicorn으로 실행 (운영 환경)
ENTRYPOINT [ "sh", "-c", "python manage.py migrate && gunicorn config.wsgi:application -b 0.0.0.0:8000" ]



