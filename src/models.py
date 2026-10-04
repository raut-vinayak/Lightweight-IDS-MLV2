"""
Models Module for Lightweight IoT IDS.

Defines 4 resource-constrained machine learning architectures suited for IoT devices:
1. ConstrainedLightGBM (shallow gradient-boosted trees)
2. DecisionTree (ultra-lightweight rule engine)
3. LogisticRegression (fast linear boundary)
4. SmallRandomForest (compact ensemble)
"""

from typing import Dict, Any
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from lightgbm import LGBMClassifier
from src import config


def get_model_registry(task: str = "binary") -> Dict[str, Any]:
    """
    Return dictionary of initialized model instances with constrained hyperparameters
    tailored for memory and computation on embedded IoT / edge devices.

    Args:
        task (str): 'binary' or 'multiclass'.

    Returns:
        Dict[str, Any]: Dictionary mapping model name to instantiated model.
    """
    # Objective parameter depending on task
    lgbm_objective = "binary" if task == "binary" else "multiclass"

    models = {
        "ConstrainedLightGBM": LGBMClassifier(
            objective=lgbm_objective,
            max_depth=5,
            num_leaves=15,
            n_estimators=40,
            learning_rate=0.08,
            random_state=config.RANDOM_STATE,
            verbose=-1
        ),
        "DecisionTree": DecisionTreeClassifier(
            max_depth=6,
            criterion="gini",
            random_state=config.RANDOM_STATE
        ),
        "LogisticRegression": LogisticRegression(
            max_iter=500,
            solver="lbfgs",
            random_state=config.RANDOM_STATE
        ),
        "SmallRandomForest": RandomForestClassifier(
            n_estimators=15,
            max_depth=7,
            random_state=config.RANDOM_STATE,
            n_jobs=-1
        )
    }

    return models
