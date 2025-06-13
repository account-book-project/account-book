# core/management/commands/wait_for_db.py

import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
from psycopg2 import OperationalError as Psycopg2OpError


class Command(BaseCommand):
    help = 'PostgreSQL DB가 준비될 때까지 기다립니다.'

    def handle(self, *args, **options):
        max_attempts = 10
        wait_seconds = 1

        self.stdout.write(self.style.NOTICE('🚀 DB 연결 시도 시작!'))

        for attempt in range(1, max_attempts + 1):
            try:
                db_conn = connections['default']
                c = db_conn.cursor()  #  진짜 연결 시도!
                c.execute('SELECT 1')  #  DB에 쿼리 날림
                self.stdout.write(self.style.SUCCESS('PostgreSQL DB 연결 성공!'))
                return
            except (Psycopg2OpError, OperationalError) as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'  {attempt}회차 연결 실패. {wait_seconds}초 후 재시도...'
                    )
                )
                time.sleep(wait_seconds)

        self.stdout.write(self.style.ERROR(' DB 연결 실패! 최대 재시도 횟수 초과.'))
