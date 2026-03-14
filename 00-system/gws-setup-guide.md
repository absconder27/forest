# Google Workspace API 연동 설정 가이드

> Claude Code에서 Google Calendar, Sheets, Gmail을 사용하기 위한 초기 설정

---

## 개요

| 서비스 | 용도 | API |
|--------|------|-----|
| Google Calendar | 일정 조회/생성/수정 | Calendar API v3 |
| Google Sheets | 스프레드시트 읽기/쓰기 | Sheets API v4 |
| Gmail | 이메일 발송/조회 | Gmail API v1 |

**인증 방식**: OAuth 2.0 (개인 사용, 브라우저 인증)

---

## Step 1: Google Cloud 프로젝트 설정

### 1-1. Google Cloud Console 접속

```
https://console.cloud.google.com/
```

### 1-2. 프로젝트 생성

1. 상단 프로젝트 선택 드롭다운 클릭
2. **"새 프로젝트"** 클릭
3. 프로젝트 이름: `Claude Code PKM` (원하는 이름)
4. **"만들기"** 클릭
5. 생성된 프로젝트 선택

---

## Step 2: API 활성화

### 2-1. API 라이브러리 접속

```
https://console.cloud.google.com/apis/library
```

### 2-2. 3개 API 각각 활성화

다음 API를 검색하고 **"사용"** 클릭:

1. **Google Calendar API**
2. **Google Sheets API**
3. **Gmail API**

---

## Step 3: OAuth 동의 화면 설정

### 3-1. 동의 화면 구성

```
https://console.cloud.google.com/apis/credentials/consent
```

1. User Type: **외부(External)** 선택 → **"만들기"**
2. 앱 정보:
   - 앱 이름: `Claude Code`
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처: 본인 이메일
3. **"저장 후 계속"**

### 3-2. 범위(Scopes) 추가

**"범위 추가 또는 삭제"** 클릭 후 다음 범위 선택:

| 범위 | 설명 |
|------|------|
| `https://www.googleapis.com/auth/calendar` | 캘린더 전체 접근 |
| `https://www.googleapis.com/auth/spreadsheets` | 스프레드시트 전체 접근 |
| `https://www.googleapis.com/auth/gmail.modify` | 이메일 읽기/발송/수정 |

**"저장 후 계속"**

### 3-3. 테스트 사용자 추가

1. **"+ ADD USERS"** 클릭
2. 본인 Google 계정 이메일 추가
3. **"저장 후 계속"**

> **참고**: 앱이 "테스트" 상태이므로 등록된 테스트 사용자만 인증 가능합니다.
> 개인 용도이므로 "프로덕션 게시"는 불필요합니다.

---

## Step 4: OAuth 클라이언트 ID 생성

### 4-1. 사용자 인증 정보 페이지

```
https://console.cloud.google.com/apis/credentials
```

### 4-2. OAuth 클라이언트 ID 만들기

1. **"+ 사용자 인증 정보 만들기"** → **"OAuth 클라이언트 ID"**
2. 애플리케이션 유형: **데스크톱 앱**
3. 이름: `Claude Code Desktop`
4. **"만들기"** 클릭

### 4-3. credentials.json 다운로드

1. 생성 완료 팝업에서 **"JSON 다운로드"** 클릭
2. 다운로드된 파일을 다음 경로로 이동:

```bash
mv ~/Downloads/client_secret_*.json \
   ~/do-better-workspace/00-system/02-scripts/gws/credentials.json
```

---

## Step 5: Python 환경 설정

### 5-1. 디렉토리 생성 및 의존성 설치

```bash
cd ~/do-better-workspace/00-system/02-scripts/gws

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# Google API 라이브러리 설치
pip install google-auth google-auth-oauthlib google-api-python-client
```

---

## Step 6: 최초 인증 실행

### 6-1. 인증 스크립트 실행

```bash
cd ~/do-better-workspace/00-system/02-scripts/gws
python3 gws_auth.py
```

### 6-2. 브라우저 인증

1. 브라우저가 자동으로 열립니다
2. Google 계정 로그인
3. "Claude Code에서 다음을 요청합니다" → **"허용"**
4. "이 앱은 확인되지 않았습니다" 경고 → **"고급"** → **"이동"**
5. 모든 권한 허용

### 6-3. 인증 완료 확인

```
✅ 인증 성공!
📅 Calendar API: 연결됨
📊 Sheets API: 연결됨
📧 Gmail API: 연결됨
토큰 저장 위치: token.json
```

---

## Step 7: 환경변수 설정

`.env` 파일에 추가:

```bash
# Google Workspace OAuth
GWS_CREDENTIALS_PATH=00-system/02-scripts/gws/credentials.json
GWS_TOKEN_PATH=00-system/02-scripts/gws/token.json
```

---

## 토큰 관리

### 토큰 갱신

- 토큰은 자동으로 갱신됩니다 (refresh token 포함)
- 만료 시 `gws_auth.py`를 다시 실행하세요

### 토큰 초기화

권한 변경이나 문제 발생 시:

```bash
rm ~/do-better-workspace/00-system/02-scripts/gws/token.json
python3 ~/do-better-workspace/00-system/02-scripts/gws/gws_auth.py
```

---

## 자주 묻는 질문

### Q: "Access blocked: This app's request is invalid" 오류
**A**: OAuth 동의 화면에서 테스트 사용자로 본인 이메일이 추가되었는지 확인

### Q: "invalid_grant" 오류
**A**: `token.json` 삭제 후 재인증 (`gws_auth.py` 다시 실행)

### Q: 특정 API만 권한 오류
**A**: Google Cloud Console에서 해당 API가 활성화되었는지 확인

### Q: 리프레시 토큰이 만료됨
**A**: 테스트 앱의 리프레시 토큰은 7일 후 만료됩니다.
"프로덕션 게시"하면 만료 없이 사용 가능합니다.
(Google 검증 불필요 - "내부 사용"으로 게시 가능)

---

## 보안 주의사항

- `credentials.json`, `token.json`은 절대 Git에 커밋 금지
- `.gitignore`에 이미 등록되어 있음
- 토큰 유출 시: Google Cloud Console → 사용자 인증 정보 → 해당 클라이언트 삭제 후 재생성

---

## 다음 단계

설정 완료 후 사용 가능한 기능:
- **Calendar**: 일정 조회, 생성, 수정, 삭제
- **Sheets**: 스프레드시트 읽기, 쓰기, 생성
- **Gmail**: 이메일 조회, 발송, 라벨 관리

사용법: Claude Code에 자연어로 요청하세요.
