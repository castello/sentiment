"""모델 학습 및 평가 스크립트.

여러 분류기(Naive Bayes, Logistic Regression, LinearSVC)를 비교하고
최적 모델을 저장한다.
"""

import os
import sys

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.preprocess import load_data, preprocess_dataframe

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def train():
    # 데이터 로드
    print("데이터 로드 중...")
    train_df = load_data(os.path.join(DATA_DIR, "ratings_train.txt"))
    test_df = load_data(os.path.join(DATA_DIR, "ratings_test.txt"))

    # 전처리
    print("전처리 중 (시간이 걸릴 수 있습니다)...")
    train_df = preprocess_dataframe(train_df)
    test_df = preprocess_dataframe(test_df)

    X_train_text = train_df["tokens"]
    y_train = train_df["label"]
    X_test_text = test_df["tokens"]
    y_test = test_df["label"]

    # TF-IDF 벡터화 (sublinear_tf, min_df, ngram 확대)
    print("TF-IDF 벡터화 중...")
    tfidf = TfidfVectorizer(
        max_features=80000,
        ngram_range=(1, 3),
        sublinear_tf=True,
        min_df=3,
        max_df=0.9,
    )
    X_train = tfidf.fit_transform(X_train_text)
    X_test = tfidf.transform(X_test_text)

    # 분류기 정의 + GridSearchCV로 하이퍼파라미터 탐색
    classifiers = {
        "MultinomialNB": {
            "model": MultinomialNB(),
            "params": {"alpha": [0.01, 0.1, 0.5, 1.0]},
        },
        "LogisticRegression": {
            "model": LogisticRegression(max_iter=1000),
            "params": {"C": [0.5, 1.0, 2.0, 5.0]},
        },
        "LinearSVC": {
            "model": LinearSVC(max_iter=2000),
            "params": {"C": [0.5, 1.0, 2.0, 5.0]},
        },
        "SGDClassifier": {
            "model": SGDClassifier(loss="modified_huber", max_iter=1000),
            "params": {"alpha": [1e-4, 1e-5, 1e-6]},
        },
    }

    best_name = None
    best_score = 0
    best_model = None

    for name, config in classifiers.items():
        print(f"\n{'='*50}")
        print(f"모델: {name}")
        print(f"{'='*50}")

        # GridSearchCV로 최적 파라미터 탐색
        grid = GridSearchCV(
            config["model"], config["params"],
            cv=5, scoring="accuracy", n_jobs=-1,
        )
        grid.fit(X_train, y_train)
        clf = grid.best_estimator_
        print(f"최적 파라미터: {grid.best_params_}")
        print(f"교차 검증 정확도: {grid.best_score_:.4f}")

        # 테스트
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"테스트 정확도: {acc:.4f}")
        print(f"\n분류 보고서:\n{classification_report(y_test, y_pred, target_names=['부정', '긍정'])}")
        print(f"혼동 행렬:\n{confusion_matrix(y_test, y_pred)}")

        if acc > best_score:
            best_score = acc
            best_name = name
            best_model = clf

    # 최적 모델 저장
    print(f"\n{'='*50}")
    print(f"최적 모델: {best_name} (정확도: {best_score:.4f})")
    print(f"{'='*50}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, "best_model.joblib")
    tfidf_path = os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib")

    joblib.dump(best_model, model_path)
    joblib.dump(tfidf, tfidf_path)
    print(f"모델 저장: {model_path}")
    print(f"벡터라이저 저장: {tfidf_path}")


if __name__ == "__main__":
    train()
