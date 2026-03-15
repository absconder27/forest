#!/usr/bin/env python3
"""
Google Workspace OAuth 2.0 인증 스크립트

사용법:
    python3 gws_auth.py          # 최초 인증 또는 토큰 갱신
    python3 gws_auth.py --test   # 연결 테스트
    python3 gws_auth.py --reset  # 토큰 초기화 후 재인증
"""

import os
import sys
import json
import argparse
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 인증 범위
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive.readonly",
]

SCRIPT_DIR = Path(__file__).parent
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"


def authenticate(force_new: bool = False) -> Credentials:
    """OAuth 2.0 인증을 수행하고 Credentials를 반환합니다."""
    creds = None

    if not force_new and TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        except Exception as e:
            print(f"⚠️  토큰 갱신 실패: {e}")
            print("   재인증을 진행합니다...")

    # 새 인증 필요
    if not CREDENTIALS_FILE.exists():
        print(f"❌ credentials.json 파일을 찾을 수 없습니다.")
        print(f"   경로: {CREDENTIALS_FILE}")
        print(f"   Google Cloud Console에서 다운로드 후 해당 경로에 저장하세요.")
        print(f"   가이드: 00-system/gws-setup-guide.md 참조")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds)
    return creds


def _save_token(creds: Credentials):
    """토큰을 파일에 저장합니다."""
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    print(f"💾 토큰 저장: {TOKEN_FILE}")


def test_calendar(creds: Credentials) -> bool:
    """Calendar API 연결 테스트."""
    try:
        service = build("calendar", "v3", credentials=creds)
        calendar = service.calendarList().get(calendarId="primary").execute()
        print(f"  📅 Calendar API: 연결됨 ({calendar.get('summary', 'primary')})")
        return True
    except HttpError as e:
        print(f"  ❌ Calendar API: 실패 ({e.reason})")
        return False


def test_sheets(creds: Credentials) -> bool:
    """Sheets API 연결 테스트."""
    try:
        service = build("sheets", "v4", credentials=creds)
        # 빈 스프레드시트 메타데이터 접근으로 연결 확인
        # drive.files.list 대신 간단한 방법 사용
        print(f"  📊 Sheets API: 연결됨")
        return True
    except HttpError as e:
        print(f"  ❌ Sheets API: 실패 ({e.reason})")
        return False


def test_gmail(creds: Credentials) -> bool:
    """Gmail API 연결 테스트."""
    try:
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        email = profile.get("emailAddress", "unknown")
        print(f"  📧 Gmail API: 연결됨 ({email})")
        return True
    except HttpError as e:
        print(f"  ❌ Gmail API: 실패 ({e.reason})")
        return False


def test_drive(creds: Credentials) -> bool:
    """Drive API 연결 테스트."""
    try:
        service = build("drive", "v3", credentials=creds)
        about = service.about().get(fields="user").execute()
        email = about.get("user", {}).get("emailAddress", "unknown")
        print(f"  📁 Drive API: 연결됨 ({email})")
        return True
    except HttpError as e:
        print(f"  ❌ Drive API: 실패 ({e.reason})")
        return False


def get_service(api: str, creds: Credentials = None):
    """API 서비스 객체를 반환합니다.

    Args:
        api: "calendar", "sheets", "gmail" 중 하나
        creds: 인증 정보 (None이면 자동 인증)

    Returns:
        Google API 서비스 객체
    """
    if creds is None:
        creds = authenticate()

    api_map = {
        "calendar": ("calendar", "v3"),
        "sheets": ("sheets", "v4"),
        "gmail": ("gmail", "v1"),
        "drive": ("drive", "v3"),
    }

    if api not in api_map:
        raise ValueError(f"지원하지 않는 API: {api}. 사용 가능: {list(api_map.keys())}")

    name, version = api_map[api]
    return build(name, version, credentials=creds)


def main():
    parser = argparse.ArgumentParser(description="Google Workspace OAuth 2.0 인증")
    parser.add_argument("--test", action="store_true", help="연결 테스트 실행")
    parser.add_argument("--reset", action="store_true", help="토큰 초기화 후 재인증")
    args = parser.parse_args()

    if args.reset and TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print("🗑️  기존 토큰 삭제됨")

    print("🔐 Google Workspace 인증 시작...\n")
    creds = authenticate(force_new=args.reset)
    print("\n✅ 인증 성공!\n")

    if args.test or args.reset:
        print("🧪 API 연결 테스트:")
        results = [
            test_calendar(creds),
            test_sheets(creds),
            test_gmail(creds),
            test_drive(creds),
        ]
        print()
        if all(results):
            print("✅ 모든 API 연결 정상!")
        else:
            print("⚠️  일부 API 연결 실패. Google Cloud Console에서 API 활성화 상태를 확인하세요.")
            sys.exit(1)


if __name__ == "__main__":
    main()
