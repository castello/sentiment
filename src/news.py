"""뉴스 기사 URL 감성분석 모듈.

URL에서 뉴스 본문을 크롤링하고, 문장 단위로 감성분석한 뒤
전체 기사의 종합 감성을 반환한다.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.predict import load_model, predict_sentiment

import kss
from newspaper import Article
from newspaper.article import ArticleException


def fetch_article(url):
    """URL에서 뉴스 기사 제목과 본문을 추출한다."""
    try:
        article = Article(url, language="ko")
        article.download()
        article.parse()
    except ArticleException as e:
        raise ValueError(f"기사를 가져올 수 없습니다: {e}")

    title = article.title
    text = article.text

    if not text.strip():
        raise ValueError("기사 본문을 추출할 수 없습니다.")

    return title, text


def split_sentences(text):
    """한국어 텍스트를 문장 단위로 분리한다."""
    sentences = kss.split_sentences(text, backend="pecab")
    # 빈 문장 제거
    return [s.strip() for s in sentences if s.strip()]


def analyze_article(url):
    """뉴스 기사 URL을 받아 문장별 감성분석 및 종합 결과를 반환한다."""
    title, text = fetch_article(url)
    sentences = split_sentences(text)

    if not sentences:
        raise ValueError("분석할 문장이 없습니다.")

    model, tfidf = load_model()

    results = []
    for sentence in sentences:
        label, confidence = predict_sentiment(sentence, model, tfidf)
        results.append({
            "sentence": sentence,
            "label": label,
            "confidence": confidence,
        })

    # 종합 집계
    counts = {"긍정": 0, "중립": 0, "부정": 0}
    for r in results:
        counts[r["label"]] += 1

    total = len(results)
    ratios = {k: v / total * 100 for k, v in counts.items()}
    overall = max(counts, key=counts.get)

    return {
        "title": title,
        "sentences": results,
        "summary": {
            "total_sentences": total,
            "counts": counts,
            "ratios": ratios,
            "overall": overall,
        },
    }


def main():
    if len(sys.argv) < 2:
        print("사용법: python src/news.py <뉴스 기사 URL>")
        sys.exit(1)

    url = sys.argv[1]
    print(f"기사 분석 중: {url}\n")

    try:
        result = analyze_article(url)
    except ValueError as e:
        print(f"오류: {e}")
        sys.exit(1)

    print(f"제목: {result['title']}")
    print(f"총 문장 수: {result['summary']['total_sentences']}")
    print("-" * 60)

    for i, s in enumerate(result["sentences"], 1):
        print(f"[{i}] ({s['label']}, {s['confidence']:.4f}) {s['sentence']}")

    print("-" * 60)
    summary = result["summary"]
    print("종합 결과:")
    print(f"  긍정: {summary['counts']['긍정']}문장 ({summary['ratios']['긍정']:.1f}%)")
    print(f"  중립: {summary['counts']['중립']}문장 ({summary['ratios']['중립']:.1f}%)")
    print(f"  부정: {summary['counts']['부정']}문장 ({summary['ratios']['부정']:.1f}%)")
    print(f"  전체 감성: {summary['overall']}")


if __name__ == "__main__":
    main()
