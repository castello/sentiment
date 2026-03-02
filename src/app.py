"""Streamlit 웹 UI — 뉴스 기사 감성분석 시각화.

실행: streamlit run src/app.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collections import Counter
from datetime import date, timezone, timedelta
from email.utils import parsedate_to_datetime

import numpy as np
import streamlit as st
import pandas as pd
import feedparser
from googlenewsdecoder import gnewsdecoder
from src.news import analyze_article
from src.predict import load_model
from src.preprocess import tokenize


st.set_page_config(page_title="뉴스 감성분석", layout="wide")
st.title("뉴스 기사 감성분석")


@st.cache_data(ttl=600)
def fetch_latest_news(n=50):
    """Google News Korea RSS에서 최신 뉴스를 가져온다."""
    feed = feedparser.parse(
        "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    )
    kst = timezone(timedelta(hours=9))
    articles = []
    for entry in feed.entries[:n]:
        published = ""
        try:
            dt = parsedate_to_datetime(entry.get("published", ""))
            published = dt.astimezone(kst).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass
        articles.append({
            "title": entry.title,
            "url": entry.link,
            "source": entry.get("source", {}).get("title", ""),
            "published": published,
        })
    return articles


def resolve_google_news_url(url):
    """Google News 리다이렉트 URL을 실제 기사 URL로 변환한다."""
    if "news.google.com" not in url:
        return url
    try:
        decoded = gnewsdecoder(url)
        if decoded.get("status"):
            return decoded["decoded_url"]
        return url
    except Exception:
        return url


@st.cache_data(ttl=3600, show_spinner=False)
def cached_analyze(url):
    """분석 결과를 캐싱한다."""
    resolved = resolve_google_news_url(url)
    return analyze_article(resolved)


def display_result(result):
    """분석 결과를 화면에 표시한다."""
    st.header(result["title"])

    summary = result["summary"]

    # 종합 감성 비율
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("종합 감성")
        st.metric("전체 감성", summary["overall"])
        st.metric("총 문장 수", summary["total_sentences"])

    with col2:
        st.subheader("감성 비율")
        pie_df = pd.DataFrame({
            "감성": ["긍정", "중립", "부정"],
            "비율": [
                summary["ratios"]["긍정"],
                summary["ratios"]["중립"],
                summary["ratios"]["부정"],
            ],
        })
        st.bar_chart(pie_df.set_index("감성"))

    # 키워드 분석
    all_text = " ".join(s["sentence"] for s in result["sentences"])
    tokens = tokenize(all_text).split()

    kw_col1, kw_col2 = st.columns(2)

    with kw_col1:
        st.subheader("키워드 빈도수 Top 10")
        top10_freq = Counter(tokens).most_common(10)
        freq_df = pd.DataFrame(top10_freq, columns=["키워드", "빈도수"])
        freq_df.index = range(1, len(freq_df) + 1)
        freq_df.index.name = "순위"
        st.table(freq_df)

    with kw_col2:
        st.subheader("TF-IDF 핵심 키워드 Top 10")
        _, tfidf = load_model()
        vec = tfidf.transform([" ".join(tokens)])
        feature_names = np.array(tfidf.get_feature_names_out())
        scores = vec.toarray().flatten()
        top_idx = scores.argsort()[::-1]
        seen = set()
        tfidf_top10 = []
        for idx in top_idx:
            word = feature_names[idx]
            if " " not in word and word not in seen:
                seen.add(word)
                tfidf_top10.append((word, round(float(scores[idx]), 4)))
            if len(tfidf_top10) == 10:
                break
        tfidf_df = pd.DataFrame(tfidf_top10, columns=["키워드", "TF-IDF 점수"])
        tfidf_df.index = range(1, len(tfidf_df) + 1)
        tfidf_df.index.name = "순위"
        st.table(tfidf_df)

    # 문장별 감성 테이블
    st.subheader("문장별 분석 결과")
    sentences_df = pd.DataFrame([
        {
            "번호": i,
            "문장": s["sentence"],
            "감성": s["label"],
            "신뢰도": f"{s['confidence']:.4f}",
        }
        for i, s in enumerate(result["sentences"], 1)
    ])
    st.dataframe(sentences_df, use_container_width=True, hide_index=True)


# --- 메인 UI ---
tab1, tab2 = st.tabs(["최신 뉴스", "URL 직접 입력"])

with tab1:
    # 개수 선택 & 뉴스 가져오기
    count_options = {"5": 5, "10": 10, "20": 20, "50": 50, "100": 100, "전부": 9999}
    filter_col0, filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([0.4, 3, 1, 0.5, 0.5, 0.5])
    with filter_col0:
        count_label = st.selectbox("개수", list(count_options.keys()), index=3, label_visibility="collapsed")
    news_list = fetch_latest_news(n=count_options[count_label])

    # 검색 & 필터
    with filter_col1:
        search_query = st.text_input("검색", placeholder="제목 키워드로 검색", label_visibility="collapsed")
    with filter_col2:
        sources = sorted(set(n["source"] for n in news_list if n["source"]))
        source_filter = st.selectbox("언론사", ["전체"] + sources, label_visibility="collapsed")
    with filter_col3:
        date_from = st.date_input("시작일", value=date.today(), label_visibility="collapsed")
    with filter_col4:
        date_to = st.date_input("종료일", value=date.today(), label_visibility="collapsed")
    with filter_col5:
        st.button("조회", use_container_width=True)

    # 필터 적용
    filtered = news_list
    if search_query:
        filtered = [n for n in filtered if search_query.lower() in n["title"].lower()]
    if source_filter != "전체":
        filtered = [n for n in filtered if n["source"] == source_filter]
    if date_from and date_to:
        def _in_range(pub):
            if not pub:
                return False
            try:
                return date_from <= date.fromisoformat(pub[:10]) <= date_to
            except ValueError:
                return True
        filtered = [n for n in filtered if _in_range(n["published"])]

    # 페이지네이션
    page_size = 10
    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)

    if "news_page" not in st.session_state:
        st.session_state.news_page = 1
    if st.session_state.news_page > total_pages:
        st.session_state.news_page = total_pages

    current_page = st.session_state.news_page
    start = (current_page - 1) * page_size
    page_items = filtered[start:start + page_size]

    display_df = pd.DataFrame([
        {"번호": start + i + 1, "제목": n["title"], "언론사": n["source"], "발행시간": n["published"]}
        for i, n in enumerate(page_items)
    ])

    st.caption(f"총 {total}건")
    selected = st.dataframe(
        display_df,
        use_container_width=True,
        height=450,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "번호": st.column_config.NumberColumn(width="small"),
            "제목": st.column_config.TextColumn(width="large"),
            "언론사": st.column_config.TextColumn(width="small"),
            "발행시간": st.column_config.TextColumn(width="small"),
        },
    )

    if selected and selected.selection.rows:
        row_idx = selected.selection.rows[0]
        st.session_state.analyze_url = page_items[row_idx]["url"]

    # 페이지 네비게이터 (고정 14칸: 패딩 + « + ‹ + 10페이지 + › + » + 패딩)
    block_size = 10
    current_block = (current_page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = min(block_start + block_size - 1, total_pages)
    page_nums = list(range(block_start, block_end + 1))

    col_widths = [1, 0.4, 0.4] + [0.4] * block_size + [0.4, 0.4, 1]
    nav_cols = st.columns(col_widths)

    with nav_cols[1]:
        if st.button("«", key="pg_first", disabled=current_page == 1):
            st.session_state.news_page = 1
            st.rerun()
    with nav_cols[2]:
        if st.button("‹", key="pg_prev", disabled=block_start == 1):
            st.session_state.news_page = block_start - 1
            st.rerun()
    for i in range(block_size):
        with nav_cols[3 + i]:
            if i < len(page_nums):
                p = page_nums[i]
                btn_type = "primary" if p == current_page else "secondary"
                if st.button(str(p), key=f"pg_{p}", type=btn_type, use_container_width=True):
                    st.session_state.news_page = p
                    st.rerun()
    with nav_cols[-2]:
        if st.button("›", key="pg_next", disabled=block_end >= total_pages):
            st.session_state.news_page = block_end + 1
            st.rerun()
    with nav_cols[-1]:
        if st.button("»", key="pg_last", disabled=current_page == total_pages):
            st.session_state.news_page = total_pages
            st.rerun()

with tab2:
    url = st.text_input("뉴스 기사 URL을 입력하세요")
    if st.button("분석 시작") and url:
        st.session_state.analyze_url = url

# --- 분석 결과 표시 ---
if st.session_state.get("analyze_url"):
    st.divider()
    with st.spinner("기사를 분석하고 있습니다..."):
        try:
            result = cached_analyze(st.session_state.analyze_url)
        except (ValueError, Exception) as e:
            st.error(f"오류: {e}")
            st.stop()
    display_result(result)
