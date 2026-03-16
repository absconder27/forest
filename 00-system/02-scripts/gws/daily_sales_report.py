"""
뉴믹스 일간 매출 보고서 자동 생성

데이터 소스:
1. [뉴믹스] 일간 보고 지표 템플릿 → 채널별 매출/목표 (Sheets API, 전체 정밀도)
2. (뉴마센) 데일리 국가별 매출 → 외국인 국적별 비중

사용법:
    python3 daily_sales_report.py                    # 어제 기준 리포트 생성
    python3 daily_sales_report.py --date 2026-03-15  # 특정 날짜 리포트
    python3 daily_sales_report.py --send-email       # 생성 + 이메일 발송
"""

import sys
import json
import argparse
import base64
from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, str(Path(__file__).parent))
from gws_auth import get_service

# sheets_fetcher에서 국가별 매출만 임포트
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "dashboard"))
from sheets_fetcher import fetch_country_sales

DAILY_REPORT_ID = "1r4MOXIXJEL9qdO5FRaJfhmQV7xxqsB6_1Q5y33cSh-8"
WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

# Excel serial date epoch (1899-12-30)
EXCEL_EPOCH = datetime(1899, 12, 30)


def _serial_to_date(serial: int) -> datetime:
    """Excel serial number → datetime"""
    return EXCEL_EPOCH + timedelta(days=serial)


def _safe_float(val) -> float:
    """안전하게 float 변환"""
    if val is None or val == "" or isinstance(val, str):
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _get_tab_name(target_date: datetime) -> str:
    """월별 탭 이름 생성 (예: '26년 3월')"""
    year_short = str(target_date.year)[2:]
    return f"{year_short}년 {target_date.month}월"


def _parse_store_dates(date_row: list, year: int) -> list:
    """오프라인 탭의 날짜 행 파싱 ('02/14(토)' → '2026-02-14')"""
    import re
    dates = []
    for val in date_row:
        if not val or not isinstance(val, str):
            dates.append("")
            continue
        m = re.match(r"(\d{2})/(\d{2})", str(val))
        if m:
            month, day = int(m.group(1)), int(m.group(2))
            # 월이 1-2월이면 연도 그대로, 아니면 연도 그대로
            dates.append(datetime(year, month, day).strftime("%Y-%m-%d"))
        else:
            dates.append("")
    return dates


def fetch_store_detail(target_date: datetime) -> dict:
    """오프라인(성수점/북촌점) 탭에서 건단가/결제건수를 가져옵니다.

    Returns:
        {
            "성수점": {"dates": [...], "건단가": [...], "결제건수": [...]},
            "북촌점": {"dates": [...], "건단가": [...], "결제건수": [...]},
        }
    """
    sheets = get_service("sheets")
    year = target_date.year
    result = {}

    for tab, store_name in [("오프라인(성수점)", "성수점"), ("오프라인(북촌점)", "북촌점")]:
        try:
            data = sheets.spreadsheets().values().get(
                spreadsheetId=DAILY_REPORT_ID,
                range=f"'{tab}'!A52:BQ55",
                valueRenderOption="UNFORMATTED_VALUE",
            ).execute()
            rows = data.get("values", [])

            # Row 52: 날짜, Row 53: 건단가, Row 54: 결제건수
            date_row = rows[0] if len(rows) > 0 else []
            price_row = rows[1] if len(rows) > 1 else []
            count_row = rows[2] if len(rows) > 2 else []

            dates = _parse_store_dates(date_row[2:], year)
            prices = [_safe_float(v) for v in price_row[2:]]
            counts = [int(_safe_float(v)) for v in count_row[2:]]

            result[store_name] = {
                "dates": dates,
                "건단가": prices,
                "결제건수": counts,
            }
        except Exception as e:
            print(f"[경고] {store_name} 건단가 조회 실패: {e}", file=sys.stderr)
            result[store_name] = {"dates": [], "건단가": [], "결제건수": []}

    return result


def fetch_online_detail(target_date: datetime) -> dict:
    """온라인(네이버 스마트스토어) 탭에서 ROAS/광고비를 가져옵니다.

    Returns:
        {"dates": [...], "일매출": [...], "roas": [...], "광고비": [...]}
    """
    sheets = get_service("sheets")
    year = target_date.year

    try:
        data = sheets.spreadsheets().values().get(
            spreadsheetId=DAILY_REPORT_ID,
            range="'온라인 (네이버 스마트스토어)'!A25:BQ29",
            valueRenderOption="UNFORMATTED_VALUE",
        ).execute()
        rows = data.get("values", [])

        # Row 25: 날짜, Row 26: 일매출, Row 27: ROAS, Row 28: 광고비
        date_row = rows[0] if len(rows) > 0 else []
        sales_row = rows[1] if len(rows) > 1 else []
        roas_row = rows[2] if len(rows) > 2 else []
        ad_row = rows[3] if len(rows) > 3 else []

        dates = _parse_store_dates(date_row[2:], year)
        sales = [_safe_float(v) for v in sales_row[2:]]
        roas = [_safe_float(v) for v in roas_row[2:]]
        ads = [_safe_float(v) for v in ad_row[2:]]

        return {"dates": dates, "일매출": sales, "roas": roas, "광고비": ads}
    except Exception as e:
        print(f"[경고] 온라인 ROAS 조회 실패: {e}", file=sys.stderr)
        return {"dates": [], "일매출": [], "roas": [], "광고비": []}


def fetch_weather(target_date: datetime) -> Optional[str]:
    """Open-Meteo API로 서울 날씨를 가져옵니다 (과거+예보 모두 지원)."""
    import urllib.request
    import json as json_mod

    WMO_KR = {
        0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림",
        45: "안개", 48: "안개",
        51: "이슬비", 53: "이슬비", 55: "이슬비",
        61: "비", 63: "비", 65: "폭우",
        71: "눈", 73: "눈", 75: "폭설",
        80: "소나기", 81: "소나기", 82: "소나기",
        95: "뇌우", 96: "우박", 99: "우박",
    }

    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=37.5665&longitude=126.9780"
            "&daily=temperature_2m_max,temperature_2m_min,weathercode"
            "&timezone=Asia/Seoul&past_days=7"
        )
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=10)
        data = json_mod.loads(resp.read().decode("utf-8"))

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        maxs = daily.get("temperature_2m_max", [])
        mins = daily.get("temperature_2m_min", [])
        codes = daily.get("weathercode", [])

        date_str = target_date.strftime("%Y-%m-%d")
        for i, d in enumerate(dates):
            if d == date_str:
                desc = WMO_KR.get(codes[i], f"코드{codes[i]}")
                return f"{desc} (최고 {maxs[i]}° / 최저 {mins[i]}°)"

        return None
    except Exception as e:
        print(f"[경고] 날씨 조회 실패: {e}", file=sys.stderr)
        return None


WEEKLY_REPORT_DOC_ID = "11qqNS1TGhWgxN6W6L0m2Hto6XD4cIH44ORw7dhjC-TI"


def fetch_weekly_foreign_breakdown() -> dict:
    """서원님 주간보고 구글독스에서 최신 외국인 매출 비중을 가져옵니다.

    Returns:
        {
            "성수": {"일본": "60%", "일본_전주비": "-2%", "대만": "22%", "대만_전주비": "-%"},
            "북촌": {"일본": "56%", ...},
        }
    """
    import re

    try:
        docs = get_service("docs")
        doc = docs.documents().get(documentId=WEEKLY_REPORT_DOC_ID).execute()

        content = doc.get("body", {}).get("content", [])
        full_text = ""
        for elem in content:
            if "paragraph" in elem:
                for run in elem["paragraph"].get("elements", []):
                    if "textRun" in run:
                        full_text += run["textRun"]["content"]

        # 주간 블록 분리 (최신이 맨 위)
        blocks = re.split(r"(?=1\. 전체 매출액)", full_text)
        blocks = [b.strip() for b in blocks if b.strip()]

        if not blocks:
            return {"성수": {}, "북촌": {}}

        # 전주비가 모두 채워진 블록 사용 (최신 블록이 미완성일 수 있음)
        latest = None
        for block in blocks:
            # 성수 일본 전주비 숫자가 있는지 확인
            check = re.search(
                r"5\.\s*성수점.*?일본\s*\d+%\(전주비\s*[+\-]\d+%\).*?대만\s*\d+%\(전주비\s*[+\-]\d+%\)",
                block, re.DOTALL,
            )
            if check:
                latest = block
                break

        if latest is None:
            latest = blocks[0]  # fallback: 최신 블록

        result = {}

        for section_num, store_key in [("5", "성수"), ("6", "북촌")]:
            pattern = (
                rf"{section_num}\.\s*{store_key}점.*?"
                r"일본\s*(\d+)%\(전주비\s*([+\-]?\d*)%?\).*?"
                r"대만\s*(\d+)%\(전주비\s*([+\-]?\d*)%?\)"
            )
            match = re.search(pattern, latest, re.DOTALL)
            if match:
                jp_pct = int(match.group(1))
                jp_diff = match.group(2)
                jp_diff = int(jp_diff) if jp_diff and jp_diff not in ("", "-", "+") else None
                tw_pct = int(match.group(3))
                tw_diff = match.group(4)
                tw_diff = int(tw_diff) if tw_diff and tw_diff not in ("", "-", "+") else None

                result[store_key] = {
                    "일본_pct": jp_pct,
                    "일본_diff": jp_diff,
                    "대만_pct": tw_pct,
                    "대만_diff": tw_diff,
                }
            else:
                result[store_key] = {}

        return result
    except Exception as e:
        print(f"[경고] 주간보고 외국인 비중 조회 실패: {e}", file=sys.stderr)
        return {"성수": {}, "북촌": {}}


def fetch_monthly_data_api(target_date: datetime) -> dict:
    """Sheets API로 UNFORMATTED_VALUE 데이터를 가져옵니다 (전체 정밀도).

    Returns:
        {
            "dates": ["2026-03-01", ...],
            "targets": {"성수점": [12.0, 10.0, ...], ...},
            "actuals": {"성수점": [16.0065, 8.1471, ...], ...},
            "monthly_targets": {"성수점": 440.0, ...},
        }
    """
    sheets = get_service("sheets")
    tab_name = _get_tab_name(target_date)

    # 전체 데이터 가져오기 (row 1~25, col A~AH)
    data = sheets.spreadsheets().values().get(
        spreadsheetId=DAILY_REPORT_ID,
        range=f"'{tab_name}'!A1:AH25",
        valueRenderOption="UNFORMATTED_VALUE",
    ).execute()
    rows = data.get("values", [])

    year = target_date.year

    # Row 5 (index 5): 날짜 행 — Excel serial numbers
    date_row = rows[5] if len(rows) > 5 else []
    dates = []
    for i in range(3, len(date_row)):
        val = date_row[i]
        if isinstance(val, (int, float)) and val > 40000:
            dt = _serial_to_date(int(val))
            dates.append(dt.strftime("%Y-%m-%d"))
        else:
            dates.append("")

    # 채널별 목표 (rows 6-11)
    channel_rows_target = {6: "성수점", 7: "북촌점", 8: "네이버", 9: "쿠팡", 10: "컬리", 11: "기타"}
    channel_rows_actual = {15: "성수점", 16: "북촌점", 17: "네이버", 18: "쿠팡", 19: "컬리", 20: "기타"}

    targets = {}
    monthly_targets = {}
    for row_idx, channel in channel_rows_target.items():
        if row_idx >= len(rows):
            continue
        row = rows[row_idx]
        monthly_targets[channel] = _safe_float(row[1]) if len(row) > 1 else 0
        vals = [_safe_float(row[i + 3]) if i + 3 < len(row) else 0 for i in range(len(dates))]
        targets[channel] = vals

    actuals = {}
    for row_idx, channel in channel_rows_actual.items():
        if row_idx >= len(rows):
            continue
        row = rows[row_idx]
        vals = [_safe_float(row[i + 3]) if i + 3 < len(row) else 0 for i in range(len(dates))]
        actuals[channel] = vals

    return {
        "dates": dates,
        "targets": targets,
        "actuals": actuals,
        "monthly_targets": monthly_targets,
    }


def compute_report(target_date: datetime) -> dict:
    """리포트에 필요한 모든 데이터를 계산합니다."""
    date_str = target_date.strftime("%Y-%m-%d")
    weekday = WEEKDAY_KR[target_date.weekday()]
    last_week = target_date - timedelta(days=7)
    last_week_str = last_week.strftime("%Y-%m-%d")

    # 1. 월별 채널 데이터 (Sheets API, 전체 정밀도)
    monthly = fetch_monthly_data_api(target_date)
    dates = monthly["dates"]

    # 날짜 인덱스 찾기
    day_idx = None
    for i, d in enumerate(dates):
        if d == date_str:
            day_idx = i
            break

    if day_idx is None:
        raise ValueError(f"{date_str} 데이터를 찾을 수 없습니다. 시트에 해당 날짜가 없습니다.")

    # 전주 같은 요일 인덱스
    last_week_idx = None
    for i, d in enumerate(dates):
        if d == last_week_str:
            last_week_idx = i
            break

    # 2. 채널별 당일 매출 & 전주비
    channels = ["성수점", "북촌점", "네이버", "쿠팡", "컬리", "기타"]
    channel_data = {}

    for ch in channels:
        actuals_list = monthly["actuals"].get(ch, [])
        targets_list = monthly["targets"].get(ch, [])

        today_sales = actuals_list[day_idx] if day_idx < len(actuals_list) else 0
        today_target = targets_list[day_idx] if day_idx < len(targets_list) else 0

        last_week_sales = None
        if last_week_idx is not None:
            last_week_sales = actuals_list[last_week_idx] if last_week_idx < len(actuals_list) else 0

        # MTD 누적
        mtd_actual = sum(actuals_list[:day_idx + 1])
        mtd_target = sum(targets_list[:day_idx + 1])
        monthly_target = monthly["monthly_targets"].get(ch, 0)

        channel_data[ch] = {
            "sales": today_sales,
            "target": today_target,
            "last_week_sales": last_week_sales,
            "mtd_actual": mtd_actual,
            "mtd_target": mtd_target,
            "monthly_target": monthly_target,
        }

    # 3. 건단가/결제건수 (오프라인 탭)
    store_detail = fetch_store_detail(target_date)
    for store_name in ["성수점", "북촌점"]:
        detail = store_detail.get(store_name, {})
        detail_dates = detail.get("dates", [])
        prices = detail.get("건단가", [])
        counts = detail.get("결제건수", [])

        # 해당 날짜 인덱스 찾기
        detail_idx = None
        for i, d in enumerate(detail_dates):
            if d == date_str:
                detail_idx = i
                break

        lw_detail_idx = None
        for i, d in enumerate(detail_dates):
            if d == last_week_str:
                lw_detail_idx = i
                break

        if detail_idx is not None:
            channel_data[store_name]["건단가"] = int(prices[detail_idx]) if detail_idx < len(prices) else None
            channel_data[store_name]["결제건수"] = counts[detail_idx] if detail_idx < len(counts) else None
        else:
            channel_data[store_name]["건단가"] = None
            channel_data[store_name]["결제건수"] = None

        if lw_detail_idx is not None:
            channel_data[store_name]["건단가_전주"] = int(prices[lw_detail_idx]) if lw_detail_idx < len(prices) else None
            channel_data[store_name]["결제건수_전주"] = counts[lw_detail_idx] if lw_detail_idx < len(counts) else None
        else:
            channel_data[store_name]["건단가_전주"] = None
            channel_data[store_name]["결제건수_전주"] = None

    # 4. 롯데면세점 (Row 27: 달러, Row 28: 원화 백만)
    lotte_usd = None
    lotte_krw = None
    try:
        sheets_svc = get_service("sheets")
        lotte_data = sheets_svc.spreadsheets().values().get(
            spreadsheetId=DAILY_REPORT_ID,
            range=f"'{_get_tab_name(target_date)}'!A27:AH29",
            valueRenderOption="UNFORMATTED_VALUE",
        ).execute()
        lotte_rows = lotte_data.get("values", [])
        if len(lotte_rows) >= 2 and day_idx is not None:
            col = day_idx + 3
            usd_row = lotte_rows[0]
            krw_row = lotte_rows[1]
            if col < len(usd_row) and usd_row[col]:
                lotte_usd = int(_safe_float(usd_row[col]))
            if col < len(krw_row) and krw_row[col]:
                lotte_krw = round(_safe_float(krw_row[col]), 1)
    except Exception as e:
        print(f"[경고] 롯데면세 조회 실패: {e}", file=sys.stderr)

    # 5. 국가별 매출 비중 (서원님 주간보고 구글독스에서 직접 가져옴)
    country_data = fetch_weekly_foreign_breakdown()
    last_week_country = {}

    # 5. ROAS (온라인 탭)
    online_detail = fetch_online_detail(target_date)
    online_dates = online_detail.get("dates", [])
    roas_list = online_detail.get("roas", [])

    roas_idx = None
    for i, d in enumerate(online_dates):
        if d == date_str:
            roas_idx = i
            break

    roas_value = None
    if roas_idx is not None and roas_idx < len(roas_list):
        roas_value = roas_list[roas_idx]

    # 6. 날씨
    weather = fetch_weather(target_date)

    # 7. 합계 계산
    total_sales = sum(cd["sales"] for cd in channel_data.values())
    total_target = sum(cd["target"] for cd in channel_data.values())
    total_mtd_actual = sum(cd["mtd_actual"] for cd in channel_data.values())
    total_monthly_target = sum(cd["monthly_target"] for cd in channel_data.values())

    days_in_month = (target_date.replace(month=target_date.month % 12 + 1, day=1) - timedelta(days=1)).day
    day_of_month = target_date.day
    remaining_days = days_in_month - day_of_month
    remaining_target = total_monthly_target - total_mtd_actual
    daily_needed = remaining_target / remaining_days if remaining_days > 0 else 0

    progress_rate = (total_mtd_actual / total_monthly_target * 100) if total_monthly_target > 0 else 0
    expected_rate = (day_of_month / days_in_month * 100)

    return {
        "date": target_date,
        "date_str": date_str,
        "weekday": weekday,
        "channels": channel_data,
        "country": country_data,
        "last_week_country": last_week_country,
        "roas": roas_value,
        "weather": weather,
        "lotte_usd": lotte_usd,
        "lotte_krw": lotte_krw,
        "total": {
            "sales": total_sales,
            "target": total_target,
            "mtd_actual": total_mtd_actual,
            "monthly_target": total_monthly_target,
            "progress_rate": progress_rate,
            "expected_rate": expected_rate,
            "remaining": remaining_target,
            "daily_needed": daily_needed,
            "day_of_month": day_of_month,
            "days_in_month": days_in_month,
        },
    }


def _fmt_won(val_million: float) -> str:
    """백만원 → 원 단위 포맷 (전체 정밀도, 예: 20.6968 → 20,696,800원)"""
    won = round(val_million * 1_000_000)
    return f"{won:,}원"


def _fmt_diff_won(current: float, previous: Optional[float]) -> str:
    """전주비 포맷 (예: (전주비 +2,454,000원))"""
    if previous is None or previous == 0:
        return ""
    diff = current - previous
    diff_won = round(diff * 1_000_000)
    sign = "+" if diff >= 0 else ""
    return f" (전주비 {sign}{diff_won:,}원)"


def _country_breakdown_from_weekly(store_data: dict) -> str:
    """서원님 주간보고 데이터로 외국인 매출 비중 텍스트 생성
    예: ㄴ 일본 62%(전주비 +11%), 대만 22%(전주비 -9%)
    """
    if not store_data:
        return ""

    parts = []
    for country in ["일본", "대만"]:
        pct_key = f"{country}_pct"
        diff_key = f"{country}_diff"
        if pct_key not in store_data:
            continue
        pct = store_data[pct_key]
        diff = store_data.get(diff_key)
        if diff is not None:
            sign = "+" if diff >= 0 else ""
            parts.append(f"{country} {pct}%(전주비 {sign}{diff}%)")
        else:
            parts.append(f"{country} {pct}%")

    if not parts:
        return ""

    return "ㄴ " + ", ".join(parts)


def format_report_text(data: dict) -> str:
    """실제 이메일 양식에 맞춘 본문 텍스트를 생성합니다."""
    d = data["date"]
    date_display = f"{d.month}/{d.day}({data['weekday']})"

    lines = []
    lines.append("안녕하세요, 김규림입니다.")
    lines.append(f"{date_display} 뉴믹스 일간 매출 공유드립니다.")
    lines.append("")
    weather = data.get("weather")
    if weather:
        lines.append(f"날씨: {weather}")
    else:
        lines.append("날씨: (수동 입력)")
    lotte_usd = data.get("lotte_usd")
    lotte_krw = data.get("lotte_krw")
    if lotte_usd and lotte_krw:
        lines.append("특이사항")
        lines.append(f"   롯데면세점 명동 일매출 {lotte_usd:,}불 (한화 약 {lotte_krw}백만)")
    else:
        lines.append("특이사항")
        lines.append("   (수동 입력)")
    lines.append("")

    # ── 그래프 1: 매출 요약 ──
    lines.append("(그래프)")
    lines.append("")

    lines.append("[국내 온라인 + 성수점 / 북촌점 매출]")
    lines.append("")

    # ── 그래프 2: 온라인+오프라인 종합 ──
    lines.append("(그래프)")
    lines.append("")

    # ── 1. 국내 온라인 ──
    online_channels = ["네이버", "쿠팡", "컬리"]
    online_total = sum(data["channels"][ch]["sales"] for ch in online_channels)
    online_lw = None
    if all(data["channels"][ch]["last_week_sales"] is not None for ch in online_channels):
        online_lw = sum(data["channels"][ch]["last_week_sales"] for ch in online_channels)

    lines.append("1. 국내 온라인")
    lines.append(f"매출: {_fmt_won(online_total)}")
    roas = data.get("roas")
    if roas is not None and roas > 0:
        lines.append(f"ROAS: {round(roas * 100)}%")
    else:
        lines.append("ROAS: (수동 입력)")

    # ── 그래프 3: 온라인 상세 ──
    lines.append("(그래프)")
    lines.append("")

    # ── 2. 오프라인 ──
    lines.append("2. 오프라인")
    lines.append("")

    for store_name, store_key in [("성수점", "성수"), ("북촌점", "북촌")]:
        ch = data["channels"][store_name]
        lines.append(f"[{store_name}]")
        lines.append(f"매출: {_fmt_won(ch['sales'])}{_fmt_diff_won(ch['sales'], ch['last_week_sales'])}")

        # 건단가
        price = ch.get("건단가")
        price_lw = ch.get("건단가_전주")
        if price is not None:
            price_diff = ""
            if price_lw is not None and price_lw > 0:
                diff = price - price_lw
                sign = "+" if diff >= 0 else ""
                price_diff = f" (전주비 {sign}{diff:,}원)"
            lines.append(f"건단가: {price:,}원{price_diff}")
        else:
            lines.append("건단가: (수동 입력)")

        # 결제건수
        count = ch.get("결제건수")
        count_lw = ch.get("결제건수_전주")
        if count is not None:
            count_diff = ""
            if count_lw is not None and count_lw > 0:
                diff = count - count_lw
                sign = "+" if diff >= 0 else ""
                count_diff = f" (전주비 {sign}{diff:,}건)"
            lines.append(f"결제건수: {count:,}건{count_diff}")
        else:
            lines.append("결제건수: (수동 입력)")

        # 외국인 비중 (서원님 주간보고)
        country_line = _country_breakdown_from_weekly(
            data["country"].get(store_key, {})
        )
        if country_line:
            lines.append("지난주 외국인 매출 비중: 99%")
            lines.append(country_line)

        # ── 그래프: 매장별 상세 ──
        lines.append("(그래프)")
        lines.append("(그래프)")
        lines.append("")
        lines.append("")

    lines.append("")
    lines.append("감사합니다.")
    lines.append("김규림 드림")

    return "\n".join(lines)


def format_report_html(data: dict) -> str:
    """Gmail 기본 작성 양식에 맞춘 HTML을 생성합니다."""
    import html as html_mod

    S = 'style="font-size:small;color:rgb(34,34,34)"'  # Gmail default
    d = data["date"]
    date_display = f"{d.month}/{d.day}({data['weekday']})"

    parts = []
    parts.append(f'<div dir="ltr">')
    parts.append(f'<span {S}>안녕하세요, 김규림입니다.</span><br>')
    parts.append(f'<span {S}>{date_display} 뉴믹스 일간 매출 공유드립니다.</span><br>')

    # ── 날씨 + 특이사항 (불릿) ──
    weather = data.get("weather")
    weather_text = weather if weather else "(수동 입력)"

    lotte_usd = data.get("lotte_usd")
    lotte_krw = data.get("lotte_krw")

    parts.append('<ul>')
    parts.append(f'<li {S}>날씨: {html_mod.escape(weather_text)}</li>')
    if lotte_usd and lotte_krw:
        parts.append(f'<li {S}>특이사항<ul><li {S}>롯데면세점 명동 일매출 {lotte_usd:,}불 (한화 약 {lotte_krw}백만)</li></ul></li>')
    else:
        parts.append(f'<li {S}>특이사항<ul><li {S}>(수동 입력)</li></ul></li>')
    parts.append('</ul>')

    # ── 그래프 ──
    parts.append(f'<span {S}>(그래프)</span><br><br>')

    # ── [국내 온라인 + 성수점 / 북촌점 매출] ──
    parts.append(f'<b {S}>[국내 온라인 + 성수점 / 북촌점 매출]</b><br><br>')
    parts.append(f'<span {S}>(그래프)</span><br><br>')

    # ── 1. 국내 온라인 ──
    online_channels = ["네이버", "쿠팡", "컬리"]
    online_total = sum(data["channels"][ch]["sales"] for ch in online_channels)

    parts.append(f'<b {S}>1. 국내 온라인</b><br>')
    parts.append('<ul>')
    parts.append(f'<li {S}>매출: {_fmt_won(online_total)}</li>')
    roas = data.get("roas")
    if roas is not None and roas > 0:
        parts.append(f'<li {S}>ROAS: {round(roas * 100)}%</li>')
    else:
        parts.append(f'<li {S}>ROAS: (수동 입력)</li>')
    parts.append('</ul>')
    parts.append(f'<span {S}>(그래프)</span><br><br>')

    # ── 2. 오프라인 ──
    parts.append(f'<b {S}>2. 오프라인</b><br><br>')

    for store_name, store_key in [("성수점", "성수"), ("북촌점", "북촌")]:
        ch = data["channels"][store_name]
        parts.append(f'<b {S}>[{store_name}]</b><br>')
        parts.append('<ul>')

        # 매출
        parts.append(f'<li {S}>매출: {_fmt_won(ch["sales"])}{_fmt_diff_won(ch["sales"], ch["last_week_sales"])}</li>')

        # 건단가
        price = ch.get("건단가")
        price_lw = ch.get("건단가_전주")
        if price is not None:
            price_diff = ""
            if price_lw is not None and price_lw > 0:
                diff = price - price_lw
                sign = "+" if diff >= 0 else ""
                price_diff = f" (전주비 {sign}{diff:,}원)"
            parts.append(f'<li {S}>건단가: {price:,}원{price_diff}</li>')

        # 결제건수
        count = ch.get("결제건수")
        count_lw = ch.get("결제건수_전주")
        if count is not None:
            count_diff = ""
            if count_lw is not None and count_lw > 0:
                diff = count - count_lw
                sign = "+" if diff >= 0 else ""
                count_diff = f" (전주비 {sign}{diff:,}건)"
            parts.append(f'<li {S}>결제건수: {count:,}건{count_diff}</li>')

        # 외국인 비중 (서원님 주간보고)
        country_line = _country_breakdown_from_weekly(
            data["country"].get(store_key, {})
        )
        if country_line:
            parts.append(f'<li {S}>지난주 외국인 매출 비중: 99%<br>')
            parts.append(f'<span {S}>&nbsp;&nbsp;{html_mod.escape(country_line)}</span></li>')

        parts.append('</ul>')
        parts.append(f'<span {S}>(그래프)</span><br>')
        parts.append(f'<span {S}>(그래프)</span><br><br><br>')

    parts.append(f'<span {S}>감사합니다.</span><br>')
    parts.append(f'<span {S}>김규림 드림</span><br>')

    # ── 서명 ──
    parts.append('<br>')
    parts.append('<div style="color:rgb(102,102,102);font-size:small;border-top:1px solid rgb(221,221,221);padding-top:10px">')
    parts.append('<b>김규림</b> Forest Kim<br>')
    parts.append('Creative Director, Grandeclip FnB Korea LLC.<br>')
    parts.append('<b>+82 10 9970 5676</b><br>')
    parts.append('서울특별시 종로구 창덕궁1길 40 (우.03057)<br>')
    parts.append('Grandeclip fnb Korea LLC, 40, Changdeokgung 1-gil, Jongno-gu, Seoul, Republic of Korea, 03057')
    parts.append('</div>')
    parts.append('</div>')

    return "\n".join(parts)


def send_email(subject: str, html_body: str, to: str) -> dict:
    """Gmail API로 이메일을 발송합니다."""
    gmail = get_service("gmail")

    message = MIMEMultipart("alternative")
    message["to"] = to
    message["subject"] = subject

    import re
    text_body = re.sub(r"<[^>]+>", "", html_body)
    text_body = text_body.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    part1 = MIMEText(text_body, "plain", "utf-8")
    part2 = MIMEText(html_body, "html", "utf-8")
    message.attach(part1)
    message.attach(part2)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    result = gmail.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
    return result


def main():
    parser = argparse.ArgumentParser(description="뉴믹스 일간 매출 보고서")
    parser.add_argument("--date", help="대상 날짜 (YYYY-MM-DD, 기본: 어제)")
    parser.add_argument("--send-email", dest="send_email", action="store_true",
                        help="이메일 발송")
    parser.add_argument("--to", default="forest@grandeclipfnb.com",
                        help="수신자 이메일 (기본: 본인)")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        target_date = datetime.now() - timedelta(days=1)

    print(f"리포트 대상: {target_date.strftime('%Y-%m-%d')} ({WEEKDAY_KR[target_date.weekday()]})")
    print("데이터 수집 중...")

    data = compute_report(target_date)

    if args.json:
        output = {
            "date": data["date_str"],
            "weekday": data["weekday"],
            "channels": data["channels"],
            "total": data["total"],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
        return

    report_text = format_report_text(data)

    print("\n" + "=" * 50)
    print(report_text)
    print("=" * 50)

    if args.send_email:
        d = data["date"]
        subject = f"[뉴믹스][일간]{d.month:02d}{d.day:02d}"
        html_body = format_report_html(data)
        result = send_email(subject, html_body, args.to)
        print(f"\n이메일 발송 완료: {args.to} (Message ID: {result.get('id', 'N/A')})")


if __name__ == "__main__":
    main()
