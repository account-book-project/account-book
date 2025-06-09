# account-book
"가계부 시스템 미니 프로젝트"
# 📚 ERD 설계 (Account Book Project)

본 프로젝트는 사용자, 계좌, 거래 내역을 관리하고 추가로 수입/지출 분석 및 알림 기능을 제공합니다.

## 📖 테이블 설명

| 테이블 이름 | 설명 |
|:--|:--|
| **users** | 서비스 사용자 정보를 저장합니다. |
| **accounts** | 사용자가 보유한 계좌 정보를 저장합니다. |
| **transaction_history** | 계좌별 거래 내역을 저장합니다. |
| **analysis** | 수입과 지출 내역을 분석하고 결과를 저장합니다. |
| **notifications** | 사용자 알림을 관리합니다. |

## 🔗 테이블 관계

- **users 1:N accounts**
- **accounts 1:N transaction_history**
- **users 1:N analysis**
- **users 1:N notifications**

## 🖼️ ERD 다이어그램 (Mermaid)

```mermaid
erDiagram
    users {
        int id PK "Primary Key, Auto Increment"
        varchar email "이메일 (Unique)"
        varchar password "비밀번호"
        varchar nickname "닉네임"
        varchar name "이름"
        varchar phone_number "전화번호"
        datetime last_login "마지막 로그인"
        boolean is_staff "스태프 여부 (Default: False)"
        boolean is_admin "관리자 여부 (Default: False)"
        boolean is_active "계정 활성화 여부 (Default: True)"
    }

    accounts {
        int id PK "Primary Key, Auto Increment"
        int user_id FK "Foreign Key: users.id"
        varchar account_number "계좌번호 (Unique)"
        varchar bank_code "은행 코드"
        varchar account_type "계좌 종류"
        decimal balance "잔액"
    }

    transaction_history {
        int id PK "Primary Key, Auto Increment"
        int account_id FK "Foreign Key: accounts.id"
        decimal transaction_amount "거래 금액"
        decimal post_transaction_amount "거래 후 잔액"
        varchar transaction_details "거래 상세 내역"
        enum transaction_type "입출금 타입 (입금/출금)"
        enum transaction_method "거래 방법 (현금, 계좌 이체, 자동 이체, 카드 결제)"
        datetime transaction_timestamp "거래 일시"
    }

    analysis {
        int id PK "Primary Key, Auto Increment"
        int user_id FK "Foreign Key: users.id"
        enum analysis_target "분석 대상 (수입/지출)"
        enum analysis_period "분석 기간 (일간/주간/월간/연간)"
        date start_date "분석 시작 날짜"
        date end_date "분석 종료 날짜"
        text description "설명"
        varchar result_image "분석 결과 이미지"
        datetime created_at "생성 날짜"
        datetime updated_at "업데이트 날짜"
    }

    notifications {
        int id PK "Primary Key, Auto Increment"
        int user_id FK "Foreign Key: users.id"
        text message "메시지 내용"
        boolean is_read "읽음 여부 (Default: False)"
        datetime created_at "생성 날짜"
    }

    users ||--o{ accounts : has
    accounts ||--o{ transaction_history : has
    users ||--o{ analysis : has
    users ||--o{ notifications : has
