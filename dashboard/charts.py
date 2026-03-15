"""
차트 컴포넌트 모듈

스타일가이드 기반 Plotly 차트를 제공합니다.
컬러 팔레트: 올리브 그린, 웜 오렌지, 소프트 옐로우, 틸 그린, 소프트 블루
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 스타일가이드 컬러 팔레트
COLORS = {
    "primary": "#849A6C",      # 올리브 그린
    "secondary": "#F27D42",    # 웜 오렌지
    "accent": "#F6C06B",       # 소프트 옐로우
    "sub": "#4A897F",          # 틸 그린
    "soft_blue": "#A8DADC",    # 소프트 블루
    "bg": "#FEFBF6",           # 웜 아이보리
    "text": "#333333",         # 다크 그레이
    "text_sub": "#888888",     # 미디엄 그레이
    "border": "#EAEAEA",       # 라이트 그레이
}

# 국가별 색상 (스타일가이드 차트 컬러)
COUNTRY_COLORS = {
    "일본": COLORS["secondary"],   # 웜 오렌지
    "대만": COLORS["primary"],     # 올리브 그린
    "중국": COLORS["sub"],         # 틸 그린
}

COUNTRY_ORDER = ["일본", "대만", "중국"]


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """HEX 색상을 rgba 문자열로 변환합니다."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# 공통 레이아웃 설정
_LAYOUT_COMMON = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Pretendard, sans-serif", color=COLORS["text"], size=13),
    margin=dict(t=45, b=25, l=25, r=25),
    hoverlabel=dict(
        bgcolor="white",
        font_size=13,
        font_family="Pretendard, sans-serif",
        bordercolor=COLORS["border"],
    ),
)


def create_dataframe(records: list[dict]) -> pd.DataFrame:
    """매출 데이터를 DataFrame으로 변환합니다."""
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["sales"] = df["sales"].astype(int)
    return df


def sales_pie_chart(df: pd.DataFrame, period: str = "전체") -> go.Figure:
    """국가별 매출 비중 도넛 차트."""
    totals = df.groupby("country")["sales"].sum().reset_index()

    fig = px.pie(
        totals,
        values="sales",
        names="country",
        color="country",
        color_discrete_map=COUNTRY_COLORS,
        hole=0.55,
        category_orders={"country": COUNTRY_ORDER},
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont=dict(size=14, family="Pretendard, sans-serif"),
        marker=dict(line=dict(color="white", width=2)),
        hovertemplate="<b>%{label}</b><br>매출: %{value:,.0f}원<br>비중: %{percent}<extra></extra>",
    )
    fig.update_layout(
        **_LAYOUT_COMMON,
        title=dict(
            text=f"매출 비중 ({period})",
            font=dict(size=16, family="NanumSquareRound, Pretendard, sans-serif"),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        height=380,
    )
    return fig


def sales_trend_chart(df: pd.DataFrame) -> go.Figure:
    """국가별 매출 추이 라인차트."""
    fig = go.Figure()

    for country in COUNTRY_ORDER:
        cdf = df[df["country"] == country].sort_values("date")
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["date"],
            y=cdf["sales"],
            name=country,
            mode="lines+markers",
            line=dict(width=2.5, color=COUNTRY_COLORS[country], shape="spline"),
            marker=dict(size=5, color=COUNTRY_COLORS[country]),
            hovertemplate=f"<b>{country}</b><br>%{{x|%m/%d}}<br>매출: %{{y:,.0f}}원<extra></extra>",
        ))

    fig.update_layout(
        **_LAYOUT_COMMON,
        title=dict(
            text="일간 매출 추이",
            font=dict(size=16, family="NanumSquareRound, Pretendard, sans-serif"),
        ),
        height=420,
        hovermode="x unified",
        xaxis=dict(
            showgrid=False,
            tickformat="%m/%d",
            dtick="D7",
        ),
        yaxis=dict(
            tickformat=",",
            gridcolor=COLORS["border"],
            gridwidth=0.5,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def sales_bar_chart(df: pd.DataFrame) -> go.Figure:
    """국가별 매출 비교 막대차트."""
    fig = px.bar(
        df,
        x="date",
        y="sales",
        color="country",
        color_discrete_map=COUNTRY_COLORS,
        barmode="group",
        category_orders={"country": COUNTRY_ORDER},
    )
    fig.update_layout(
        **_LAYOUT_COMMON,
        title=dict(
            text="국가별 매출 비교",
            font=dict(size=16, family="NanumSquareRound, Pretendard, sans-serif"),
        ),
        height=420,
        xaxis=dict(showgrid=False, tickformat="%m/%d"),
        yaxis=dict(tickformat=",", gridcolor=COLORS["border"], gridwidth=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_traces(
        marker_line_width=0,
        marker_cornerradius=6,
        hovertemplate="<b>%{x|%m/%d}</b><br>매출: %{y:,.0f}원<extra></extra>",
    )
    return fig


def sales_stacked_area(df: pd.DataFrame) -> go.Figure:
    """국가별 매출 누적 영역 차트."""
    fig = go.Figure()

    for country in COUNTRY_ORDER:
        cdf = df[df["country"] == country].sort_values("date")
        if cdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=cdf["date"],
            y=cdf["sales"],
            name=country,
            mode="lines",
            stackgroup="one",
            line=dict(width=1, color=COUNTRY_COLORS[country], shape="spline"),
            fillcolor=_hex_to_rgba(COUNTRY_COLORS[country], 0.25),
            hovertemplate=f"<b>{country}</b><br>%{{x|%m/%d}}<br>매출: %{{y:,.0f}}원<extra></extra>",
        ))

    fig.update_layout(
        **_LAYOUT_COMMON,
        title=dict(
            text="매출 추이 (누적)",
            font=dict(size=16, family="NanumSquareRound, Pretendard, sans-serif"),
        ),
        height=420,
        hovermode="x unified",
        xaxis=dict(showgrid=False, tickformat="%m/%d"),
        yaxis=dict(tickformat=",", gridcolor=COLORS["border"], gridwidth=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def sales_change_metrics(df: pd.DataFrame) -> dict:
    """전일/전주 대비 매출 변동률을 계산합니다."""
    metrics = {}
    latest_date = df["date"].max()

    for country in COUNTRY_ORDER:
        cdf = df[df["country"] == country].sort_values("date")
        if cdf.empty:
            continue

        latest = cdf[cdf["date"] == latest_date]["sales"]
        latest_val = int(latest.iloc[0]) if len(latest) > 0 else 0

        prev_day = cdf[cdf["date"] == latest_date - pd.Timedelta(days=1)]["sales"]
        prev_day_val = int(prev_day.iloc[0]) if len(prev_day) > 0 else 0

        prev_week = cdf[cdf["date"] == latest_date - pd.Timedelta(days=7)]["sales"]
        prev_week_val = int(prev_week.iloc[0]) if len(prev_week) > 0 else 0

        day_change = ((latest_val - prev_day_val) / prev_day_val * 100) if prev_day_val else 0
        week_change = ((latest_val - prev_week_val) / prev_week_val * 100) if prev_week_val else 0

        # 국가별 총 매출 비중
        total = df["sales"].sum()
        country_total = cdf["sales"].sum()
        share_pct = (country_total / total * 100) if total else 0

        metrics[country] = {
            "latest": latest_val,
            "prev_day": prev_day_val,
            "prev_week": prev_week_val,
            "day_change_pct": round(day_change, 1),
            "week_change_pct": round(week_change, 1),
            "share_pct": round(share_pct, 1),
        }

    return metrics


# ============================================================
# 콘텐츠 트래커 차트
# ============================================================

PLATFORM_COLORS = {
    "Instagram": "#E1306C",
    "TikTok": "#000000",
    "샤오홍슈": "#FF2442",
    "YouTube": "#FF0000",
    "X": "#1DA1F2",
    "블로그": COLORS["primary"],
}

PLATFORM_ICONS = {
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "xiaohongshu": "샤오홍슈",
    "youtube": "YouTube",
    "x": "X",
    "blog": "블로그",
}


def create_content_dataframe(records: list[dict]) -> pd.DataFrame:
    """콘텐츠 데이터를 DataFrame으로 변환합니다."""
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    for col in ("likes", "comments", "saves", "views", "followers"):
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0).astype(int)
    df["platform_name"] = df["platform"].map(PLATFORM_ICONS).fillna(df["platform"])
    df["engagement"] = df["likes"] + df["comments"] + df["saves"]
    return df


def content_by_platform_chart(df: pd.DataFrame) -> go.Figure:
    """플랫폼별 포스팅 수 도넛 차트."""
    counts = df.groupby("platform_name").size().reset_index(name="count")

    fig = px.pie(
        counts,
        values="count",
        names="platform_name",
        color="platform_name",
        color_discrete_map=PLATFORM_COLORS,
        hole=0.55,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont=dict(size=13, family="Pretendard, sans-serif"),
        marker=dict(line=dict(color="white", width=2)),
        hovertemplate="<b>%{label}</b><br>포스팅: %{value}건<br>비중: %{percent}<extra></extra>",
    )
    fig.update_layout(
        **_LAYOUT_COMMON,
        title=dict(
            text="플랫폼별 포스팅",
            font=dict(size=16, family="NanumSquareRound, Pretendard, sans-serif"),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        height=350,
    )
    return fig


def content_by_country_chart(df: pd.DataFrame) -> go.Figure:
    """국가별 포스팅 수 + 평균 반응 막대 차트."""
    grouped = df.groupby("country").agg(
        posts=("url", "count"),
        avg_likes=("likes", "mean"),
        avg_views=("views", "mean"),
    ).reset_index()

    fig = go.Figure()
    for _, row in grouped.iterrows():
        color = COUNTRY_COLORS.get(row["country"], COLORS["soft_blue"])
        fig.add_trace(go.Bar(
            x=[row["country"]],
            y=[row["posts"]],
            name=row["country"],
            marker_color=color,
            marker_cornerradius=6,
            text=[f'{row["posts"]}건'],
            textposition="outside",
            hovertemplate=(
                f"<b>{row['country']}</b><br>"
                f"포스팅: {row['posts']}건<br>"
                f"평균 좋아요: {row['avg_likes']:,.0f}<br>"
                f"평균 조회수: {row['avg_views']:,.0f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_LAYOUT_COMMON,
        title=dict(
            text="국가별 포스팅",
            font=dict(size=16, family="NanumSquareRound, Pretendard, sans-serif"),
        ),
        showlegend=False,
        height=350,
        yaxis=dict(gridcolor=COLORS["border"], gridwidth=0.5),
    )
    return fig


def content_timeline_chart(df: pd.DataFrame, sales_df: pd.DataFrame = None) -> go.Figure:
    """콘텐츠 포스팅 타임라인 + 매출 오버레이."""
    daily = df.groupby("date").agg(
        posts=("url", "count"),
        total_engagement=("engagement", "sum"),
    ).reset_index()

    fig = go.Figure()

    # 포스팅 수 (막대)
    fig.add_trace(go.Bar(
        x=daily["date"],
        y=daily["posts"],
        name="포스팅 수",
        marker_color=COLORS["accent"],
        marker_cornerradius=6,
        opacity=0.7,
        yaxis="y",
        hovertemplate="<b>%{x|%m/%d}</b><br>포스팅: %{y}건<extra></extra>",
    ))

    # 매출 오버레이 (라인)
    if sales_df is not None and not sales_df.empty:
        daily_sales = sales_df.groupby("date")["sales"].sum().reset_index()
        fig.add_trace(go.Scatter(
            x=daily_sales["date"],
            y=daily_sales["sales"],
            name="총 매출",
            mode="lines+markers",
            line=dict(width=2.5, color=COLORS["primary"], shape="spline"),
            marker=dict(size=4),
            yaxis="y2",
            hovertemplate="<b>%{x|%m/%d}</b><br>매출: %{y:,.0f}원<extra></extra>",
        ))

    fig.update_layout(
        **_LAYOUT_COMMON,
        title=dict(
            text="콘텐츠 × 매출 타임라인",
            font=dict(size=16, family="NanumSquareRound, Pretendard, sans-serif"),
        ),
        height=420,
        hovermode="x unified",
        xaxis=dict(showgrid=False, tickformat="%m/%d"),
        yaxis=dict(
            title="포스팅 수",
            gridcolor=COLORS["border"],
            gridwidth=0.5,
            side="left",
        ),
        yaxis2=dict(
            title="매출 (원)",
            overlaying="y",
            side="right",
            tickformat=",",
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        barmode="stack",
    )
    return fig


def content_engagement_scatter(df: pd.DataFrame) -> go.Figure:
    """팔로워 수 vs 반응률 스캐터 차트."""
    plot_df = df[df["followers"] > 0].copy()
    if plot_df.empty:
        plot_df = df.copy()
        plot_df["followers"] = plot_df["followers"].replace(0, 1000)

    plot_df["engagement_rate"] = (
        plot_df["engagement"] / plot_df["followers"].replace(0, 1) * 100
    )

    fig = px.scatter(
        plot_df,
        x="followers",
        y="engagement_rate",
        color="country",
        color_discrete_map={**COUNTRY_COLORS, "기타": COLORS["soft_blue"]},
        size="engagement",
        hover_name="author",
        hover_data={
            "platform_name": True,
            "likes": True,
            "views": True,
            "followers": ":,",
            "engagement_rate": ":.1f",
            "engagement": False,
        },
        labels={
            "followers": "팔로워 수",
            "engagement_rate": "반응률 (%)",
            "platform_name": "플랫폼",
        },
    )
    fig.update_layout(
        **_LAYOUT_COMMON,
        title=dict(
            text="인플루언서 반응률",
            font=dict(size=16, family="NanumSquareRound, Pretendard, sans-serif"),
        ),
        height=420,
        xaxis=dict(showgrid=False, tickformat=","),
        yaxis=dict(gridcolor=COLORS["border"], gridwidth=0.5, ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
