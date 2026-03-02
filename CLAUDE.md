# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Korean sentiment analysis using scikit-learn and NSMC (Naver Sentiment Movie Corpus). The model performs binary classification (positive/negative) during training, then uses prediction probability thresholds (0.4–0.6) to produce 3-class output (긍정/중립/부정) at inference time.

## Commands

```bash
# Setup
pip install -r requirements.txt

# Download NSMC dataset (ratings_train.txt, ratings_test.txt → data/)
python data/download_data.py

# Train models (compares MultinomialNB, LogisticRegression, LinearSVC; saves best to models/)
python src/train.py

# Predict sentiment for a text
python src/predict.py "이 영화 정말 재밌다"
```

All scripts must be run from the project root directory.

## Architecture

- **`src/preprocess.py`** — Core text pipeline: `konlpy.Okt` morpheme tokenizer with stemming, stopword filtering, and Korean-only regex cleaning. Exports `tokenize()` (used by both training and prediction) and `load_data()`/`preprocess_dataframe()` for NSMC TSV handling.
- **`src/train.py`** — Trains three classifiers on TF-IDF features (max 50k features, unigrams+bigrams), selects the best by test accuracy, saves model and vectorizer as `.joblib` files to `models/`.
- **`src/predict.py`** — Loads saved model; uses `predict_proba` for probability-based 3-class mapping, falls back to `decision_function` for models like LinearSVC that lack probability support.
- **`data/download_data.py`** — Downloads NSMC from `e9t/nsmc` GitHub repo.

## Key Design Decisions

- **3-class from 2-class**: NSMC only has 0/1 labels. Neutral class is derived at prediction time via probability thresholds (`NEUTRAL_LOW=0.4`, `NEUTRAL_HIGH=0.6` in `predict.py`), not from training data.
- **TF-IDF config**: `max_features=50000`, `ngram_range=(1, 2)` — the vectorizer is saved alongside the model and must be loaded together.
- **Module imports**: Scripts use `sys.path.insert` to add project root, then import from `src.preprocess`.
