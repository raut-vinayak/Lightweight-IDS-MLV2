"""
Preprocessing Module for Lightweight IoT IDS.

Handles data cleaning, leakage removal, constant feature dropping,
label encoding for binary & multiclass tasks, stratified splitting,
and leakage-safe scaling (fit on train only).
"""

from typing import Tuple, List
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from src import config
from src.data_loader import load_merged_dataset


def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Clean dataset by:
    1. Removing identifier and data-leakage columns.
    2. Removing constant or zero-variance columns.
    3. Handling NaN and infinite numerical values.

    Args:
        df (pd.DataFrame): Raw dataframe including features and label.

    Returns:
        Tuple: (cleaned_df, dropped_leakage_cols, dropped_constant_cols)
    """
    initial_rows = len(df)
    df_clean = df.copy()

    # 1. Identify and drop leakage / identifier columns
    dropped_leakage = [col for col in config.LEAKAGE_COLUMNS if col in df_clean.columns]
    if dropped_leakage:
        df_clean = df_clean.drop(columns=dropped_leakage)

    # 2. Replace inf/-inf with NaN and drop corrupted rows
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    df_clean[numeric_cols] = df_clean[numeric_cols].replace([np.inf, -np.inf], np.nan)
    df_clean = df_clean.dropna(subset=numeric_cols)

    # 3. Identify and drop constant columns (variance == 0 or nunique <= 1)
    feature_cols = [c for c in df_clean.columns if c != config.LABEL_COLUMN]
    dropped_constant = [col for col in feature_cols if df_clean[col].nunique() <= 1]
    if dropped_constant:
        df_clean = df_clean.drop(columns=dropped_constant)

    final_rows = len(df_clean)
    return df_clean, dropped_leakage, dropped_constant


def prepare_features_and_labels(df: pd.DataFrame, task: str = "binary") -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extract cleaned feature matrix X and target label vector y.

    Args:
        df (pd.DataFrame): Input dataframe.
        task (str): Either 'binary' (0=Benign, 1=Attack)
                    or 'multiclass' (Benign, DDoS, DoS, Recon, Web-based, Brute Force, Spoofing, Mirai).

    Returns:
        Tuple[pd.DataFrame, pd.Series]: (X, y)
    """
    if task not in ["binary", "multiclass"]:
        raise ValueError(f"Task must be 'binary' or 'multiclass', got '{task}'")

    # Clean the dataframe first
    df_clean, _, _ = clean_data(df)

    if config.LABEL_COLUMN not in df_clean.columns:
        raise KeyError(f"Label column '{config.LABEL_COLUMN}' not found in data.")

    raw_labels = df_clean[config.LABEL_COLUMN].astype(str)

    if task == "binary":
        # Binary: 0 for BenignTraffic, 1 for any attack
        y = raw_labels.apply(lambda lbl: 0 if lbl == "BenignTraffic" else 1)
    else:
        # Multiclass: Map to 7 attack categories + Benign
        y = raw_labels.map(config.CATEGORY_MAP)
        # If any label was not in the mapping, keep original or map to Other
        y = y.fillna("Other")

    X = df_clean.drop(columns=[config.LABEL_COLUMN])
    return X, y


def leakage_safe_split(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = config.TEST_SIZE,
    random_state: int = config.RANDOM_STATE
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Perform a stratified train/test split to guarantee that class distributions
    in train and test sets remain strictly proportional without leakage.

    Args:
        X (pd.DataFrame): Features.
        y (pd.Series): Target labels.
        test_size (float): Fraction for test set.
        random_state (int): Seed for reproducibility.

    Returns:
        Tuple: (X_train, X_test, y_train, y_test)
    """
    return train_test_split(
        X, y,
        test_size=test_size,
        stratify=y,
        random_state=random_state
    )


def scale_features(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
    """
    Standardize features by fitting StandardScaler strictly on X_train,
    then transforming both X_train and X_test to prevent test-set data leakage.

    Args:
        X_train (pd.DataFrame): Training features.
        X_test (pd.DataFrame): Testing features.

    Returns:
        Tuple: (X_train_scaled, X_test_scaled, fitted_scaler)
    """
    scaler = StandardScaler()
    feature_names = list(X_train.columns)

    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=feature_names,
        index=X_train.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=feature_names,
        index=X_test.index
    )

    return X_train_scaled, X_test_scaled, scaler


def run_phase_2_validation():
    """
    Execute and print Phase 2 verification checks:
    - Data cleaning metrics (rows before/after, dropped leakage & constant columns)
    - Class distributions for binary and multiclass
    - Train/test stratified split proportion proof
    """
    print(f"\n{'='*70}")
    print("PHASE 2: PREPROCESSING & CATEGORY MAPPING VERIFICATION")
    print(f"{'='*70}")

    # Load dataset
    raw_df = load_merged_dataset(sample_fraction=config.DEV_SAMPLE_FRACTION)
    initial_rows = len(raw_df)

    # Clean data check
    df_clean, dropped_leakage, dropped_constant = clean_data(raw_df)
    print(f"Rows before cleaning: {initial_rows:,}")
    print(f"Rows after cleaning:  {len(df_clean):,}")
    print(f"Dropped Leakage-prone columns: {dropped_leakage if dropped_leakage else 'None found'}")
    print(f"Dropped Constant columns:      {dropped_constant if dropped_constant else 'None'}")

    # Validate Binary Task
    print(f"\n--- [1] Binary Task Validation ---")
    X_bin, y_bin = prepare_features_and_labels(raw_df, task="binary")
    print("Binary Class Distribution:")
    print(y_bin.value_counts(normalize=False))
    print("Binary Class Proportions:")
    print(y_bin.value_counts(normalize=True).round(4))

    X_tr_b, X_te_b, y_tr_b, y_te_b = leakage_safe_split(X_bin, y_bin)
    print("\nTrain vs Test Split Proportion Check (Binary):")
    split_proof_bin = pd.DataFrame({
        "Train Proportion": y_tr_b.value_counts(normalize=True).round(4),
        "Test Proportion":  y_te_b.value_counts(normalize=True).round(4)
    })
    print(split_proof_bin)

    # Validate Multiclass Task
    print(f"\n--- [2] Multiclass Task Validation ---")
    X_multi, y_multi = prepare_features_and_labels(raw_df, task="multiclass")
    print("Multiclass Distribution:")
    print(y_multi.value_counts(normalize=False))
    print("\nMulticlass Class Proportions:")
    print(y_multi.value_counts(normalize=True).round(4))

    X_tr_m, X_te_m, y_tr_m, y_te_m = leakage_safe_split(X_multi, y_multi)
    print("\nTrain vs Test Split Proportion Check (Multiclass):")
    split_proof_multi = pd.DataFrame({
        "Train Proportion": y_tr_m.value_counts(normalize=True).round(4),
        "Test Proportion":  y_te_m.value_counts(normalize=True).round(4)
    })
    print(split_proof_multi)
    print(f"{'='*70}\n")


if __name__ == "__main__":
    # Allows running as: python -m src.preprocess
    run_phase_2_validation()
