---
name: telegram-handler
description: 텔레그램 메시지 전송/수신 관리
triggers:
  - "텔레그램"
  - "telegram"
  - "텔레그램 보내"
  - "텔레그램 확인"
  - "텔레그램 브리핑"
  - "텔레그램 인박스"
  - "telegram daily"
  - "telegram inbox"
allowed-tools: Bash, Read, Write, Edit
---

# Telegram Handler

텔레그램 봇을 통한 메시지 전송/수신을 처리합니다.

## 기능

### 1. Daily Briefing 전송
사용자가 "텔레그램 브리핑", "텔레그램으로 보내", "daily briefing 텔레그램" 등을 요청하면:
- `/telegram-daily` 커맨드 실행

### 2. Inbox 수집
사용자가 "텔레그램 확인", "텔레그램 메시지", "telegram inbox" 등을 요청하면:
- `/telegram-inbox` 커맨드 실행

### 3. 단순 메시지 전송
사용자가 "텔레그램으로 [내용] 보내줘" 등을 요청하면:
- `./00-system/02-scripts/gws/venv/bin/python3 ./00-system/02-scripts/telegram/telegram_api.py send "내용"` 실행

## 스크립트 위치
- API 래퍼: `00-system/02-scripts/telegram/telegram_api.py`
- 환경변수: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## 셋업 가이드
1. Telegram에서 @BotFather에게 `/newbot` 명령
2. 봇 이름/username 설정 후 Bot Token 발급
3. 발급받은 토큰을 `.env` 파일에 `TELEGRAM_BOT_TOKEN=토큰` 저장
4. 봇과 1:1 대화 시작 (아무 메시지 전송)
5. `./00-system/02-scripts/gws/venv/bin/python3 ./00-system/02-scripts/telegram/telegram_api.py setup` 실행
6. 출력된 Chat ID를 `.env` 파일에 `TELEGRAM_CHAT_ID=ID` 저장
7. `./00-system/02-scripts/gws/venv/bin/python3 ./00-system/02-scripts/telegram/telegram_api.py test` 로 확인
