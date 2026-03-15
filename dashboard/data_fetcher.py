"""
Gmail 매출 데이터 파싱 모듈

서원님이 보내는 매출 보고 메일을 조회하고 국가별 매출 데이터를 추출합니다.
"""

import sys
import re
import csv
import base64
from pathlib import Path
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

# GWS 인증 모듈 경로
sys.path.insert(0, str(Path(__file__).parent.parent / "00-system" / "02-scripts" / "gws"))
from gws_auth import get_service

DATA_DIR = Path(__file__).parent / "data"
SALES_CSV = DATA_DIR / "sales.csv"

# 매출 보고 메일 검색 조건 (필요시 조정)
GMAIL_QUERY = 'from:seowon subject:(매출 OR 보고 OR 일간 OR 주간 OR PayHere OR 정산)'
COUNTRY_KEYWORDS = {
    "일본": ["일본", "JP", "Japan", "日本"],
    "대만": ["대만", "TW", "Taiwan", "台湾", "台灣"],
    "중국": ["중국", "CN", "China", "中国"],
}


def fetch_sales_emails(days: int = 30, max_results: int = 50) -> list[dict]:
    """Gmail에서 매출 보고 메일을 조회합니다.

    Args:
        days: 최근 며칠간의 메일을 조회할지
        max_results: 최대 조회 수

    Returns:
        메일 목록 [{id, subject, date, body}, ...]
    """
    service = get_service("gmail")
    after_date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    query = f"{GMAIL_QUERY} after:{after_date}"

    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    emails = []
    for msg_meta in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_meta["id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        subject = headers.get("Subject", "")
        date_str = headers.get("Date", "")

        try:
            date = parsedate_to_datetime(date_str)
        except Exception:
            date = datetime.now()

        body = _extract_body(msg["payload"])

        emails.append({
            "id": msg_meta["id"],
            "subject": subject,
            "date": date,
            "body": body,
        })

    return sorted(emails, key=lambda x: x["date"])


def _extract_body(payload: dict) -> str:
    """메일 본문을 추출합니다."""
    body = ""

    if "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

    if "parts" in payload:
        for part in payload["parts"]:
            mime = part.get("mimeType", "")
            if mime == "text/plain" and part.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                break
            elif mime == "text/html" and part.get("body", {}).get("data") and not body:
                raw = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                body = re.sub(r"<[^>]+>", " ", raw)
            elif "parts" in part:
                body = _extract_body(part)
                if body:
                    break

    return body.strip()


def parse_sales_from_email(body: str, date: datetime) -> list[dict]:
    """메일 본문에서 국가별 매출 데이터를 추출합니다.

    다양한 형식을 지원:
    - "일본: 1,234,567원" 또는 "일본 1234567"
    - "JP: ¥123,456" 또는 "Japan: $1,234"
    - 테이블 형식 등

    Returns:
        [{date, country, sales}, ...]
    """
    records = []

    for country, keywords in COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            # 패턴: 키워드 뒤에 숫자 (통화 기호/쉼표/원 등 허용)
            patterns = [
                rf"{keyword}\s*[:\-=]\s*[￥¥₩$]?\s*([\d,]+)\s*(?:원|엔|円|NT\$|元)?",
                rf"{keyword}\s+[￥¥₩$]?\s*([\d,]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, body, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(",", "")
                    try:
                        amount = int(amount_str)
                        if amount > 0:
                            records.append({
                                "date": date.strftime("%Y-%m-%d"),
                                "country": country,
                                "sales": amount,
                            })
                    except ValueError:
                        continue
                    break
            if any(r["country"] == country for r in records):
                break

    return records


def fetch_and_save(days: int = 30) -> list[dict]:
    """Gmail에서 매출 데이터를 가져와 CSV로 저장합니다."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 기존 데이터 로드
    existing = load_sales_data()
    existing_dates = {(r["date"], r["country"]) for r in existing}

    # 새 데이터 파싱
    emails = fetch_sales_emails(days=days)
    new_records = []

    for email in emails:
        records = parse_sales_from_email(email["body"], email["date"])
        for r in records:
            key = (r["date"], r["country"])
            if key not in existing_dates:
                new_records.append(r)
                existing_dates.add(key)

    all_records = existing + new_records
    all_records.sort(key=lambda x: x["date"])

    # CSV 저장
    _save_csv(all_records)

    return all_records


def _save_csv(records: list[dict]):
    """매출 데이터를 CSV로 저장합니다."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SALES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "country", "sales"])
        writer.writeheader()
        writer.writerows(records)


def load_sales_data() -> list[dict]:
    """CSV에서 매출 데이터를 로드합니다."""
    if not SALES_CSV.exists():
        return []

    records = []
    with open(SALES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["sales"] = int(row["sales"])
            records.append(row)
    return records


def get_sample_data() -> list[dict]:
    """개발/데모용 샘플 데이터를 생성합니다."""
    import random
    random.seed(42)

    records = []
    base_date = datetime(2026, 2, 14)

    for i in range(30):
        date = base_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")

        # 일본: 가장 높은 매출
        jp_base = 850000 + random.randint(-100000, 150000)
        # 스파이크 시뮬레이션 (인플루언서 효과)
        if i in [7, 8, 9, 20, 21]:
            jp_base = int(jp_base * 1.6)

        # 대만: 중간 매출
        tw_base = 420000 + random.randint(-80000, 100000)
        if i in [12, 13, 14]:
            tw_base = int(tw_base * 1.5)

        # 중국: 성장 추세
        cn_base = 300000 + random.randint(-60000, 80000) + i * 5000
        if i in [18, 19]:
            cn_base = int(cn_base * 1.4)

        records.extend([
            {"date": date_str, "country": "일본", "sales": jp_base},
            {"date": date_str, "country": "대만", "sales": tw_base},
            {"date": date_str, "country": "중국", "sales": cn_base},
        ])

    return records


def add_manual_entry(date: str, country: str, sales: int):
    """수동으로 매출 데이터를 추가합니다."""
    records = load_sales_data()
    # 같은 날짜/국가 데이터가 있으면 업데이트
    updated = False
    for r in records:
        if r["date"] == date and r["country"] == country:
            r["sales"] = sales
            updated = True
            break
    if not updated:
        records.append({"date": date, "country": country, "sales": sales})

    records.sort(key=lambda x: x["date"])
    _save_csv(records)
    return records
