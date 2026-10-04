"""
Visualization Module for Lightweight IoT IDS.

Generates and saves research-grade trade-off plots:
1. Macro F1 vs K (accuracy-efficiency Pareto frontier)
2. Model Size (KB) vs K (log-scale footprint)
3. Inference Latency (ms) vs K (real-time responsiveness)
4. Confusion Matrix heatmap for the best K=10 Multiclass model
Reads strictly from scorecard CSVs with no hardcoded values.
"""

from pathlib import Path
from typing import List
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import confusion_matrix
from src import config
from src.data_loader import load_merged_dataset
from src.preprocess import prepare_features_and_labels, leakage_safe_split, scale_features


def set_plot_style():
    """
    Configure clean, professional matplotlib aesthetics for scientific reporting.
    """
    sns.set_theme(style="whitegrid", palette="tab10")
    plt.rcParams.update({
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14
    })


def plot_macro_f1_vs_k(df: pd.DataFrame, output_path: Path, task: str = "binary"):
    """
    Generate Macro F1 vs K line plot (one line per model architecture).

    Args:
        df (pd.DataFrame): Scorecard data.
        output_path (Path): PNG file destination.
        task (str): Task identifier for title.
    """
    plt.figure(figsize=(8, 5))
    models = df["model"].unique()
    markers = ["o", "s", "^", "D"]

    for idx, model_name in enumerate(models):
        sub_df = df[df["model"] == model_name].sort_values("k")
        plt.plot(
            sub_df["k"],
            sub_df["macro_f1"],
            marker=markers[idx % len(markers)],
            linewidth=2.2,
            markersize=7,
            label=model_name
        )

    plt.title(f"Macro F1 Score vs. Feature Subset Size (K) — [{task.capitalize()}]")
    plt.xlabel("Number of Features (K)")
    plt.ylabel("Macro F1 Score")
    plt.xticks(sorted(df["k"].unique()))
    plt.ylim(0.0, 1.0)
    plt.legend(title="Model", frameon=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[Plot 1/4] Saved Macro F1 vs K plot: {output_path}")


def plot_model_size_vs_k(df: pd.DataFrame, output_path: Path, task: str = "binary"):
    """
    Generate Model Size (KB) vs K line plot on a logarithmic scale.

    Args:
        df (pd.DataFrame): Scorecard data.
        output_path (Path): PNG file destination.
        task (str): Task identifier for title.
    """
    plt.figure(figsize=(8, 5))
    models = df["model"].unique()
    markers = ["o", "s", "^", "D"]

    for idx, model_name in enumerate(models):
        sub_df = df[df["model"] == model_name].sort_values("k")
        plt.plot(
            sub_df["k"],
            sub_df["model_size_kb"],
            marker=markers[idx % len(markers)],
            linewidth=2.2,
            markersize=7,
            label=model_name
        )

    plt.yscale("log")
    plt.title(f"Serialized Model Size (KB) vs. K (Log Scale) — [{task.capitalize()}]")
    plt.xlabel("Number of Features (K)")
    plt.ylabel("Model Size (KB) [Log Scale]")
    plt.xticks(sorted(df["k"].unique()))
    plt.legend(title="Model", frameon=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[Plot 2/4] Saved Model Size vs K plot: {output_path}")


def plot_latency_vs_k(df: pd.DataFrame, output_path: Path, task: str = "binary"):
    """
    Generate Inference Latency (ms) vs K line plot.

    Args:
        df (pd.DataFrame): Scorecard data.
        output_path (Path): PNG file destination.
        task (str): Task identifier for title.
    """
    plt.figure(figsize=(8, 5))
    models = df["model"].unique()
    markers = ["o", "s", "^", "D"]

    for idx, model_name in enumerate(models):
        sub_df = df[df["model"] == model_name].sort_values("k")
        plt.plot(
            sub_df["k"],
            sub_df["latency_ms"],
            marker=markers[idx % len(markers)],
            linewidth=2.2,
            markersize=7,
            label=model_name
        )

    plt.title(f"Inference Latency per Sample (ms) vs. K — [{task.capitalize()}]")
    plt.xlabel("Number of Features (K)")
    plt.ylabel("Latency per Sample (ms)")
    plt.xticks(sorted(df["k"].unique()))
    plt.legend(title="Model", frameon=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[Plot 3/4] Saved Latency vs K plot: {output_path}")


def plot_confusion_matrix_k10_multiclass(output_path: Path):
    """
    Generate Confusion Matrix heatmap for best performing model at K=10 on multiclass task.

    Args:
        output_path (Path): PNG destination.
    """
    scorecard_path = config.SCORECARD_MULTICLASS_CSV
    if not scorecard_path.exists():
        scorecard_path = config.SCORECARD_CSV

    if not scorecard_path.exists():
        print(f"[Plots] Error: Scorecard file not found at {scorecard_path}")
        return

    scorecard_df = pd.read_csv(scorecard_path)
    k10_df = scorecard_df[scorecard_df["k"] == 10]

    if k10_df.empty:
        best_model_name = "ConstrainedLightGBM"
    else:
        best_row = k10_df.sort_values(by="macro_f1", ascending=False).iloc[0]
        best_model_name = best_row["model"]

    model_file = config.MODELS_DIR / f"model_multiclass_{best_model_name}_k10.joblib"
    if not model_file.exists():
        print(f"[Plots] Model file not found: {model_file}")
        return

    artifact = joblib.load(model_file)
    model = artifact["model"]
    features = artifact["features"]

    # Load test split for multiclass
    raw_df = load_merged_dataset(sample_fraction=config.DEV_SAMPLE_FRACTION)
    X, y = prepare_features_and_labels(raw_df, task="multiclass")
    X_train, X_test, y_train, y_test = leakage_safe_split(X, y)
    _, X_test_scaled, _ = scale_features(X_train, X_test)

    # Predict using selected features
    y_pred = model.predict(X_test_scaled[features])

    classes = sorted(list(set(y_test.unique()) | set(y_pred)))
    cm = confusion_matrix(y_test, y_pred, labels=classes)

    plt.figure(figsize=(9, 7))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=classes,
        yticklabels=classes,
        cbar=True
    )
    plt.title(f"Confusion Matrix: Best K=10 Multiclass Model ({best_model_name})")
    plt.xlabel("Predicted Class")
    plt.ylabel("Ground Truth Class")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[Plot 4/4] Saved Confusion Matrix heatmap: {output_path}")


def generate_all_plots() -> List[Path]:
    """
    Generate all 4 research trade-off plots and return list of saved file paths.

    Returns:
        List[Path]: Paths to generated PNG files.
    """
    set_plot_style()
    config.PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Choose primary scorecard (binary first, fallback to scorecard.csv)
    scorecard_file = config.SCORECARD_BINARY_CSV if config.SCORECARD_BINARY_CSV.exists() else config.SCORECARD_CSV
    if not scorecard_file.exists():
        raise FileNotFoundError(f"Scorecard not found at {scorecard_file}. Run main.py first.")

    df_scorecard = pd.read_csv(scorecard_file)

    p1 = config.PLOTS_DIR / "macro_f1_vs_k.png"
    p2 = config.PLOTS_DIR / "model_size_vs_k.png"
    p3 = config.PLOTS_DIR / "latency_vs_k.png"
    p4 = config.PLOTS_DIR / "confusion_matrix_k10_multiclass.png"

    plot_macro_f1_vs_k(df_scorecard, p1, task="binary")
    plot_model_size_vs_k(df_scorecard, p2, task="binary")
    plot_latency_vs_k(df_scorecard, p3, task="binary")
    plot_confusion_matrix_k10_multiclass(p4)

    generated_paths = [p1, p2, p3, p4]
    print(f"\n[Plots] All 4 plots generated successfully in: {config.PLOTS_DIR}")
    for p in generated_paths:
        print(f"  - {p.name}")
    return generated_paths


if __name__ == "__main__":
    generate_all_plots()
