"""
C-Code Exporter for Lightweight IoT IDS.

Translates the trained scikit-learn DecisionTree (K=10) into pure,
standalone, zero-dependency C code (ids_rules.c and ids_rules.h).
Enables direct deployment to bare-metal IoT microcontrollers (ESP32,
STM32, Arduino, Raspberry Pi Pico) and low-power embedded routers.
"""

from pathlib import Path
import joblib
from sklearn.tree import _tree
from src import config


def export_decision_tree_to_c(model_path: Path, output_c_path: Path, output_h_path: Path):
    """Convert a serialized DecisionTree model into a standalone C function."""
    if not model_path.exists():
        print(f"[Exporter] Model not found: {model_path}")
        return

    artifact = joblib.load(model_path)
    model = artifact["model"]
    features = artifact["features"]

    tree_ = model.tree_
    feature_names = features

    header_content = f"""/*
 * Lightweight IoT Intrusion Detection System (IDS)
 * Hardware Deployment Header (Auto-Generated)
 * 
 * Model: Decision Tree (K={len(features)})
 * Memory Footprint: ~4 KB
 * Dependencies: None (Bare-Metal C99)
 */

#ifndef IDS_RULES_H
#define IDS_RULES_H

#ifdef __cplusplus
extern "C" {{
#endif

/*
 * Feature Input Mapping (Array of {len(features)} floats):
"""
    for i, name in enumerate(feature_names):
        header_content += f" *   features[{i}] : {name}\n"

    header_content += """ *
 * Returns:
 *   0 = Benign (Normal Safe Traffic)
 *   1 = Attack (Malicious Threat Detected)
 */
int predict_ids(const float* features);

#ifdef __cplusplus
}
#endif

#endif /* IDS_RULES_H */
"""

    c_content = f"""/*
 * Lightweight IoT Intrusion Detection System (IDS)
 * Embedded C Implementation
 * 
 * Target: Low-power IoT Gateway & Edge Microcontrollers
 */

#include "ids_rules.h"

int predict_ids(const float* features) {{
"""

    def recurse(node: int, depth: int) -> str:
        indent = "    " * (depth + 1)
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            feat_idx = tree_.feature[node]
            feat_name = feature_names[feat_idx]
            threshold = tree_.threshold[node]

            code = f"{indent}/* Condition: {feat_name} <= {threshold:.5f} */\n"
            code += f"{indent}if (features[{feat_idx}] <= {threshold:.5f}f) {{\n"
            code += recurse(tree_.children_left[node], depth + 1)
            code += f"{indent}}} else {{\n"
            code += recurse(tree_.children_right[node], depth + 1)
            code += f"{indent}}}\n"
            return code
        else:
            # Leaf node
            val = tree_.value[node][0]
            pred_class = int(val.argmax())
            class_label = "Attack (1)" if pred_class == 1 else "Benign (0)"
            return f"{indent}return {pred_class}; /* {class_label} */\n"

    c_content += recurse(0, 0)
    c_content += "}\n"

    output_c_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_c_path, "w", encoding="utf-8") as f:
        f.write(c_content)

    with open(output_h_path, "w", encoding="utf-8") as f:
        f.write(header_content)

    print(f"[Exporter] Successfully generated C source: {output_c_path} ({len(c_content)} bytes)")
    print(f"[Exporter] Successfully generated C header: {output_h_path} ({len(header_content)} bytes)")


if __name__ == "__main__":
    model_file = config.MODELS_DIR / "model_binary_DecisionTree_k10.joblib"
    c_file = config.MODELS_DIR / "ids_rules.c"
    h_file = config.MODELS_DIR / "ids_rules.h"
    export_decision_tree_to_c(model_file, c_file, h_file)
