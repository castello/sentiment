"""FastAPI 백엔드 — 뉴스 감성분석 API.

실행: uvicorn src.api:app --reload --port 8000
"""

import os
import sys
from collections import Counter
from contextlib import asynccontextmanager
from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import numpy as np
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException
from googlenewsdecoder import gnewsdecoder
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.news import analyze_article, split_sentences
from src.predict import load_model, predict_sentiment
from src.preprocess import tokenize

# 전역 모델 저장소
_model = None
_tfidf = None

# 뉴스 캐시 (10분 TTL, 최대 10 항목)
_news_cache = TTLCache(maxsize=10, ttl=600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 모델을 1회 로드한다."""
    global _model, _tfidf
    _model, _tfidf = load_model()
    yield


app = FastAPI(title="뉴스 감성분석 API", lifespan=lifespan)


class AnalyzeRequest(BaseModel):
    url: str


class AnalyzeTextRequest(BaseModel):
    text: str


def _fetch_latest_news(n: int = 50):
    """Google News Korea RSS에서 최신 뉴스를 가져온다."""
    cache_key = f"news_{n}"
    if cache_key in _news_cache:
        return _news_cache[cache_key]

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

    _news_cache[cache_key] = articles
    return articles


def _resolve_google_news_url(url: str) -> str:
    """Google News 리다이렉트 URL을 실제 기사 URL로 변환한다."""
    if "news.google.com" not in url:
        return url
    try:
        decoded = gnewsdecoder(url)
        if decoded.get("success"):
            return decoded["decoded_url"]
        return url
    except Exception:
        return url


def _extract_keywords(sentences: list) -> dict:
    """문장 리스트에서 빈도수 및 TF-IDF 키워드를 추출한다."""
    all_text = " ".join(s["sentence"] for s in sentences)
    tokens = tokenize(all_text).split()

    # 빈도수 Top 10
    top10_freq = Counter(tokens).most_common(10)
    frequency = [{"keyword": word, "count": count} for word, count in top10_freq]

    # TF-IDF Top 10
    vec = _tfidf.transform([" ".join(tokens)])
    feature_names = np.array(_tfidf.get_feature_names_out())
    scores = vec.toarray().flatten()
    top_idx = scores.argsort()[::-1]

    seen = set()
    tfidf_top10 = []
    for idx in top_idx:
        word = feature_names[idx]
        if " " not in word and word not in seen:
            seen.add(word)
            tfidf_top10.append({"keyword": word, "score": round(float(scores[idx]), 4)})
        if len(tfidf_top10) == 10:
            break

    return {"frequency": frequency, "tfidf": tfidf_top10}


@app.get("/api/news")
def get_news(count: int = 50):
    """최신 뉴스 목록을 반환한다 (10분 캐시)."""
    try:
        articles = _fetch_latest_news(n=count)
        return articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
def post_analyze(req: AnalyzeRequest):
    """단일 URL 감성분석 (키워드 분석 포함)."""
    try:
        resolved_url = _resolve_google_news_url(req.url)
        result = analyze_article(resolved_url)
        result["keywords"] = _extract_keywords(result["sentences"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-text")
def post_analyze_text(req: AnalyzeTextRequest):
    """직접 입력 텍스트 감성분석 (키워드 분석 포함)."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="텍스트를 입력해주세요.")

    try:
        sentences = split_sentences(req.text)
        if not sentences:
            raise HTTPException(status_code=400, detail="분석할 문장이 없습니다.")

        results = []
        for sentence in sentences:
            label, confidence = predict_sentiment(sentence, _model, _tfidf)
            results.append({
                "sentence": sentence,
                "label": label,
                "confidence": confidence,
            })

        counts = {"긍정": 0, "중립": 0, "부정": 0}
        for r in results:
            counts[r["label"]] += 1

        total = len(results)
        ratios = {k: v / total * 100 for k, v in counts.items()}
        overall = max(counts, key=counts.get)

        response = {
            "title": "직접 입력 텍스트",
            "sentences": results,
            "summary": {
                "total_sentences": total,
                "counts": counts,
                "ratios": ratios,
                "overall": overall,
            },
        }
        response["keywords"] = _extract_keywords(results)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
