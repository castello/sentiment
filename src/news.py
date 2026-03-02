"""뉴스 기사 URL 감성분석 모듈.

URL에서 뉴스 본문을 크롤링하고, 문장 단위로 감성분석한 뒤
전체 기사의 종합 감성을 반환한다.
"""

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.predict import load_model, predict_sentiment

import requests
from bs4 import BeautifulSoup
import kss
from newspaper import Article
from newspaper.article import ArticleException

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _fallback_fetch(url):
    """newspaper3k 실패 시 requests+BeautifulSoup로 본문을 추출한다."""
    resp = requests.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title:
        title = og_title.get("content", "")
    if not title:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

    # 1) article / [itemprop=articleBody] 등 시맨틱 태그
    text = ""
    for selector in ["[itemprop=articleBody]", "article", ".article-body"]:
        el = soup.select_one(selector)
        if el:
            paragraphs = el.find_all("p")
            body = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)
            if body:
                text = body
                break

    # 2) 전체 p 태그
    if not text:
        paragraphs = soup.find_all("p")
        body = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)
        if body:
            text = body

    # 3) meta description 폴백 (더 긴 쪽 사용)
    if not text:
        candidates = []
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            candidates.append(og_desc.get("content", ""))
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            candidates.append(meta_desc.get("content", ""))
        if candidates:
            text = max(candidates, key=len)

    return title, text


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

    # newspaper3k 실패 시 폴백
    if not text.strip():
        title, text = _fallback_fetch(url)

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


def analyze_articles(urls):
    """여러 URL을 배치 분석한다. 실패한 URL은 건너뛰고 에러 메시지를 포함한다."""
    results = []
    for url in urls:
        try:
            result = analyze_article(url)
            results.append(result)
        except (ValueError, Exception) as e:
            results.append({"url": url, "error": str(e)})
    return results


def export_json(results, filepath):
    """분석 결과를 JSON 파일로 저장한다."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def export_csv(results, filepath):
    """기사별 요약을 CSV 파일로 저장한다."""
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["제목", "전체 감성", "긍정(%)", "중립(%)", "부정(%)"])
        for r in results:
            if "error" in r:
                writer.writerow([r.get("url", ""), f"오류: {r['error']}", "", "", ""])
            else:
                s = r["summary"]
                writer.writerow([
                    r["title"],
                    s["overall"],
                    f"{s['ratios']['긍정']:.1f}",
                    f"{s['ratios']['중립']:.1f}",
                    f"{s['ratios']['부정']:.1f}",
                ])


def print_result(result):
    """단일 분석 결과를 터미널에 출력한다."""
    if "error" in result:
        print(f"오류 ({result.get('url', '')}): {result['error']}")
        return

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


def main():
    parser = argparse.ArgumentParser(description="뉴스 기사 감성분석")
    parser.add_argument("urls", nargs="+", help="분석할 뉴스 기사 URL (하나 이상)")
    parser.add_argument("--output", "-o", help="결과 저장 경로 (.json 또는 .csv)")
    args = parser.parse_args()

    results = analyze_articles(args.urls)

    for result in results:
        print_result(result)
        print()

    if args.output:
        ext = os.path.splitext(args.output)[1].lower()
        if ext == ".json":
            export_json(results, args.output)
        elif ext == ".csv":
            export_csv(results, args.output)
        else:
            print(f"지원하지 않는 파일 형식: {ext} (.json 또는 .csv만 지원)")
            sys.exit(1)
        print(f"결과 저장 완료: {args.output}")


if __name__ == "__main__":
    main()
