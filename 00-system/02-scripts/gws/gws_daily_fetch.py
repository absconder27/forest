#!/usr/bin/env python3
"""
Daily Note용 GWS 데이터 fetcher

오늘 일정(Calendar), 최근 메일(Gmail), 어제 우선순위를 가져와
마크다운 섹션으로 stdout 출력.

Usage:
    python3 gws_daily_fetch.py --date 2026-03-15 --workspace-root /path/to/workspace
"""

import argparse
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path

# 스크립트 디렉토리를 path에 추가
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from gws_auth import get_service

# --- Gmail 필터링 상수 ---
# 이 목록에 해당하는 발신자 주소 패턴은 그룹웨어/자동 알림으로 간주하여 제외
GMAIL_EXCLUDE_SENDER_PATTERNS = [
    "noreply",
    "no-reply",
    "notification",
    "notifications",
    "alert",
    "alerts",
    "mailer-daemon",
    "postmaster",
    "donotreply",
    "do-not-reply",
    "automated",
    "system@",
    "admin@",
]

# 제외할 발신자 도메인 (그룹웨어, 사내 시스템 등)
GMAIL_EXCLUDE_DOMAINS = [
    "accounts.google.com",
    "calendar-notification@google.com",
]

KST_OFFSET = "+09:00"
WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]


def fetch_calendar_events(date_str: str) -> tuple[str, str]:
    """Calendar API로 오늘 일정 + 향후 2-3일 일정을 가져옵니다.

    Returns:
        (schedule_table, upcoming_events) 마크다운 문자열 튜플
    """
    service = get_service("calendar")
    target_date = datetime.strptime(date_str, "%Y-%m-%d")

    # 오늘 일정
    time_min = f"{date_str}T00:00:00{KST_OFFSET}"
    time_max = f"{date_str}T23:59:59{KST_OFFSET}"

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            timeZone="Asia/Seoul",
        )
        .execute()
    )
    events = events_result.get("items", [])

    # 스케줄 테이블 생성
    table_rows = []
    for event in events:
        summary = event.get("summary", "(제목 없음)")
        start = event.get("start", {})
        end = event.get("end", {})

        # 종일 이벤트
        if "date" in start:
            time_range = "종일"
        else:
            start_dt = _parse_datetime(start.get("dateTime", ""))
            end_dt = _parse_datetime(end.get("dateTime", ""))
            time_range = f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"

        # 장소 또는 Meet 링크
        location = event.get("location", "")
        hangout = event.get("hangoutLink", "")
        if hangout:
            summary = f"{summary} ([Meet]({hangout}))"
        elif location:
            summary = f"{summary} ({location})"

        table_rows.append(f"| {time_range} | {summary} | 예정 |")

    schedule_table = "\n".join(table_rows) if table_rows else "| | (일정 없음) | |"

    # 향후 3일 일정
    future_start = target_date + timedelta(days=1)
    future_end = target_date + timedelta(days=4)
    future_min = f"{future_start.strftime('%Y-%m-%d')}T00:00:00{KST_OFFSET}"
    future_max = f"{future_end.strftime('%Y-%m-%d')}T23:59:59{KST_OFFSET}"

    future_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=future_min,
            timeMax=future_max,
            singleEvents=True,
            orderBy="startTime",
            timeZone="Asia/Seoul",
        )
        .execute()
    )
    future_events = future_result.get("items", [])

    upcoming_lines = []
    for event in future_events:
        summary = event.get("summary", "(제목 없음)")
        start = event.get("start", {})

        if "date" in start:
            ev_date = datetime.strptime(start["date"], "%Y-%m-%d")
            weekday = WEEKDAY_KO[ev_date.weekday()]
            date_str_fmt = f"{ev_date.month}/{ev_date.day}({weekday})"
            time_str = "종일"
        else:
            ev_dt = _parse_datetime(start.get("dateTime", ""))
            weekday = WEEKDAY_KO[ev_dt.weekday()]
            date_str_fmt = f"{ev_dt.month}/{ev_dt.day}({weekday})"
            time_str = ev_dt.strftime("%H:%M")

        # Meet 링크
        hangout = event.get("hangoutLink", "")
        if hangout:
            summary = f"{summary} ([Meet]({hangout}))"

        upcoming_lines.append(f"- {date_str_fmt} {time_str} - {summary}")

    upcoming_events = "\n".join(upcoming_lines) if upcoming_lines else "- (예정된 일정 없음)"

    return schedule_table, upcoming_events


def fetch_gmail_summary(hours: int = 48) -> str:
    """Gmail API로 최근 메일 요약을 가져옵니다.

    Args:
        hours: 몇 시간 이내 메일을 가져올지

    Returns:
        마크다운 불릿 리스트 문자열
    """
    service = get_service("gmail")

    # newer_than 쿼리
    days = max(1, hours // 24)
    query = f"newer_than:{days}d"

    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=15)
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        return "- (새 메일 없음)"

    mail_lines = []
    important_lines = []

    for msg_meta in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_meta["id"], format="metadata",
                 metadataHeaders=["From", "Subject", "Date"])
            .execute()
        )

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        from_raw = headers.get("From", "")
        subject = headers.get("Subject", "(제목 없음)")
        date_str = headers.get("Date", "")

        # 발신자 파싱
        sender_name, sender_email = _parse_sender(from_raw)

        # 그룹웨어 필터링
        if _is_excluded_sender(sender_email):
            continue

        # 날짜 포맷
        date_display = _format_mail_date(date_str)

        # 중요/스타 메일 확인
        label_ids = msg.get("labelIds", [])
        is_important = "IMPORTANT" in label_ids or "STARRED" in label_ids

        line = f"- {sender_name} - {subject} ({date_display})"
        if is_important:
            important_lines.append(f"- **[중요]** {sender_name} - {subject} ({date_display})")
        else:
            mail_lines.append(line)

    all_lines = important_lines + mail_lines
    return "\n".join(all_lines) if all_lines else "- (새 메일 없음)"


def fetch_yesterday_priorities(workspace_root: str, yesterday_str: str) -> str:
    """어제 daily note에서 '내일 우선순위' 섹션을 파싱합니다.

    Returns:
        체크박스 리스트 마크다운 문자열
    """
    yesterday_path = Path(workspace_root) / "40-personal" / "41-daily" / f"{yesterday_str}.md"

    if not yesterday_path.exists():
        return "- [ ]\n- [ ]\n- [ ]"

    content = yesterday_path.read_text(encoding="utf-8")

    # "내일 우선순위" 섹션 찾기
    lines = content.split("\n")
    in_section = False
    priorities = []

    for line in lines:
        if "내일 우선순위" in line:
            in_section = True
            continue
        if in_section:
            # 다음 섹션 헤딩(## 또는 ---)을 만나면 종료
            if line.startswith("#") or line.startswith("---"):
                break
            stripped = line.strip()
            if stripped.startswith("-") and stripped != "-":
                # 기존 내용을 체크박스로 변환
                item = stripped.lstrip("- ").strip()
                # 이미 체크박스면 그대로
                if item.startswith("[ ]") or item.startswith("[x]"):
                    priorities.append(f"- {item}")
                else:
                    priorities.append(f"- [ ] {item}")

    if not priorities:
        return "- [ ]\n- [ ]\n- [ ]"

    return "\n".join(priorities)


# --- 헬퍼 함수 ---

def _parse_datetime(dt_str: str) -> datetime:
    """ISO 형식 datetime 문자열을 파싱합니다."""
    # 다양한 형식 대응
    for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"]:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    # fallback: fromisoformat
    return datetime.fromisoformat(dt_str)


def _parse_sender(from_header: str) -> tuple[str, str]:
    """From 헤더에서 이름과 이메일을 분리합니다.

    예: '"김민영" <kim@example.com>' → ('김민영', 'kim@example.com')
    """
    match = re.match(r'^"?([^"<]*)"?\s*<?([^>]*)>?$', from_header.strip())
    if match:
        name = match.group(1).strip()
        email = match.group(2).strip().lower()
        if not name:
            name = email.split("@")[0]
        return name, email
    return from_header.strip(), from_header.strip().lower()


def _is_excluded_sender(email: str) -> bool:
    """그룹웨어/자동 알림 발신자인지 확인합니다."""
    email_lower = email.lower()

    for pattern in GMAIL_EXCLUDE_SENDER_PATTERNS:
        if pattern in email_lower:
            return True

    for domain in GMAIL_EXCLUDE_DOMAINS:
        if domain in email_lower:
            return True

    return False


def _format_mail_date(date_str: str) -> str:
    """메일 Date 헤더를 간단한 형식으로 변환합니다."""
    if not date_str:
        return ""
    try:
        # RFC 2822 형식 파싱
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return f"{dt.month}/{dt.day}"
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Daily Note용 GWS 데이터 fetcher")
    parser.add_argument("--date", required=True, help="대상 날짜 (YYYY-MM-DD)")
    parser.add_argument("--workspace-root", required=True, help="워크스페이스 루트 경로")
    args = parser.parse_args()

    target_date = datetime.strptime(args.date, "%Y-%m-%d")
    yesterday = (target_date - timedelta(days=1)).strftime("%Y-%m-%d")

    # 각 API 독립적으로 실행 - 하나 실패해도 나머지 정상 출력
    schedule_table = "| | (일정 로드 실패) | |"
    upcoming_events = "- (일정 로드 실패)"
    gmail_summary = "- (메일 확인 필요)"
    top3_tasks = "- [ ]\n- [ ]\n- [ ]"

    # Calendar
    try:
        schedule_table, upcoming_events = fetch_calendar_events(args.date)
    except Exception as e:
        print(f"[Calendar 오류] {e}", file=sys.stderr)

    # Gmail
    try:
        gmail_summary = fetch_gmail_summary(hours=48)
    except Exception as e:
        print(f"[Gmail 오류] {e}", file=sys.stderr)

    # 어제 우선순위
    try:
        top3_tasks = fetch_yesterday_priorities(args.workspace_root, yesterday)
    except Exception as e:
        print(f"[Yesterday priorities 오류] {e}", file=sys.stderr)

    # 구분자 형식으로 출력
    print(f"===SCHEDULE_TABLE===\n{schedule_table}")
    print(f"===UPCOMING_EVENTS===\n{upcoming_events}")
    print(f"===GMAIL_SUMMARY===\n{gmail_summary}")
    print(f"===TOP3_TASKS===\n{top3_tasks}")


if __name__ == "__main__":
    main()
