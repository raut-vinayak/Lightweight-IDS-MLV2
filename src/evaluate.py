"""
Evaluation & Benchmarking Module for Lightweight IoT IDS.

Calculates multi-dimensional trade-off metrics essential for edge IoT deployment:
1. Macro F1, Weighted F1, Accuracy, Precision, Recall
2. Model size footprint (KB) on disk
3. Single-sample inference latency (ms)
4. Saves benchmark scorecards and serializes models.
"""

import time
import os
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
from src import config


def benchmark_inference_latency(model: Any, X_sample: pd.DataFrame, num_runs: int = 50) -> float:
    """
    Measure single-sample inference latency in milliseconds (ms).
    Averages over multiple runs to simulate real-time packet arrival on edge devices.

    Args:
        model: Trained model instance.
        X_sample (pd.DataFrame): Test samples.
        num_runs (int): Number of inference iterations.

    Returns:
        float: Average latency per sample in milliseconds.
    """
    # Use first 50 rows or whatever is available
    test_rows = X_sample.iloc[:min(len(X_sample), 50)]
    latencies = []

    for _ in range(num_runs):
        start_time = time.perf_counter()
        _ = model.predict(test_rows)
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000.0
        latencies.append(total_time_ms / len(test_rows))

    avg_latency = float(np.mean(latencies))
    return round(avg_latency, 4)


def measure_model_size_kb(model_path: Path) -> float:
    """
    Compute disk footprint of the serialized model in Kilobytes (KB).

    Args:
        model_path (Path): Path to saved joblib file.

    Returns:
        float: File size in KB.
    """
    if not model_path.exists():
        return 0.0
    size_bytes = os.path.getsize(model_path)
    return round(size_bytes / 1024.0, 2)


def evaluate_and_benchmark_model(
    model: Any,
    model_name: str,
    task: str,
    k: int,
    features: List[str],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    scaler: Any = None
) -> Dict[str, Any]:
    """
    Train model, evaluate classification performance on test set,
    benchmark latency, save model artifact, and return scorecard record.

    Args:
        model: Model instance.
        model_name (str): Architecture name.
        task (str): 'binary' or 'multiclass'.
        k (int): Feature subset size.
        features (List[str]): Exact feature names used.
        X_train (pd.DataFrame): Training features (k subset).
        y_train (pd.Series): Training labels.
        X_test (pd.DataFrame): Test features (k subset).
        y_test (pd.Series): Test labels.
        scaler: Optional fitted StandardScaler.

    Returns:
        Dict[str, Any]: Dictionary representing row for scorecard table.
    """
    # 1. Fit model
    start_train = time.perf_counter()
    model.fit(X_train, y_train)
    train_duration = time.perf_counter() - start_train

    # 2. Predict on test set
    y_pred = model.predict(X_test)

    # 3. Compute evaluation metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    # 4. Check for data leakage red flag
    if macro_f1 > 0.999:
        print(f"\n[WARNING / RED FLAG] Model {model_name} at K={k} achieved Macro F1 = {macro_f1:.4f} > 0.999!")
        print("  This strongly indicates potential label or identifier data leakage. Investigate features.\n")

    # 5. Measure latency
    latency_ms = benchmark_inference_latency(model, X_test)

    # 6. Save model artifact with metadata
    model_filename = f"model_{task}_{model_name}_k{k}.joblib"
    model_path = config.MODELS_DIR / model_filename
    artifact = {
        "model": model,
        "model_name": model_name,
        "task": task,
        "k": k,
        "features": features,
        "scaler": scaler
    }
    joblib.dump(artifact, model_path)
    size_kb = measure_model_size_kb(model_path)

    # 7. Build result entry
    record = {
        "task": task,
        "k": k,
        "model": model_name,
        "accuracy": round(float(acc), 4),
        "precision_macro": round(float(prec), 4),
        "recall_macro": round(float(rec), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "model_size_kb": size_kb,
        "latency_ms": latency_ms,
        "train_time_sec": round(train_duration, 3)
    }

    return record


def save_scorecard(records: List[Dict[str, Any]], task: str) -> pd.DataFrame:
    """
    Save list of benchmark evaluation records to scorecard CSV files.

    Args:
        records (List[Dict[str, Any]]): Collected benchmark results.
        task (str): 'binary' or 'multiclass'.

    Returns:
        pd.DataFrame: Formatted scorecard DataFrame.
    """
    df_scorecard = pd.DataFrame(records)

    # Sort descending by macro_f1 within each K
    df_scorecard = df_scorecard.sort_values(by=["k", "macro_f1"], ascending=[True, False])

    # Save task-specific scorecard
    if task == "binary":
        out_file = config.SCORECARD_BINARY_CSV
    else:
        out_file = config.SCORECARD_MULTICLASS_CSV

    df_scorecard.to_csv(out_file, index=False)
    # Also save to master scorecard.csv
    df_scorecard.to_csv(config.SCORECARD_CSV, index=False)

    print(f"\n[Scorecard] Saved {task} results to: {out_file}")
    return df_scorecard
