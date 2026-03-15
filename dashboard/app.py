"""
뉴믹스 마케팅 대시보드 - MVP

스타일가이드 적용: '꿈이 자라는 뜰' 컬러 팔레트 + 모던 카드 UI
실행: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from data_fetcher import (
    fetch_and_save,
    load_sales_data,
    get_sample_data,
    add_manual_entry,
)
from sheets_fetcher import (
    fetch_country_sales,
    fetch_daily_report,
    country_sales_to_dashboard_format,
    save_country_sales_csv,
)
from content_tracker import (
    sync_all_content,
    load_content_data,
    get_sample_content,
    add_manual_content,
    PLATFORM_NAMES,
)
from charts import (
    COLORS,
    COUNTRY_COLORS,
    create_dataframe,
    sales_pie_chart,
    sales_trend_chart,
    sales_bar_chart,
    sales_change_metrics,
    sales_stacked_area,
    create_content_dataframe,
    content_by_platform_chart,
    content_by_country_chart,
    content_timeline_chart,
    content_engagement_scatter,
)

# --- 페이지 설정 ---
st.set_page_config(
    page_title="뉴믹스 마케팅 대시보드",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --- 커스텀 CSS ---
def inject_custom_css():
    st.markdown(f"""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');
    @import url('https://hangeul.pstatic.net/hangeul_static/css/nanum-square-round.css');

    .stApp {{
        background-color: {COLORS["bg"]};
    }}
    .stMainBlockContainer {{
        padding-top: 1.5rem;
    }}
    html, body, [class*="css"] {{
        font-family: 'Pretendard Variable', 'Pretendard', -apple-system, sans-serif;
        color: {COLORS["text"]};
    }}
    h1, h2, h3 {{
        font-family: 'NanumSquareRound', 'Pretendard Variable', sans-serif !important;
        color: {COLORS["text"]} !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: white;
        border-right: 1px solid {COLORS["border"]};
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {{
        font-size: 1.1rem !important;
    }}
    [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white;
        border-radius: 12px;
        border: 1px solid {COLORS["border"]};
        box-shadow: 0 2px 20px rgba(0, 0, 0, 0.04);
        padding: 0;
    }}
    [data-testid="stMetric"] {{
        background-color: white;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 20px rgba(0, 0, 0, 0.04);
        border: 1px solid {COLORS["border"]};
    }}
    [data-testid="stMetricLabel"] {{
        font-family: 'Pretendard Variable', sans-serif;
        font-size: 0.85rem !important;
        color: {COLORS["text_sub"]} !important;
    }}
    [data-testid="stMetricValue"] {{
        font-family: 'NanumSquareRound', sans-serif;
        font-size: 1.5rem !important;
        color: {COLORS["text"]} !important;
    }}
    [data-testid="stMetricDelta"] > div {{
        font-size: 0.8rem !important;
    }}
    [data-testid="stPlotlyChart"] {{
        background-color: white;
        border-radius: 12px;
        padding: 0.5rem;
        box-shadow: 0 2px 20px rgba(0, 0, 0, 0.04);
        border: 1px solid {COLORS["border"]};
    }}
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid {COLORS["border"]};
        box-shadow: 0 2px 20px rgba(0, 0, 0, 0.04);
    }}
    [data-testid="stRadio"] > div {{
        gap: 0.5rem;
    }}
    [data-testid="stRadio"] label {{
        background-color: white;
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 0.3rem 0.8rem !important;
        font-size: 0.85rem;
        transition: all 0.15s ease;
    }}
    [data-testid="stRadio"] label:hover {{
        border-color: {COLORS["primary"]};
    }}
    hr {{
        border-color: {COLORS["border"]} !important;
        opacity: 0.5;
    }}
    .stButton > button {{
        border-radius: 8px;
        border: 1px solid {COLORS["border"]};
        font-family: 'Pretendard Variable', sans-serif;
        transition: all 0.15s ease;
    }}
    .stButton > button:hover {{
        border-color: {COLORS["primary"]};
        color: {COLORS["primary"]};
    }}
    .stButton > button[kind="primary"] {{
        background-color: {COLORS["primary"]};
        color: white;
        border-color: {COLORS["primary"]};
    }}
    [data-testid="stDateInput"] {{
        max-width: 320px;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        border-bottom: 2px solid {COLORS["border"]};
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1rem;
        font-family: 'Pretendard Variable', sans-serif;
        font-size: 0.9rem;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: white;
        border-bottom-color: {COLORS["primary"]} !important;
        color: {COLORS["primary"]} !important;
    }}
    .stCaption, [data-testid="stCaptionContainer"] {{
        color: {COLORS["text_sub"]} !important;
        font-size: 0.8rem !important;
    }}
    </style>
    """, unsafe_allow_html=True)


inject_custom_css()


# --- 헤더 ---
def render_header():
    st.markdown(f"""
    <div style="
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.8rem 0 1.2rem 0;
    ">
        <div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="
                    width: 40px; height: 40px;
                    background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["sub"]});
                    border-radius: 10px;
                    display: flex; align-items: center; justify-content: center;
                    color: white; font-size: 20px;
                "><span>N</span></div>
                <div>
                    <h1 style="
                        margin: 0; padding: 0; font-size: 1.6rem; font-weight: 700;
                        font-family: 'NanumSquareRound', sans-serif; color: {COLORS["text"]};
                    ">뉴믹스 마케팅 대시보드</h1>
                    <p style="
                        margin: 0; padding: 0; font-size: 0.85rem; color: {COLORS["text_sub"]};
                    ">국가별 마케팅 예산 배분 의사결정을 위한 매출 & 콘텐츠 현황</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

render_header()


# --- 커스텀 컴포넌트 ---
def render_metric_card(country: str, metrics: dict, color: str, icon: str):
    m = metrics
    delta_color = COLORS["primary"] if m["day_change_pct"] >= 0 else COLORS["secondary"]
    delta_arrow = "&#9650;" if m["day_change_pct"] >= 0 else "&#9660;"
    week_color = COLORS["primary"] if m["week_change_pct"] >= 0 else COLORS["secondary"]
    week_arrow = "&#9650;" if m["week_change_pct"] >= 0 else "&#9660;"

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}15, {color}08);
        border: 1px solid {color}30;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        height: 100%;
        transition: box-shadow 0.15s ease;
    ">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.7rem;">
            <span style="font-size: 1.3rem;">{icon}</span>
            <span style="
                font-family: 'Pretendard Variable', sans-serif;
                font-size: 0.85rem; color: {COLORS["text_sub"]}; font-weight: 500;
            ">{country}</span>
            <span style="
                margin-left: auto;
                background: {color}20; color: {color};
                font-size: 0.7rem; padding: 2px 8px;
                border-radius: 12px; font-weight: 600;
            ">{m["share_pct"]:.1f}%</span>
        </div>
        <div style="
            font-family: 'NanumSquareRound', sans-serif;
            font-size: 1.6rem; font-weight: 700; color: {COLORS["text"]};
            margin-bottom: 0.5rem;
        ">{m["latest"]:,}<span style="font-size: 0.85rem; font-weight: 400; color: {COLORS["text_sub"]};">원</span></div>
        <div style="display: flex; gap: 12px; font-size: 0.78rem;">
            <span style="color: {delta_color};">
                {delta_arrow} {abs(m["day_change_pct"]):.1f}% <span style="color: {COLORS["text_sub"]};">전일</span>
            </span>
            <span style="color: {week_color};">
                {week_arrow} {abs(m["week_change_pct"]):.1f}% <span style="color: {COLORS["text_sub"]};">전주</span>
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_summary_card(label: str, value: str, sub: str = "", color: str = COLORS["primary"]):
    st.markdown(f"""
    <div style="
        background: white;
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        box-shadow: 0 2px 20px rgba(0,0,0,0.04);
        border-top: 3px solid {color};
    ">
        <div style="
            font-size: 0.8rem; color: {COLORS["text_sub"]};
            font-weight: 500; margin-bottom: 0.4rem;
        ">{label}</div>
        <div style="
            font-family: 'NanumSquareRound', sans-serif;
            font-size: 1.4rem; font-weight: 700; color: {COLORS["text"]};
        ">{value}</div>
        <div style="
            font-size: 0.75rem; color: {COLORS["text_sub"]}; margin-top: 0.2rem;
        ">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def render_content_card(post: dict, color: str = COLORS["border"]):
    """포스팅 카드 렌더링."""
    platform_icons = {
        "instagram": "📸", "tiktok": "🎵", "xiaohongshu": "📕",
        "youtube": "▶️", "x": "𝕏", "blog": "📝",
    }
    icon = platform_icons.get(post.get("platform", ""), "📌")
    platform_label = PLATFORM_NAMES.get(post.get("platform", ""), post.get("platform", ""))
    country_icons = {"일본": "🇯🇵", "대만": "🇹🇼", "중국": "🇨🇳"}
    country_icon = country_icons.get(post.get("country", ""), "🌏")

    likes = int(post.get("likes", 0))
    views = int(post.get("views", 0))
    comments = int(post.get("comments", 0))
    saves = int(post.get("saves", 0))
    url = post.get("url", "")

    # URL 관련 HTML 조각을 미리 생성
    primary = COLORS["primary"]
    border_c = COLORS["border"]
    text_c = COLORS["text"]
    text_sub_c = COLORS["text_sub"]

    link_open = f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="text-decoration: none; color: inherit; display: block;">' if url else ""
    link_close = "</a>" if url else ""
    link_badge = f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="font-size: 0.7rem; color: {primary}; text-decoration: none; border: 1px solid {primary}40; padding: 1px 8px; border-radius: 10px; margin-left: auto; white-space: nowrap;">원본 보기 ↗</a>' if url else ""
    cursor = "pointer" if url else "default"
    hover_attr = "onmouseover=\"this.style.boxShadow='0 4px 24px rgba(0,0,0,0.08)'\" onmouseout=\"this.style.boxShadow='none'\"" if url else ""

    saves_html = f"<span>🔖 {saves:,}</span>" if saves else ""
    views_html = f"<span>👁️ {views:,}</span>" if views else ""
    followers_val = int(post.get("followers", 0))
    followers_html = f"<span style='font-size: 0.7rem;'>👥 {followers_val:,}</span>" if followers_val else ""
    caption_text = (post.get("caption", "") or "")[:120]
    author = post.get("author", "")
    date_str = post.get("date", "")

    html = f"""{link_open}
    <div style="
        background: white;
        border: 1px solid {border_c};
        border-left: 3px solid {color};
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
        transition: box-shadow 0.15s ease;
        cursor: {cursor};
    " {hover_attr}>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
            <div style="display: flex; align-items: center; gap: 6px;">
                <span>{icon}</span>
                <span style="font-size: 0.8rem; font-weight: 600; color: {text_c};">{platform_label}</span>
                <span>{country_icon}</span>
                <span style="font-size: 0.75rem; color: {text_sub_c};">@{author}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.72rem; color: {text_sub_c};">{date_str}</span>
                {link_badge}
            </div>
        </div>
        <div style="font-size: 0.82rem; color: {text_c}; margin-bottom: 0.5rem; line-height: 1.4;">
            {caption_text}
        </div>
        <div style="display: flex; gap: 14px; font-size: 0.75rem; color: {text_sub_c};">
            <span>❤️ {likes:,}</span>
            <span>💬 {comments:,}</span>
            {saves_html}
            {views_html}
            {followers_html}
        </div>
    </div>
    {link_close}"""

    st.markdown(html, unsafe_allow_html=True)


# --- 사이드바 ---
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 0.5rem 0 1rem 0;">
        <h2 style="font-family: 'NanumSquareRound', sans-serif; font-size: 1.1rem; margin: 0;">설정</h2>
    </div>
    """, unsafe_allow_html=True)

    data_source = st.radio(
        "데이터 소스",
        ["Google Sheets (실제 데이터)", "샘플 데이터 (데모)"],
        index=0,
    )

    if data_source == "Google Sheets (실제 데이터)":
        if st.button("Sheets에서 최신 데이터 가져오기", type="primary", use_container_width=True):
            with st.spinner("Google Sheets에서 매출 데이터를 가져오는 중..."):
                try:
                    country_data = fetch_country_sales()
                    save_country_sales_csv(country_data)
                    report = fetch_daily_report()
                    st.session_state["channel_report"] = report
                    st.success(f"국가별 매출 {len(country_data)}건, 채널 보고 {len(report['actuals'])}건")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"데이터 조회 실패: {e}")

    st.divider()

    # 콘텐츠 데이터 설정
    st.markdown(f"""
    <div style="padding: 0 0 0.5rem 0;">
        <h3 style="font-family: 'NanumSquareRound', sans-serif; font-size: 1rem; margin: 0;">콘텐츠 수집</h3>
    </div>
    """, unsafe_allow_html=True)

    content_sheet_id = st.text_input(
        "Google Sheets ID (선택)",
        placeholder="스프레드시트 URL에서 ID 복사",
        help="콘텐츠 트래커 시트의 ID를 입력하면 자동 연동됩니다.",
    )

    col_ig, col_sync = st.columns(2)
    with col_ig:
        if st.button("Instagram 수집", use_container_width=True):
            with st.spinner("Instagram 해시태그 수집 중..."):
                try:
                    stats = sync_all_content(days=30, sheet_id=content_sheet_id or None)
                    st.success(f"신규 {stats['new']}건 (총 {stats['total']}건)")
                except Exception as e:
                    st.error(f"수집 실패: {e}")
    with col_sync:
        if st.button("Sheets 동기화", use_container_width=True):
            if content_sheet_id:
                with st.spinner("Sheets 동기화 중..."):
                    try:
                        stats = sync_all_content(days=30, sheet_id=content_sheet_id)
                        st.success(f"신규 {stats['new']}건")
                    except Exception as e:
                        st.error(f"동기화 실패: {e}")
            else:
                st.warning("Sheets ID를 입력하세요")

    st.divider()

    # 수동 매출 입력
    st.markdown(f"""
    <div style="padding: 0 0 0.5rem 0;">
        <h3 style="font-family: 'NanumSquareRound', sans-serif; font-size: 1rem; margin: 0;">수동 매출 입력</h3>
    </div>
    """, unsafe_allow_html=True)
    with st.form("manual_entry"):
        entry_date = st.date_input("날짜", datetime.now())
        entry_country = st.selectbox("국가", ["일본", "대만", "중국"])
        entry_sales = st.number_input("매출 (원)", min_value=0, step=10000)
        submitted = st.form_submit_button("추가", type="primary")
        if submitted and entry_sales > 0:
            add_manual_entry(
                entry_date.strftime("%Y-%m-%d"), entry_country, entry_sales,
            )
            st.success(f"{entry_country} {entry_date} 매출 추가 완료")
            st.rerun()

    st.divider()

    # 수동 콘텐츠 입력
    st.markdown(f"""
    <div style="padding: 0 0 0.5rem 0;">
        <h3 style="font-family: 'NanumSquareRound', sans-serif; font-size: 1rem; margin: 0;">수동 콘텐츠 입력</h3>
    </div>
    """, unsafe_allow_html=True)
    with st.form("manual_content"):
        c_date = st.date_input("포스팅 날짜", datetime.now(), key="c_date")
        c_platform = st.selectbox("플랫폼", list(PLATFORM_NAMES.values()))
        c_country = st.selectbox("국가", ["일본", "대만", "중국"], key="c_country")
        c_author = st.text_input("작성자 (계정명)")
        c_url = st.text_input("URL")
        c_caption = st.text_area("캡션/내용 요약", height=68)
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            c_likes = st.number_input("좋아요", min_value=0, step=10, key="c_likes")
            c_saves = st.number_input("저장", min_value=0, step=10, key="c_saves")
        with c_col2:
            c_comments = st.number_input("댓글", min_value=0, step=1, key="c_comments")
            c_views = st.number_input("조회수", min_value=0, step=100, key="c_views")
        c_followers = st.number_input("팔로워 수", min_value=0, step=1000, key="c_followers")

        c_submitted = st.form_submit_button("콘텐츠 추가", type="primary")
        if c_submitted and c_author:
            # 플랫폼명 → 키 변환
            platform_key = {v: k for k, v in PLATFORM_NAMES.items()}.get(c_platform, c_platform)
            add_manual_content({
                "date": c_date.strftime("%Y-%m-%d"),
                "platform": platform_key,
                "country": c_country,
                "author": c_author,
                "url": c_url,
                "caption": c_caption,
                "likes": c_likes,
                "comments": c_comments,
                "saves": c_saves,
                "views": c_views,
                "followers": c_followers,
            })
            st.success("콘텐츠 추가 완료")
            st.rerun()


# --- 데이터 로드 ---
@st.cache_data(ttl=300)
def load_data(source: str) -> list[dict]:
    if source == "샘플 데이터 (데모)":
        return get_sample_data()
    else:
        # Google Sheets 데이터 (CSV 캐시)
        import csv
        from pathlib import Path
        csv_path = Path(__file__).parent / "data" / "country_sales.csv"
        if csv_path.exists():
            records = []
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append({
                        "date": row["date"],
                        "country": row["country"],
                        "sales": int(row["sales"]),
                        "visitors": int(row.get("visitors", 0)),
                        "store": row.get("store", ""),
                        "marketing_note": row.get("marketing_note", ""),
                    })
            if records:
                # 성수+북촌 합산 (대시보드용)
                return country_sales_to_dashboard_format(records)
        return get_sample_data()


@st.cache_data(ttl=300)
def load_channel_report(source: str) -> dict:
    if source == "샘플 데이터 (데모)":
        return {}
    try:
        return fetch_daily_report()
    except Exception:
        return {}


@st.cache_data(ttl=300)
def load_content(source: str) -> list[dict]:
    if source == "샘플 데이터 (데모)":
        return get_sample_content()
    else:
        data = load_content_data()
        return data if data else get_sample_content()


records = load_data(data_source)
content_records = load_content(data_source)
channel_report = st.session_state.get("channel_report") or load_channel_report(data_source)

if not records:
    st.warning("매출 데이터가 없습니다. 사이드바에서 데이터를 가져오거나 수동 입력하세요.")
    st.stop()

df = create_dataframe(records)
content_df = create_content_dataframe(content_records) if content_records else pd.DataFrame()

# --- 날짜 필터 ---
col_filter1, col_filter2 = st.columns([1, 2])
with col_filter1:
    date_range = st.date_input(
        "기간 선택",
        value=(df["date"].min().date(), df["date"].max().date()),
        min_value=df["date"].min().date(),
        max_value=df["date"].max().date(),
    )

if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    mask = (df["date"].dt.date >= start) & (df["date"].dt.date <= end)
    df = df[mask]
    if not content_df.empty:
        cmask = (content_df["date"].dt.date >= start) & (content_df["date"].dt.date <= end)
        content_df = content_df[cmask]


# ============================================================
# 메인 탭
# ============================================================
tab_sales, tab_content, tab_correlation = st.tabs([
    "📊 매출 현황", "📱 콘텐츠 트래커", "🔗 콘텐츠 × 매출"
])


# ============================================================
# 탭 1: 매출 현황
# ============================================================
with tab_sales:
    # 국가별 매출 메트릭 카드
    st.markdown(f"""
    <div style="margin: 0.5rem 0 0.8rem 0;">
        <h2 style="
            font-family: 'NanumSquareRound', sans-serif;
            font-size: 1.2rem; font-weight: 700; color: {COLORS["text"]}; margin: 0;
        ">국가별 매출 현황</h2>
        <p style="font-size: 0.8rem; color: {COLORS["text_sub"]}; margin: 0.2rem 0 0 0;">
            {df["date"].max().strftime("%Y년 %m월 %d일")} 기준
        </p>
    </div>
    """, unsafe_allow_html=True)

    metrics = sales_change_metrics(df)
    COUNTRY_ICONS = {"일본": "🇯🇵", "대만": "🇹🇼", "중국": "🇨🇳"}
    metric_cols = st.columns(3, gap="medium")

    for i, (country, m) in enumerate(metrics.items()):
        with metric_cols[i]:
            render_metric_card(
                country, m,
                color=COUNTRY_COLORS[country],
                icon=COUNTRY_ICONS.get(country, "🌏"),
            )

    # 차트
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    chart_col1, chart_col2 = st.columns([1, 2], gap="medium")

    with chart_col1:
        period_label = f"{df['date'].min().strftime('%m/%d')} ~ {df['date'].max().strftime('%m/%d')}"
        st.plotly_chart(sales_pie_chart(df, period_label), use_container_width=True)

    with chart_col2:
        chart_type = st.radio(
            "chart_type",
            ["라인 차트", "막대 차트", "누적 영역"],
            horizontal=True,
            label_visibility="collapsed",
        )
        if chart_type == "라인 차트":
            st.plotly_chart(sales_trend_chart(df), use_container_width=True)
        elif chart_type == "막대 차트":
            st.plotly_chart(sales_bar_chart(df), use_container_width=True)
        else:
            st.plotly_chart(sales_stacked_area(df), use_container_width=True)

    # 기간 요약
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    total_sales = df["sales"].sum()
    avg_daily = int(total_sales / df["date"].nunique()) if df["date"].nunique() > 0 else 0
    best_day = df.groupby("date")["sales"].sum()
    best_date = best_day.idxmax() if len(best_day) > 0 else None
    top_country = df.groupby("country")["sales"].sum().idxmax()
    top_pct = df.groupby("country")["sales"].sum().max() / total_sales * 100

    summary_cols = st.columns(4, gap="medium")
    with summary_cols[0]:
        render_summary_card("총 매출", f"₩{total_sales:,}", f"{df['date'].nunique()}일간", COLORS["primary"])
    with summary_cols[1]:
        render_summary_card("일평균 매출", f"₩{avg_daily:,}", "전체 기간 평균", COLORS["sub"])
    with summary_cols[2]:
        render_summary_card(
            "최고 매출일",
            best_date.strftime("%m월 %d일") if best_date else "-",
            f"₩{int(best_day.max()):,}" if len(best_day) > 0 else "",
            COLORS["secondary"],
        )
    with summary_cols[3]:
        render_summary_card("매출 1위 국가", f"{top_country}", f"비중 {top_pct:.1f}%", COLORS["accent"])

    # 채널별 매출 (일간 보고 지표)
    if channel_report and channel_report.get("actuals"):
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="margin: 0 0 0.8rem 0;">
            <h2 style="
                font-family: 'NanumSquareRound', sans-serif;
                font-size: 1.2rem; font-weight: 700; color: {COLORS["text"]}; margin: 0;
            ">채널별 매출 현황 (3월)</h2>
            <p style="font-size: 0.8rem; color: {COLORS["text_sub"]}; margin: 0.2rem 0 0 0;">
                일간 보고 지표 기준 · 달성률 {channel_report["summary"]["achievement_rate"]}%
            </p>
        </div>
        """, unsafe_allow_html=True)

        ch_summary = channel_report["summary"]
        ch_cols = st.columns(3, gap="medium")
        with ch_cols[0]:
            render_summary_card(
                "3월 목표", f"{ch_summary['total_target']}만",
                "전체 채널 합산", COLORS["primary"],
            )
        with ch_cols[1]:
            render_summary_card(
                "3월 실적", f"{ch_summary['total_actual']}만",
                f"달성률 {ch_summary['achievement_rate']}%", COLORS["secondary"],
            )
        with ch_cols[2]:
            gap = ch_summary["total_target"] - ch_summary["total_actual"]
            render_summary_card(
                "잔여 목표", f"{gap:.1f}만",
                f"남은 일수 기준", COLORS["sub"],
            )

        # 채널별 실적 테이블
        actuals_df = pd.DataFrame(channel_report["actuals"])
        if not actuals_df.empty:
            ch_pivot = actuals_df.pivot_table(
                index="date", columns="channel", values="sales", aggfunc="sum"
            ).reset_index()
            ch_pivot["합계"] = ch_pivot.select_dtypes(include="number").sum(axis=1)
            st.dataframe(
                ch_pivot.style.format(
                    {col: "{:.1f}" for col in ch_pivot.columns if col != "date"}
                ),
                use_container_width=True,
                height=250,
            )

    # 상세 데이터
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="margin: 0 0 0.8rem 0;">
        <h2 style="
            font-family: 'NanumSquareRound', sans-serif;
            font-size: 1.2rem; font-weight: 700; color: {COLORS["text"]}; margin: 0;
        ">국가별 상세 데이터</h2>
    </div>
    """, unsafe_allow_html=True)

    selected_countries = st.multiselect(
        "국가 필터",
        df["country"].unique().tolist(),
        default=df["country"].unique().tolist(),
        label_visibility="collapsed",
    )
    filtered = df[df["country"].isin(selected_countries)]
    pivot = filtered.pivot_table(
        index="date", columns="country", values="sales", aggfunc="sum"
    ).reset_index()
    pivot["date"] = pivot["date"].dt.strftime("%Y-%m-%d")
    pivot["합계"] = pivot.select_dtypes(include="number").sum(axis=1)

    st.dataframe(
        pivot.style.format({col: "{:,.0f}" for col in pivot.columns if col != "date"}),
        use_container_width=True,
        height=350,
    )


# ============================================================
# 탭 2: 콘텐츠 트래커
# ============================================================
with tab_content:
    if content_df.empty:
        st.info("콘텐츠 데이터가 없습니다. 사이드바에서 Instagram 수집 또는 수동 입력하세요.")
    else:
        # 콘텐츠 요약 메트릭
        st.markdown(f"""
        <div style="margin: 0.5rem 0 0.8rem 0;">
            <h2 style="
                font-family: 'NanumSquareRound', sans-serif;
                font-size: 1.2rem; font-weight: 700; color: {COLORS["text"]}; margin: 0;
            ">콘텐츠 현황</h2>
            <p style="font-size: 0.8rem; color: {COLORS["text_sub"]}; margin: 0.2rem 0 0 0;">
                총 {len(content_df)}건의 포스팅 · 중국 데이터는 WI마케팅 보고 기반
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 요약 카드
        cs_cols = st.columns(4, gap="medium")
        with cs_cols[0]:
            render_summary_card(
                "총 포스팅", f"{len(content_df)}건",
                f"{content_df['date'].nunique()}일간",
                COLORS["primary"],
            )
        with cs_cols[1]:
            total_eng = int(content_df["engagement"].sum())
            render_summary_card(
                "총 반응",
                f"{total_eng:,}",
                "좋아요 + 댓글 + 저장",
                COLORS["secondary"],
            )
        with cs_cols[2]:
            total_views = int(content_df["views"].sum())
            render_summary_card(
                "총 조회수",
                f"{total_views:,}",
                f"평균 {int(total_views / len(content_df)):,}/건" if len(content_df) > 0 else "",
                COLORS["sub"],
            )
        with cs_cols[3]:
            # 최고 반응 포스팅
            if len(content_df) > 0:
                top_post = content_df.loc[content_df["engagement"].idxmax()]
                render_summary_card(
                    "최고 반응 포스팅",
                    f"@{top_post['author']}",
                    f"반응 {int(top_post['engagement']):,} · {top_post.get('platform_name', '')}",
                    COLORS["accent"],
                )

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # 차트
        chart_col1, chart_col2 = st.columns(2, gap="medium")
        with chart_col1:
            st.plotly_chart(content_by_platform_chart(content_df), use_container_width=True)
        with chart_col2:
            st.plotly_chart(content_by_country_chart(content_df), use_container_width=True)

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        st.plotly_chart(content_engagement_scatter(content_df), use_container_width=True)

        # 포스팅 목록
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="margin: 0 0 0.8rem 0;">
            <h2 style="
                font-family: 'NanumSquareRound', sans-serif;
                font-size: 1.2rem; font-weight: 700; color: {COLORS["text"]}; margin: 0;
            ">최근 포스팅</h2>
        </div>
        """, unsafe_allow_html=True)

        # 필터
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            f_country = st.multiselect(
                "국가", content_df["country"].unique().tolist(),
                default=content_df["country"].unique().tolist(),
                key="content_country_filter",
            )
        with filter_col2:
            f_platform = st.multiselect(
                "플랫폼", content_df["platform_name"].unique().tolist(),
                default=content_df["platform_name"].unique().tolist(),
                key="content_platform_filter",
            )
        with filter_col3:
            f_sort = st.selectbox(
                "정렬", ["최신순", "반응 높은순", "조회수 높은순"],
                key="content_sort",
            )

        filtered_content = content_df[
            content_df["country"].isin(f_country) &
            content_df["platform_name"].isin(f_platform)
        ]

        if f_sort == "반응 높은순":
            filtered_content = filtered_content.sort_values("engagement", ascending=False)
        elif f_sort == "조회수 높은순":
            filtered_content = filtered_content.sort_values("views", ascending=False)
        else:
            filtered_content = filtered_content.sort_values("date", ascending=False)

        # 카드 렌더링
        for _, post in filtered_content.head(20).iterrows():
            color = COUNTRY_COLORS.get(post.get("country", ""), COLORS["border"])
            render_content_card(post.to_dict(), color)


# ============================================================
# 탭 3: 콘텐츠 × 매출 상관관계
# ============================================================
with tab_correlation:
    st.markdown(f"""
    <div style="margin: 0.5rem 0 0.8rem 0;">
        <h2 style="
            font-family: 'NanumSquareRound', sans-serif;
            font-size: 1.2rem; font-weight: 700; color: {COLORS["text"]}; margin: 0;
        ">콘텐츠 × 매출 상관관계</h2>
        <p style="font-size: 0.8rem; color: {COLORS["text_sub"]}; margin: 0.2rem 0 0 0;">
            포스팅 시점과 매출 스파이크를 비교합니다
        </p>
    </div>
    """, unsafe_allow_html=True)

    if content_df.empty:
        st.info("콘텐츠 데이터가 없습니다.")
    else:
        # 전체 타임라인
        st.plotly_chart(
            content_timeline_chart(content_df, df),
            use_container_width=True,
        )

        # 국가별 타임라인
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="margin: 0 0 0.8rem 0;">
            <h3 style="
                font-family: 'NanumSquareRound', sans-serif;
                font-size: 1.1rem; font-weight: 600; color: {COLORS["text"]}; margin: 0;
            ">국가별 상관관계</h3>
        </div>
        """, unsafe_allow_html=True)

        country_tab = st.radio(
            "country_corr", ["🇯🇵 일본", "🇹🇼 대만", "🇨🇳 중국"],
            horizontal=True, label_visibility="collapsed",
            key="corr_country",
        )

        country_name = country_tab.split(" ")[1]
        country_content = content_df[content_df["country"] == country_name]
        country_sales = df[df["country"] == country_name]

        if country_content.empty:
            if country_name == "중국":
                st.info("중국 콘텐츠 데이터는 WI마케팅 보고서를 기반으로 입력해주세요. 사이드바 '수동 콘텐츠 입력'을 이용하세요.")
            else:
                st.info(f"{country_name} 콘텐츠 데이터가 없습니다.")
        else:
            st.plotly_chart(
                content_timeline_chart(country_content, country_sales),
                use_container_width=True,
            )

            # 스파이크 감지
            if not country_sales.empty:
                daily_sales = country_sales.groupby("date")["sales"].sum()
                mean_sales = daily_sales.mean()
                std_sales = daily_sales.std()
                spikes = daily_sales[daily_sales > mean_sales + std_sales]

                if len(spikes) > 0:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {COLORS["accent"]}15, {COLORS["accent"]}08);
                        border: 1px solid {COLORS["accent"]}30;
                        border-radius: 8px;
                        padding: 1rem;
                        margin-top: 0.5rem;
                    ">
                        <div style="font-size: 0.85rem; font-weight: 600; color: {COLORS["text"]}; margin-bottom: 0.4rem;">
                            ⚡ 매출 스파이크 감지 ({len(spikes)}건)
                        </div>
                        <div style="font-size: 0.8rem; color: {COLORS["text_sub"]};">
                            평균+1σ 이상: {', '.join(d.strftime('%m/%d') for d in spikes.index[:5])}
                            {"..." if len(spikes) > 5 else ""}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


# --- 푸터 ---
st.markdown(f"""
<div style="
    text-align: center;
    padding: 1.5rem 0 1rem 0;
    color: {COLORS["text_sub"]};
    font-size: 0.75rem;
    border-top: 1px solid {COLORS["border"]};
    margin-top: 1.5rem;
">
    뉴믹스 마케팅 대시보드 &middot;
    마지막 업데이트: {datetime.now().strftime("%Y-%m-%d %H:%M")} &middot;
    데이터 기간: {df["date"].min().strftime("%Y-%m-%d")} ~ {df["date"].max().strftime("%Y-%m-%d")} &middot;
    매출 {len(df)}건 · 콘텐츠 {len(content_df)}건
</div>
""", unsafe_allow_html=True)
