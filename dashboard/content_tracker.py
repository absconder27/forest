"""
콘텐츠 트래커 모듈

Instagram 해시태그/멘션 자동 수집 + Google Sheets 수동 입력 통합
"""

import sys
import csv
import json
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent / "data"
CONTENT_CSV = DATA_DIR / "content.csv"

# 검색할 해시태그/키워드 목록
HASHTAGS = ["뉴믹스커피", "newmixcoffee", "ニューミックス", "newmix", "뉴믹스"]
MENTIONS = ["newmixcoffee.kr", "newmixcoffee.jp"]  # 공식 계정

# 공식 채널 정보
OFFICIAL_ACCOUNTS = {
    "instagram": {
        "kr": {"handle": "newmixcoffee.kr", "followers": 22000, "market": "한국"},
        "jp": {"handle": "newmixcoffee.jp", "followers": 3636, "market": "일본"},
    },
    "x": {
        "jp": {"handle": "newmixcoffee", "market": "일본"},
    },
}

# 국가 매핑 (언어/해시태그 기반 추정)
COUNTRY_KEYWORDS = {
    "일본": ["日本", "japan", "jp", "ニュー", "東京", "大阪", "🇯🇵"],
    "대만": ["台灣", "台湾", "taiwan", "tw", "台北", "🇹🇼"],
    "중국": ["中国", "china", "cn", "北京", "上海", "🇨🇳", "小红书"],
}

PLATFORM_NAMES = {
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "xiaohongshu": "샤오홍슈",
    "youtube": "YouTube",
    "x": "X",
    "blog": "블로그",
}

CONTENT_FIELDS = [
    "date", "platform", "country", "author", "followers",
    "url", "caption", "likes", "comments", "saves",
    "views", "source",  # source: "auto" or "manual"
]


# ============================================================
# Instagram 자동 수집 (instaloader)
# ============================================================

def fetch_instagram_hashtag(hashtag: str, days: int = 30, max_posts: int = 50) -> list[dict]:
    """Instagram 해시태그 포스팅을 수집합니다.

    로그인이 필요합니다. 최초 1회 `instaloader -l <username>` 실행 필요.

    Args:
        hashtag: 검색할 해시태그 (# 제외)
        days: 최근 며칠간 수집
        max_posts: 최대 수집 수

    Returns:
        포스팅 목록
    """
    try:
        import instaloader
    except ImportError:
        print("instaloader 미설치. pip install instaloader")
        return []

    L = instaloader.Instaloader()

    # 저장된 세션 로드 시도
    session_dir = Path.home() / ".config" / "instaloader"
    session_files = list(session_dir.glob("session-*")) if session_dir.exists() else []

    if session_files:
        username = session_files[0].name.replace("session-", "")
        try:
            L.load_session_from_file(username)
        except Exception as e:
            print(f"세션 로드 실패: {e}")
            print("instaloader -l <username> 으로 로그인 필요")
            return []
    else:
        print("Instagram 로그인 필요:")
        print("  터미널에서 실행: python3 -m instaloader -l <your_instagram_username>")
        print("  로그인 후 다시 시도하세요.")
        return []

    cutoff = datetime.now() - timedelta(days=days)
    posts = []

    try:
        ht = instaloader.Hashtag.from_name(L.context, hashtag)
        for post in ht.get_posts():
            if post.date_utc < cutoff:
                break
            if len(posts) >= max_posts:
                break

            country = _guess_country(post.caption or "")

            posts.append({
                "date": post.date_utc.strftime("%Y-%m-%d"),
                "platform": "instagram",
                "country": country,
                "author": post.owner_username,
                "followers": _safe_get_followers(L, post.owner_username),
                "url": f"https://www.instagram.com/p/{post.shortcode}/",
                "caption": (post.caption or "")[:200],
                "likes": post.likes,
                "comments": post.comments,
                "saves": 0,  # 저장수는 비공개
                "views": post.video_view_count or 0,
                "source": "auto",
            })

    except Exception as e:
        print(f"해시태그 #{hashtag} 수집 실패: {e}")

    return posts


def _safe_get_followers(L, username: str) -> int:
    """팔로워 수를 안전하게 조회합니다."""
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        return profile.followers
    except Exception:
        return 0


def fetch_all_instagram(days: int = 30) -> list[dict]:
    """모든 해시태그에서 Instagram 포스팅을 수집합니다."""
    all_posts = []
    seen_urls = set()

    for hashtag in HASHTAGS:
        posts = fetch_instagram_hashtag(hashtag, days=days)
        for p in posts:
            if p["url"] not in seen_urls:
                all_posts.append(p)
                seen_urls.add(p["url"])

    all_posts.sort(key=lambda x: x["date"], reverse=True)
    return all_posts


# ============================================================
# Google Sheets 연동 (수동 입력 데이터)
# ============================================================

SHEET_ID = None  # 사용자가 설정해야 함
SHEET_RANGE = "콘텐츠트래커!A:L"


def fetch_from_sheets(sheet_id: str = None) -> list[dict]:
    """Google Sheets에서 콘텐츠 데이터를 가져옵니다.

    시트 컬럼 순서:
    날짜 | 플랫폼 | 국가 | 작성자 | 팔로워 | URL | 캡션 | 좋아요 | 댓글 | 저장 | 조회수

    Args:
        sheet_id: Google Sheets 문서 ID (URL에서 추출)

    Returns:
        포스팅 목록
    """
    sid = sheet_id or SHEET_ID
    if not sid:
        return []

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "00-system" / "02-scripts" / "gws"))
        from gws_auth import get_service

        service = get_service("sheets")
        result = service.spreadsheets().values().get(
            spreadsheetId=sid,
            range=SHEET_RANGE,
        ).execute()

        rows = result.get("values", [])
        if len(rows) < 2:
            return []

        headers = rows[0]
        posts = []

        # 헤더 매핑
        col_map = {
            "날짜": "date", "플랫폼": "platform", "국가": "country",
            "작성자": "author", "팔로워": "followers", "URL": "url",
            "캡션": "caption", "좋아요": "likes", "댓글": "comments",
            "저장": "saves", "조회수": "views",
        }

        for row in rows[1:]:
            if not row or not row[0]:
                continue
            post = {"source": "sheets"}
            for i, header in enumerate(headers):
                field = col_map.get(header, header.lower())
                value = row[i] if i < len(row) else ""
                # 숫자 필드 변환
                if field in ("likes", "comments", "saves", "views", "followers"):
                    try:
                        value = int(str(value).replace(",", "")) if value else 0
                    except ValueError:
                        value = 0
                post[field] = value
            posts.append(post)

        return posts

    except Exception as e:
        print(f"Sheets 연동 실패: {e}")
        return []


# ============================================================
# 통합 데이터 관리
# ============================================================

def load_content_data() -> list[dict]:
    """로컬 CSV에서 콘텐츠 데이터를 로드합니다."""
    if not CONTENT_CSV.exists():
        return []

    records = []
    with open(CONTENT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in ("likes", "comments", "saves", "views", "followers"):
                row[field] = int(row.get(field, 0) or 0)
            records.append(row)
    return records


def save_content_data(records: list[dict]):
    """콘텐츠 데이터를 CSV로 저장합니다."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONTENT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CONTENT_FIELDS)
        writer.writeheader()
        for r in records:
            row = {k: r.get(k, "") for k in CONTENT_FIELDS}
            writer.writerow(row)


def sync_all_content(days: int = 30, sheet_id: str = None) -> dict:
    """모든 소스에서 콘텐츠 데이터를 동기화합니다.

    Returns:
        {"instagram": n, "sheets": n, "total": n, "new": n}
    """
    existing = load_content_data()
    existing_urls = {r.get("url", "") for r in existing if r.get("url")}

    stats = {"instagram": 0, "sheets": 0, "total": len(existing), "new": 0}
    new_records = []

    # 1. Instagram 자동 수집
    try:
        ig_posts = fetch_all_instagram(days=days)
        stats["instagram"] = len(ig_posts)
        for p in ig_posts:
            if p["url"] not in existing_urls:
                new_records.append(p)
                existing_urls.add(p["url"])
    except Exception as e:
        print(f"Instagram 수집 에러: {e}")

    # 2. Google Sheets
    try:
        sheet_posts = fetch_from_sheets(sheet_id)
        stats["sheets"] = len(sheet_posts)
        for p in sheet_posts:
            url = p.get("url", "")
            if url and url not in existing_urls:
                new_records.append(p)
                existing_urls.add(url)
    except Exception as e:
        print(f"Sheets 수집 에러: {e}")

    # 3. 병합 및 저장
    all_records = existing + new_records
    all_records.sort(key=lambda x: x.get("date", ""), reverse=True)
    save_content_data(all_records)

    stats["new"] = len(new_records)
    stats["total"] = len(all_records)
    return stats


def add_manual_content(post: dict) -> list[dict]:
    """수동으로 콘텐츠를 추가합니다."""
    records = load_content_data()
    url = post.get("url", "")

    # URL 중복 체크
    if url:
        for r in records:
            if r.get("url") == url:
                r.update(post)
                save_content_data(records)
                return records

    post["source"] = "manual"
    records.append(post)
    records.sort(key=lambda x: x.get("date", ""), reverse=True)
    save_content_data(records)
    return records


def get_sample_content() -> list[dict]:
    """데모용 샘플 콘텐츠 데이터를 생성합니다."""
    import random
    random.seed(99)

    platforms = ["instagram", "tiktok", "youtube", "x"]
    countries = ["일본", "대만", "중국"]

    authors = {
        "일본": [
            ("tokyo_cafe_gram", 52000), ("japan_coffee_lover", 31000),
            ("miki_cafe_log", 89000), ("osaka_gourmet_trip", 15000),
            ("creatrip_jp", 210000),
        ],
        "대만": [
            ("taipei_foodie", 44000), ("tw_cafe_hunter", 27000),
            ("korea_trip_tw", 63000), ("x.yunny.x", 18000),
        ],
        "중국": [
            ("韩国咖啡探店", 120000), ("首尔美食日记", 78000),
            ("小红书探店达人", 55000),
        ],
    }

    captions_by_country = {
        "일본": [
            "뉴믹스커피 성수 본점 방문! 한국여행 필수 카페 #newmixcoffee #ニューミックス",
            "ニューミックスコーヒー最高！韓国旅行で絶対行くべきカフェ",
            "newmix coffee 성수점 다녀왔어요 커피가 진짜 맛있다 #뉴믹스커피",
            "韓国のミックスコーヒー文化を再解釈したニューミックス、すごい！",
        ],
        "대만": [
            "首爾聖水洞必去咖啡廳 newmix coffee 太好喝了 #韓國旅遊",
            "뉴믹스커피 대만 친구랑 같이 왔어요! 반응 대박 #newmixcoffee",
            "韓國咖啡推薦 newmix 信義區快開分店吧！",
        ],
        "중국": [
            "韩国圣水洞newmix咖啡 真的太好喝了！推荐给大家 #韩国旅游",
            "newmix coffee 首尔必打卡咖啡店 味道绝了",
            "뉴믹스 중국 진출 기대! WI마케팅 보고서 기반 데이터",
        ],
    }

    samples = []
    base_date = datetime(2026, 2, 20)

    for i in range(25):
        date = base_date + timedelta(days=random.randint(0, 23))
        country = random.choice(countries)
        platform = random.choice(platforms)
        author_list = authors[country]
        author_name, follower_count = random.choice(author_list)

        is_viral = random.random() < 0.15

        likes = random.randint(200, 3000)
        views = random.randint(1000, 30000)
        comments = random.randint(10, 200)
        saves = random.randint(50, 500)

        if is_viral:
            likes *= 5
            views *= 8
            comments *= 3
            saves *= 4

        caption = random.choice(captions_by_country.get(country, captions_by_country["일본"]))

        url_templates = {
            "instagram": f"https://www.instagram.com/explore/tags/newmixcoffee/",
            "tiktok": f"https://www.tiktok.com/tag/newmixcoffee",
            "youtube": f"https://www.youtube.com/results?search_query=newmix+coffee",
            "x": f"https://x.com/search?q=newmixcoffee",
        }

        samples.append({
            "date": date.strftime("%Y-%m-%d"),
            "platform": platform,
            "country": country,
            "author": author_name,
            "followers": follower_count,
            "url": url_templates.get(platform, ""),
            "caption": caption,
            "likes": likes,
            "comments": comments,
            "saves": saves,
            "views": views,
            "source": "sample",
        })

    samples.sort(key=lambda x: x["date"], reverse=True)
    return samples


def _guess_country(text: str) -> str:
    """캡션/텍스트에서 국가를 추정합니다."""
    text_lower = text.lower()
    scores = {}
    for country, keywords in COUNTRY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[country] = score

    if scores:
        return max(scores, key=scores.get)
    return "기타"
