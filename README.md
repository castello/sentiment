# 한국어 감성분석 (Korean Sentiment Analysis)

NSMC(Naver Sentiment Movie Corpus) 데이터셋과 scikit-learn을 활용한 한국어 감성분석 모델입니다.

## 주요 특징

- **Okt 형태소 분석** 기반 한국어 텍스트 전처리
- **TF-IDF + GridSearchCV**로 4개 분류기 비교 (MultinomialNB, LogisticRegression, LinearSVC, SGDClassifier)
- **3분류 지원**: 2분류 학습 후 예측 확률 임계값으로 긍정/중립/부정 구분
- 최적 모델: **LogisticRegression (정확도 84.96%)**

## 빠른 시작

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. 데이터 다운로드
python data/download_data.py

# 3. 모델 학습
python src/train.py

# 4. 감성 예측
python src/predict.py "이 영화 정말 재밌다"
# → 감성: 긍정 / 신뢰도: 0.9797
```

## 프로젝트 구조

```
sentiment/
├── requirements.txt          # 의존성 (scikit-learn, pandas, konlpy, joblib)
├── data/
│   └── download_data.py      # NSMC 데이터 다운로드
├── src/
│   ├── preprocess.py         # 형태소 분석, 불용어 제거, TF-IDF
│   ├── train.py              # 모델 학습 및 평가
│   └── predict.py            # 감성 예측 (CLI)
├── models/                   # 학습된 모델 저장 (git 제외)
└── notebooks/
    └── eda.ipynb             # 전체 과정 노트북
```

## 3분류 전략

NSMC는 긍정(1)/부정(0) 2분류 데이터셋입니다. 추가 데이터 없이 3분류를 구현하기 위해:

| 긍정 확률 | 분류 |
|-----------|------|
| > 0.6 | 긍정 |
| 0.4 ~ 0.6 | 중립 |
| < 0.4 | 부정 |

## 모델 성능

| 모델 | 교차 검증 | 테스트 정확도 |
|------|-----------|---------------|
| MultinomialNB | 0.8442 | 0.8457 |
| **LogisticRegression** | **0.8464** | **0.8496** |
| LinearSVC | 0.8421 | 0.8465 |
| SGDClassifier | 0.8452 | 0.8471 |

## 기술 스택

| 패키지 | 용도 |
|--------|------|
| scikit-learn | ML 모델, TF-IDF, GridSearchCV |
| konlpy (Okt) | 한국어 형태소 분석 |
| pandas | 데이터 처리 |
| joblib | 모델 저장/로드 |
