"""새 텍스트의 감성을 예측하는 스크립트.

저장된 모델을 로드하여 긍정/중립/부정 3분류 예측을 수행한다.
2분류 모델의 예측 확률을 기반으로 중립을 구분한다.
"""

import os
import sys

import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.preprocess import tokenize

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

NEUTRAL_LOW = 0.4
NEUTRAL_HIGH = 0.6


def load_model():
    model_path = os.path.join(MODEL_DIR, "best_model.joblib")
    tfidf_path = os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib")

    if not os.path.exists(model_path):
        print("모델 파일이 없습니다. 먼저 python src/train.py를 실행하세요.")
        sys.exit(1)

    model = joblib.load(model_path)
    tfidf = joblib.load(tfidf_path)
    return model, tfidf


def predict_sentiment(text, model, tfidf):
    """텍스트의 감성을 예측한다.

    Returns:
        (label, confidence): 감성 라벨과 신뢰도
    """
    tokens = tokenize(text)
    vec = tfidf.transform([tokens])

    # predict_proba를 지원하는 모델이면 확률 기반 3분류
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(vec)[0]
        pos_prob = proba[1]  # 긍정 확률

        if NEUTRAL_LOW <= pos_prob <= NEUTRAL_HIGH:
            return "중립", pos_prob
        elif pos_prob > NEUTRAL_HIGH:
            return "긍정", pos_prob
        else:
            return "부정", 1 - pos_prob
    else:
        # LinearSVC 등 확률 미지원 모델 → decision_function 사용
        decision = model.decision_function(vec)[0]
        if -0.5 <= decision <= 0.5:
            return "중립", abs(decision)
        elif decision > 0.5:
            return "긍정", decision
        else:
            return "부정", abs(decision)


def main():
    if len(sys.argv) < 2:
        print("사용법: python src/predict.py \"분석할 텍스트\"")
        sys.exit(1)

    text = sys.argv[1]
    model, tfidf = load_model()
    label, confidence = predict_sentiment(text, model, tfidf)

    print(f"입력: {text}")
    print(f"감성: {label}")
    print(f"신뢰도: {confidence:.4f}")


if __name__ == "__main__":
    main()
