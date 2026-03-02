"""Streamlit 웹 UI — 뉴스 기사 감성분석 시각화.

실행: streamlit run src/app.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collections import Counter

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
    articles = []
    for entry in feed.entries[:n]:
        articles.append({
            "title": entry.title,
            "url": entry.link,
            "source": entry.get("source", {}).get("title", ""),
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
    news_list = fetch_latest_news()
    with st.container(height=450):
        for i, news in enumerate(news_list):
            source_label = f" — {news['source']}" if news["source"] else ""
            if st.button(
                f"{news['title']}{source_label}",
                key=f"news_{i}",
                use_container_width=True,
            ):
                st.session_state.analyze_url = news["url"]

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
