FROM python:3.13

RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /app

RUN pip install --upgrade pip

COPY ./ /app

RUN pip install -r requirements.txt

ENTRYPOINT [ "sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000" ]


