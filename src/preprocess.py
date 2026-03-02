"""한국어 텍스트 전처리 모듈: 토큰화, 불용어 제거, TF-IDF 벡터화."""

import re

import pandas as pd
from konlpy.tag import Okt

okt = Okt()

STOPWORDS = {
    "의", "가", "이", "은", "들", "는", "과",
    "도", "를", "으로", "자", "에", "와", "한", "에서",
    "로", "에게", "뿐", "의거", "것", "수", "거", "게",
    "그", "또", "다", "나", "너", "저",
    "우리", "그것", "이것", "저것", "여기", "거기", "저기",
    "때문", "위해", "통해", "대해", "관해",
}

# 감성 표현에 불필요한 품사만 제외 (조사, 접미사 등)
EXCLUDE_POS = {"Josa", "Suffix", "Punctuation"}


def tokenize(text):
    """Okt 형태소 분석기로 토큰화한다. 불필요한 품사와 불용어를 제거."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", "", text)
    tagged = okt.pos(text, stem=True)
    tokens = [
        word for word, pos in tagged
        if pos not in EXCLUDE_POS and word not in STOPWORDS and len(word) > 1
    ]
    return " ".join(tokens)


def load_data(filepath):
    """NSMC TSV 파일을 로드하고 결측치를 제거한다."""
    df = pd.read_csv(filepath, sep="\t")
    df = df.dropna(subset=["document"])
    df = df.drop_duplicates(subset=["document"])
    return df


def preprocess_dataframe(df):
    """데이터프레임의 document 컬럼을 토큰화한다."""
    df = df.copy()
    df["tokens"] = df["document"].apply(tokenize)
    df = df[df["tokens"].str.strip().astype(bool)]
    return df
