#!/usr/bin/env python3
"""
Google Sheets OAuth 인증 스크립트 (1회 실행)

Windows에서 실행하여 브라우저로 인증 후 토큰 저장.
이후 danawa-reviews.py에서 자동으로 토큰 사용.

사용법 (PowerShell):
  python auth-sheets.py
"""

import os
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def main():
    # Windows용 경로
    home = os.path.expanduser('~')

    # WSL 경로 시도, 없으면 Windows 경로
    wsl_config = os.path.expanduser('~/.config/gspread')
    win_config = os.path.join(home, '.config', 'gspread')

    if os.path.exists(wsl_config):
        config_dir = wsl_config
    else:
        config_dir = win_config
        os.makedirs(config_dir, exist_ok=True)

    creds_path = os.path.join(config_dir, 'credentials.json')
    token_path = os.path.join(config_dir, 'authorized_user.json')

    print(f"📂 Config 디렉토리: {config_dir}")
    print(f"📄 Credentials: {creds_path}")
    print(f"🔑 Token 저장 위치: {token_path}")

    if not os.path.exists(creds_path):
        print(f"\n❌ credentials.json이 없습니다: {creds_path}")
        print("\n다음 내용으로 파일을 생성하세요:")
        print('''
{
    "installed": {
        "client_id": "YOUR_CLIENT_ID",
        "project_id": "YOUR_PROJECT",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "YOUR_CLIENT_SECRET",
        "redirect_uris": ["http://localhost"]
    }
}
''')
        return

    print("\n🚀 OAuth 인증을 시작합니다...")
    print("   브라우저가 열리면 Google 계정으로 로그인하세요.\n")

    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    creds = flow.run_local_server(port=0)

    # 토큰 저장
    with open(token_path, 'w') as token:
        token.write(creds.to_json())

    print(f"\n✅ 인증 완료! 토큰이 저장되었습니다.")
    print(f"   {token_path}")
    print("\n💡 이제 danawa-reviews.py --sheet 옵션을 사용할 수 있습니다.")

if __name__ == "__main__":
    main()
