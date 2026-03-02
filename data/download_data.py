"""NSMC (Naver Sentiment Movie Corpus) 데이터 다운로드 스크립트."""

import os
import urllib.request

BASE_URL = "https://raw.githubusercontent.com/e9t/nsmc/master"
FILES = ["ratings_train.txt", "ratings_test.txt"]
DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def download_nsmc():
    for filename in FILES:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            print(f"이미 존재함: {filepath}")
            continue
        url = f"{BASE_URL}/{filename}"
        print(f"다운로드 중: {url}")
        urllib.request.urlretrieve(url, filepath)
        print(f"저장 완료: {filepath}")


if __name__ == "__main__":
    download_nsmc()
