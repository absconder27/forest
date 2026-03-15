#!/usr/bin/env python3
"""
Telegram Bot API 래퍼

메시지 전송/수신, 연결 테스트 기능 제공.
requests 직접 호출 방식 (외부 라이브러리 최소화).

Usage:
    python3 telegram_api.py test
    python3 telegram_api.py send "메시지 내용"
    python3 telegram_api.py fetch
    python3 telegram_api.py setup
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests 패키지가 필요합니다: pip install requests", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
LAST_UPDATE_ID_FILE = SCRIPT_DIR / "last_update_id.txt"
BASE_URL = "https://api.telegram.org/bot{token}/{method}"
MAX_MESSAGE_LENGTH = 4096


def get_config() -> dict:
    """환경변수에서 Telegram 설정을 읽습니다."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    return {"token": token, "chat_id": chat_id}


def _api_call(token: str, method: str, params: dict = None) -> dict:
    """Telegram Bot API 호출."""
    url = BASE_URL.format(token=token, method=method)
    resp = requests.post(url, json=params or {}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API 오류: {data.get('description', 'unknown')}")
    return data.get("result", {})


def send_message(text: str, chat_id: str = None, parse_mode: str = "Markdown") -> list[dict]:
    """메시지를 전송합니다. 4096자 초과 시 자동 분할."""
    config = get_config()
    token = config["token"]
    target_chat_id = chat_id or config["chat_id"]

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다")
    if not target_chat_id:
        raise ValueError("TELEGRAM_CHAT_ID 환경변수가 설정되지 않았습니다")

    chunks = _split_message(text)
    results = []

    for chunk in chunks:
        params = {
            "chat_id": target_chat_id,
            "text": chunk,
        }
        if parse_mode:
            params["parse_mode"] = parse_mode

        try:
            result = _api_call(token, "sendMessage", params)
            results.append(result)
        except requests.exceptions.HTTPError:
            # Markdown 파싱 실패 시 plain text로 재시도
            if parse_mode:
                params.pop("parse_mode")
                result = _api_call(token, "sendMessage", params)
                results.append(result)
            else:
                raise

    return results


def _split_message(text: str) -> list[str]:
    """긴 메시지를 4096자 단위로 분할합니다."""
    if len(text) <= MAX_MESSAGE_LENGTH:
        return [text]

    chunks = []
    while text:
        if len(text) <= MAX_MESSAGE_LENGTH:
            chunks.append(text)
            break

        # 줄바꿈 기준으로 자르기
        split_pos = text.rfind("\n", 0, MAX_MESSAGE_LENGTH)
        if split_pos == -1:
            split_pos = MAX_MESSAGE_LENGTH

        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n")

    return chunks


def get_updates(token: str, offset: int = None, limit: int = 100) -> list:
    """봇으로 온 메시지 업데이트를 가져옵니다."""
    params = {"limit": limit, "timeout": 0}
    if offset is not None:
        params["offset"] = offset
    return _api_call(token, "getUpdates", params)


def fetch_new_messages() -> list[dict]:
    """마지막 이후의 새 메시지만 가져옵니다."""
    config = get_config()
    token = config["token"]

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다")

    # 마지막 update_id 읽기
    last_id = None
    if LAST_UPDATE_ID_FILE.exists():
        try:
            last_id = int(LAST_UPDATE_ID_FILE.read_text().strip())
        except ValueError:
            pass

    offset = (last_id + 1) if last_id else None
    updates = get_updates(token, offset=offset)

    if not updates:
        return []

    messages = []
    max_update_id = last_id or 0

    for update in updates:
        update_id = update.get("update_id", 0)
        if update_id > max_update_id:
            max_update_id = update_id

        msg = update.get("message", {})
        if not msg:
            continue

        text = msg.get("text", "")
        if not text:
            continue

        from_user = msg.get("from", {})
        date = msg.get("date", 0)
        dt = datetime.fromtimestamp(date) if date else datetime.now()

        messages.append({
            "text": text,
            "from": from_user.get("first_name", ""),
            "date": dt.strftime("%Y-%m-%d %H:%M"),
            "update_id": update_id,
            "category": categorize_message(text),
        })

    # 마지막 update_id 저장
    if max_update_id > (last_id or 0):
        LAST_UPDATE_ID_FILE.write_text(str(max_update_id))

    return messages


def categorize_message(text: str) -> tuple[str, str]:
    """메시지를 분류합니다.

    Returns:
        (category, cleaned_text) 튜플
        category: "todo", "link", "note"
    """
    stripped = text.strip()

    # #todo 접두사
    if stripped.lower().startswith("#todo "):
        return ("todo", stripped[6:].strip())

    # URL 포함
    url_pattern = r'https?://[^\s]+'
    if re.search(url_pattern, stripped):
        return ("link", stripped)

    # 그 외
    return ("note", stripped)


def test_connection() -> dict:
    """봇 연결을 테스트합니다."""
    config = get_config()
    token = config["token"]

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다")

    result = _api_call(token, "getMe")
    return result


def setup_chat_id():
    """봇과의 대화에서 Chat ID를 자동으로 찾습니다."""
    config = get_config()
    token = config["token"]

    if not token:
        print("TELEGRAM_BOT_TOKEN 환경변수를 먼저 설정하세요.")
        print("1. Telegram에서 @BotFather에게 /newbot 명령")
        print("2. 발급받은 토큰을 .env 파일에 TELEGRAM_BOT_TOKEN=토큰 형식으로 저장")
        sys.exit(1)

    # 봇 정보 확인
    bot_info = _api_call(token, "getMe")
    bot_username = bot_info.get("username", "")
    print(f"봇 확인: @{bot_username}")
    print(f"\nTelegram에서 @{bot_username} 에게 아무 메시지를 보낸 후,")
    print("이 명령을 다시 실행하세요.\n")

    # 업데이트 확인
    updates = get_updates(token)
    if not updates:
        print("아직 메시지가 없습니다. 봇에게 메시지를 보낸 후 다시 실행하세요.")
        sys.exit(1)

    # 가장 최근 메시지의 chat_id 추출
    for update in reversed(updates):
        msg = update.get("message", {})
        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        if chat_id:
            print(f"Chat ID: {chat_id}")
            print(f"\n.env 파일에 다음을 추가하세요:")
            print(f"TELEGRAM_CHAT_ID={chat_id}")
            return

    print("Chat ID를 찾을 수 없습니다. 봇에게 메시지를 보낸 후 다시 실행하세요.")


def main():
    parser = argparse.ArgumentParser(description="Telegram Bot API 래퍼")
    subparsers = parser.add_subparsers(dest="command", help="서브커맨드")

    # test
    subparsers.add_parser("test", help="봇 연결 테스트")

    # setup
    subparsers.add_parser("setup", help="Chat ID 자동 확인")

    # send
    send_parser = subparsers.add_parser("send", help="메시지 전송")
    send_parser.add_argument("text", help="전송할 메시지")
    send_parser.add_argument("--plain", action="store_true", help="Markdown 비활성화")

    # fetch
    subparsers.add_parser("fetch", help="새 메시지 수신 (JSON)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "test":
        try:
            info = test_connection()
            print(f"연결 성공! 봇: @{info.get('username', '')} ({info.get('first_name', '')})")
        except Exception as e:
            print(f"연결 실패: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "setup":
        setup_chat_id()

    elif args.command == "send":
        try:
            parse_mode = None if args.plain else "Markdown"
            results = send_message(args.text, parse_mode=parse_mode)
            print(f"전송 완료 ({len(results)}건)")
        except Exception as e:
            print(f"전송 실패: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "fetch":
        try:
            messages = fetch_new_messages()
            print(json.dumps(messages, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"수신 실패: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
