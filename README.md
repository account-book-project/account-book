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

```

<br>
<br>

# 🔐 회원가입 / 로그인 / 로그아웃 플로우 정리

---

### 1. 회원가입 (Signup)

#### 로직 설명
회원가입은 사용자가 이메일, 비밀번호, 이름 등의 정보를 입력하고, 서버에서 이메일 인증을 통해 최종 활성화하는 과정입니다.

**회원가입 로직 흐름**
- 사용자 정보 입력 (이메일, 비밀번호, 이름 등)
- 서버에서 사용자 생성 + 이메일 인증 토큰 생성
- 인증 이메일 전송 (활성화 URL 포함)
- 사용자가 이메일 링크 클릭
- 서버에서 토큰 검증 → 사용자 계정 활성화

<td align="center"><img src="https://github.com/user-attachments/assets/5aa58afb-3867-43b8-941f-831592a9d667" width="500"/></td>

---

### 2. 로그인 (Login)

#### 로직 설명
로그인은 사용자 인증을 거쳐 JWT 토큰을 발급하고, 이를 쿠키에 저장하는 과정입니다.

**로그인 로직 흐름**
- 사용자 이메일 및 비밀번호 입력
- 서버에서 사용자 인증
- 인증 성공 시 Access/Refresh Token 발급
- 발급된 토큰을 HTTP Only Secure 쿠키에 저장
- 이후 모든 인증 요청은 쿠키의 Access Token으로 처리

<td align="center"><img src="https://github.com/user-attachments/assets/8a47b823-93ab-48a5-ba46-0fdeea89935b" width="500"/></td>

---

### 3. 로그아웃 (Logout)

#### 로직 설명
로그아웃은 JWT 토큰을 삭제하고, Refresh Token을 블랙리스트에 등록하는 방식으로 처리됩니다.

**로그아웃 로직 흐름**
- 클라이언트에서 로그아웃 요청
- 서버에서 쿠키의 Refresh Token 추출
- 존재하면 해당 토큰을 블랙리스트에 등록
- Access / Refresh 쿠키 삭제
- 로그아웃 성공 메시지 반환

<td align="center"><img src="https://github.com/user-attachments/assets/6eb50f94-aa36-4a5e-8f70-8334de481e8f" width="500"/></td>

---

