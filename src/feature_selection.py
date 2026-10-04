"""
Feature Selection Module for Lightweight IoT IDS.

Implements two-stage feature selection:
1. Mutual Information ranking to score non-linear dependency with target label.
2. Correlation-based pruning to remove redundant, highly correlated features.
Generates strict nested subsets for K in [5, 10, 15, 20].
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from src import config
from src.data_loader import load_merged_dataset
from src.preprocess import prepare_features_and_labels, leakage_safe_split, scale_features


def compute_mutual_information(X: pd.DataFrame, y: pd.Series) -> pd.Series:
    """
    Compute Mutual Information (MI) classification score for every feature against target y.

    Args:
        X (pd.DataFrame): Training feature matrix.
        y (pd.Series): Target labels.

    Returns:
        pd.Series: Features sorted by MI score in descending order.
    """
    # Mutual information captures both linear and non-linear relationships
    mi_scores = mutual_info_classif(
        X, y,
        discrete_features="auto",
        random_state=config.RANDOM_STATE
    )
    mi_series = pd.Series(mi_scores, index=X.columns).sort_values(ascending=False)
    return mi_series


def prune_correlated_features(
    ranked_features: List[str],
    X: pd.DataFrame,
    threshold: float = config.CORRELATION_THRESHOLD
) -> Tuple[List[str], List[Tuple[str, str, float]]]:
    """
    Prune redundant features using greedy correlation elimination:
    Iterate through features by MI rank. If a candidate feature has an absolute
    correlation greater than threshold with any already-selected feature, prune it.

    Args:
        ranked_features (List[str]): Feature names ordered by MI descending.
        X (pd.DataFrame): Training feature data used to calculate Pearson correlation.
        threshold (float): Absolute correlation threshold above which redundancy is pruned.

    Returns:
        Tuple: (pruned_ranking_list, list_of_pruned_details)
    """
    corr_matrix = X[ranked_features].corr().abs()
    selected_features = []
    pruned_details = []

    for feat in ranked_features:
        is_redundant = False
        for selected in selected_features:
            corr_val = corr_matrix.loc[feat, selected]
            if corr_val >= threshold:
                is_redundant = True
                pruned_details.append((feat, selected, round(float(corr_val), 4)))
                break

        if not is_redundant:
            selected_features.append(feat)

    return selected_features, pruned_details


def get_feature_subsets(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    k_values: List[int] = config.K_VALUES,
    threshold: float = config.CORRELATION_THRESHOLD
) -> Tuple[Dict[int, List[str]], pd.Series, List[str]]:
    """
    Produce nested feature subsets of sizes K in k_values based on MI rank and correlation pruning.

    Args:
        X_train (pd.DataFrame): Scaled/cleaned training features.
        y_train (pd.Series): Training labels.
        k_values (List[int]): Subsets sizes, e.g. [5, 10, 15, 20].
        threshold (float): Correlation threshold.

    Returns:
        Tuple:
            - feature_subsets: Dict[int, List[str]] mapping K to feature list.
            - mi_ranking: pd.Series full MI ranking.
            - pruned_ranking: List[str] pruned ranking.
    """
    # 1. Compute full MI ranking
    mi_ranking = compute_mutual_information(X_train, y_train)
    ranked_features = list(mi_ranking.index)

    # 2. Prune correlated redundancies
    pruned_ranking, _ = prune_correlated_features(ranked_features, X_train, threshold=threshold)

    # 3. Create nested subsets: top K from the pruned ranking
    feature_subsets = {}
    for k in sorted(k_values):
        if k > len(pruned_ranking):
            raise ValueError(f"Requested K={k} exceeds available pruned features ({len(pruned_ranking)})")
        feature_subsets[k] = pruned_ranking[:k]

    return feature_subsets, mi_ranking, pruned_ranking


def run_phase_3_validation():
    """
    Execute Phase 3 validation:
    - Print full MI ranking
    - Print correlation-pruned ranking
    - Print feature list for K = 5, 10, 15, 20
    - Verify strict nested subset property
    - Check for identifier or suspicious columns
    """
    print(f"\n{'='*70}")
    print("PHASE 3: FEATURE SELECTION SANITY CHECK")
    print(f"{'='*70}")

    # Load and preprocess binary data
    df = load_merged_dataset(sample_fraction=config.DEV_SAMPLE_FRACTION)
    X, y = prepare_features_and_labels(df, task="binary")
    X_tr, X_te, y_tr, y_te = leakage_safe_split(X, y)
    X_tr_scaled, _, _ = scale_features(X_tr, X_te)

    # Run feature selection
    feature_subsets, mi_ranking, pruned_ranking = get_feature_subsets(
        X_tr_scaled, y_tr, k_values=config.K_VALUES
    )

    print("\n--- [1] Top 15 Mutual Information Features (Full Ranking) ---")
    for rank, (feat, score) in enumerate(mi_ranking.head(15).items(), 1):
        print(f"  {rank:2d}. {feat:<25} (MI Score: {score:.4f})")

    print(f"\nTotal Features initially: {len(mi_ranking)}")
    print(f"Features remaining after correlation pruning (threshold={config.CORRELATION_THRESHOLD}): {len(pruned_ranking)}")

    print("\n--- [2] Selected Feature Subsets per K ---")
    for k in config.K_VALUES:
        feats = feature_subsets[k]
        print(f"\nK = {k} Features ({len(feats)}):")
        print("  " + ", ".join(feats))

    # Strict subset check
    print("\n--- [3] Strict Nested Subset Verification ---")
    sorted_k = sorted(config.K_VALUES)
    all_passed = True
    for i in range(len(sorted_k) - 1):
        k_small = sorted_k[i]
        k_large = sorted_k[i + 1]
        set_small = set(feature_subsets[k_small])
        set_large = set(feature_subsets[k_large])

        is_strict_subset = set_small.issubset(set_large) and (len(set_small) < len(set_large))
        print(f"  Is K={k_small} a strict subset of K={k_large}? -> {'PASS' if is_strict_subset else 'FAIL'}")
        if not is_strict_subset:
            all_passed = False

    if all_passed:
        print("  [SUCCESS] All smaller-K sets are STRICT SUBSETS of larger-K sets.")
    else:
        print("  [ERROR] Nested subset property violated!")

    # Suspicious identifier check
    print("\n--- [4] Suspicious Identifier / Leakage Column Check ---")
    suspicious_found = []
    for k, feats in feature_subsets.items():
        for f in feats:
            if f.lower() in [col.lower() for col in config.LEAKAGE_COLUMNS] or "ip" in f.lower() or "id" in f.lower() or "port" in f.lower():
                suspicious_found.append((k, f))

    if not suspicious_found:
        print("  [CLEAN] No identifier, IP, or leakage-prone features detected in selected subsets.")
    else:
        print(f"  [FLAG] Potential suspicious features found: {suspicious_found}")

    print(f"{'='*70}\n")
    return feature_subsets


if __name__ == "__main__":
    # Allows running as: python -m src.feature_selection
    run_phase_3_validation()
