"""
Main Pipeline Runner for Lightweight IoT IDS.

Executes the full end-to-end workflow:
1. Data loading (with customizable sample fraction)
2. Preprocessing & leakage-safe train/test split
3. Feature selection (Mutual Information + correlation pruning for K=5, 10, 15, 20)
4. Model training across 4 resource-constrained algorithms
5. Evaluation & multi-dimensional trade-off benchmarking (Macro F1, Size, Latency)
6. Exporting and displaying scorecard tables
"""

import argparse
import sys
from typing import Dict, Any, List
import pandas as pd
from src import config
from src.data_loader import load_merged_dataset
from src.preprocess import prepare_features_and_labels, leakage_safe_split, scale_features
from src.feature_selection import get_feature_subsets
from src.models import get_model_registry
from src.evaluate import evaluate_and_benchmark_model, save_scorecard


def run_pipeline(task: str = "binary", sample_fraction: float = config.DEV_SAMPLE_FRACTION) -> pd.DataFrame:
    """
    Run full training and evaluation pipeline for specified task.

    Args:
        task (str): 'binary' or 'multiclass'.
        sample_fraction (float): Subsample ratio for dataset loading.

    Returns:
        pd.DataFrame: Completed scorecard table.
    """
    print(f"\n{'='*75}")
    print(f"STARTING LIGHTWEIGHT IOT IDS PIPELINE: TASK = '{task.upper()}'")
    print(f"{'='*75}")

    # 1. Load Data
    raw_df = load_merged_dataset(sample_fraction=sample_fraction)
    print(f"[Pipeline] Loaded {len(raw_df):,} rows with sample_fraction = {sample_fraction}")

    # 2. Preprocess and Split
    X, y = prepare_features_and_labels(raw_df, task=task)
    X_train, X_test, y_train, y_test = leakage_safe_split(X, y)
    print(f"[Pipeline] Split sizes: Train = {len(X_train):,} samples, Test = {len(X_test):,} samples")

    # 3. Scale Features (fit on train only)
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)

    # 4. Feature Selection on Train set
    print("[Pipeline] Running feature selection (Mutual Information + Correlation Pruning)...")
    feature_subsets, _, _ = get_feature_subsets(X_train_scaled, y_train, k_values=config.K_VALUES)

    # 5. Model Training & Evaluation Loop
    records: List[Dict[str, Any]] = []
    print(f"\n[Pipeline] Training 4 models across K = {config.K_VALUES}...")

    for k in config.K_VALUES:
        selected_feats = feature_subsets[k]
        print(f"\n--- Benchmarking K = {k} (Features: {', '.join(selected_feats)}) ---")

        # Natural physical features for edge interpretability & deployment
        X_tr_k = X_train[selected_feats]
        X_te_k = X_test[selected_feats]

        # Fresh model registry for this K
        models = get_model_registry(task=task)

        for model_name, model_instance in models.items():
            # For LogisticRegression only, scale with a K-specific scaler
            if model_name == "LogisticRegression":
                from sklearn.preprocessing import StandardScaler
                k_scaler = StandardScaler()
                X_tr_fit = pd.DataFrame(k_scaler.fit_transform(X_tr_k), columns=selected_feats, index=X_tr_k.index)
                X_te_fit = pd.DataFrame(k_scaler.transform(X_te_k), columns=selected_feats, index=X_te_k.index)
                model_scaler = k_scaler
            else:
                X_tr_fit = X_tr_k
                X_te_fit = X_te_k
                model_scaler = None

            record = evaluate_and_benchmark_model(
                model=model_instance,
                model_name=model_name,
                task=task,
                k=k,
                features=selected_feats,
                X_train=X_tr_fit,
                y_train=y_train,
                X_test=X_te_fit,
                y_test=y_test,
                scaler=model_scaler
            )
            records.append(record)
            print(f"  [{model_name:<20}] Macro-F1: {record['macro_f1']:.4f} | Size: {record['model_size_kb']:>6.1f} KB | Latency: {record['latency_ms']:.4f} ms")

    # 6. Save & Display Scorecard
    scorecard_df = save_scorecard(records, task=task)

    print(f"\n{'='*75}")
    print(f"FULL SCORECARD (Sorted by Macro-F1 within each K): TASK = '{task.upper()}'")
    print(f"{'='*75}")
    display_cols = ["k", "model", "macro_f1", "accuracy", "model_size_kb", "latency_ms", "train_time_sec"]
    print(scorecard_df[display_cols].to_string(index=False))
    print(f"{'='*75}\n")

    return scorecard_df


def main():
    """
    Command line interface entrypoint for running the pipeline.
    """
    parser = argparse.ArgumentParser(description="Lightweight IoT IDS Pipeline Runner")
    parser.add_argument(
        "--task",
        type=str,
        choices=["binary", "multiclass", "both"],
        default="binary",
        help="Classification task to run ('binary', 'multiclass', or 'both')"
    )
    parser.add_argument(
        "--sample_frac",
        type=float,
        default=0.10,
        help="Fraction of dataset to use for training/testing (default: 0.10)"
    )

    args = parser.parse_args()

    if args.task in ["binary", "both"]:
        run_pipeline(task="binary", sample_fraction=args.sample_frac)

    if args.task in ["multiclass", "both"]:
        run_pipeline(task="multiclass", sample_fraction=args.sample_frac)


if __name__ == "__main__":
    main()
