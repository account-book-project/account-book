#!/bin/bash

echo "Code Quality and Test Automation Script Start 🚀"

echo "1️⃣ Check code format with isort"
isort . --check --diff
if [ $? -ne 0 ]; then
  echo "❌ isort 검사 실패: import 정렬을 맞춰주세요."
  exit 1
fi

echo "2️⃣ Check code format with black"
black . --check
if [ $? -ne 0 ]; then
  echo "❌ black 검사 실패: 코드 스타일을 맞춰주세요."
  exit 1
fi

echo "3️⃣ Apply migrations (check) - 로컬 개발 환경 기준(dev.py)"
python manage.py migrate --settings=config.settings.dev --check
if [ $? -ne 0 ]; then
  echo "❌ 마이그레이션 필요 또는 실패. 'python manage.py migrate --settings=config.settings.dev'를 직접 실행하세요."
  exit 1
fi

echo "4️⃣ Run Django tests - 로컬 개발 환경 기준(dev.py)"
python manage.py test --settings=config.settings.dev
if [ $? -ne 0 ]; then
  echo "❌ 테스트 실패. 문제를 확인하세요."
  exit 1
fi

echo "모든 검사 통과! "
