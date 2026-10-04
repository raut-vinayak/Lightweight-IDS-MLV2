# AI coding agent prompts — Lightweight IoT IDS

Use these prompts **one at a time, in order**, in your AI coding agent (Claude
Code, Cursor, etc.). Paste each phase's prompt as-is, let the agent finish
and verify it, then move to the next phase. Don't skip ahead — each phase
assumes the previous one's output exists and works.

Before Phase 1: unzip `lightweight_iot_ids.zip` into your working repo and
`cd` into it so the agent can see the existing scaffold (config.py,
data_loader.py, preprocess.py, feature_selection.py, models.py, evaluate.py,
main.py) before you give it any prompt.

---

## Phase 1 — Environment setup + data sanity check

```
I have an existing Python project scaffold for a Lightweight IoT IDS at the
current directory. It has: src/config.py, src/data_loader.py,
src/preprocess.py, src/feature_selection.py, src/models.py, src/evaluate.py,
main.py, requirements.txt, README.md.

Do the following:
1. Set up a Python virtual environment and install requirements.txt
   (use --break-system-packages if pip needs it in this environment).
2. I have downloaded some CICIoT2023 CSV files into data/raw/. Run
   `python -m src.data_loader` to inspect the label column and print the
   unique label values found.
3. Report back: how many CSV files are in data/raw/, how many rows/columns
   in one sample file, the exact column names, and the unique label values
   printed. Do not modify any code yet — this phase is verification only.
4. If any script errors out, fix only what's needed to make step 2 run
   successfully, and explain what you changed and why.
```

**Check before moving on:** you should see a clean list of unique attack
labels (e.g. DDoS-ICMP_Flood, DoS-SYN_Flood, BenignTraffic, etc.) with no
errors.

---

## Phase 2 — Fill in the multiclass category map + validate preprocessing

```
Using the unique label values printed in Phase 1, fill in
config.CATEGORY_MAP in src/config.py to group the raw CICIoT2023 labels into
these 7 categories: DDoS, DoS, Recon, Web-based, Brute Force, Spoofing,
Mirai — plus Benign as its own class. Use the CICIoT2023 paper's official
attack-to-category grouping (33 attacks -> 7 categories) as the source of
truth; look up the exact grouping if you're unsure rather than guessing.

Then:
1. Run src/data_loader.load_merged_dataset() with a small
   DEV_SAMPLE_FRACTION (e.g. 0.01) on the files in data/raw/, and pass the
   result through src/preprocess.prepare_features_and_labels() for BOTH
   task="binary" and task="multiclass".
2. Print: row count before/after cleaning, which columns got dropped as
   leakage-prone, which columns got dropped as constant, and the class
   distribution (value_counts) of the resulting y for both tasks.
3. Confirm the leakage-safe split (preprocess.leakage_safe_split) preserves
   class proportions between train and test — print the proportions for
   both to prove it.
4. Do NOT change any modeling code in this phase. Only preprocess.py and
   config.py should change, and only if something is broken.
```

**Check before moving on:** class distributions should look reasonable (no
category with 0 samples), and train/test proportions should closely match.

---

## Phase 3 — Feature selection sanity check

```
Run src/feature_selection.get_feature_subsets() on the cleaned, scaled,
binary-task training data from Phase 2 (use src/preprocess.scale_features()
first, fit only on train).

1. Print the full mutual-information ranking (all features, sorted
   descending) and the pruned ranking after correlation-based redundancy
   removal.
2. Print the exact feature list chosen for K=5, K=10, K=15, K=20.
3. Sanity check: confirm each smaller-K feature set is a strict subset of
   each larger-K feature set (this should be true given how
   get_feature_subsets is implemented — if it isn't, find and fix the bug).
4. Flag anything suspicious: e.g. if a feature that looks like it could
   still be an identifier or near-constant made it into the top ranks,
   point it out to me before proceeding rather than silently keeping it.
```

**Check before moving on:** you should have 4 clean, nested feature lists
and no leftover identifier-like columns in them.

---

## Phase 4 — Full training run + scorecard

```
Run the full pipeline: python main.py, using task="binary" first, with
DEV_SAMPLE_FRACTION set high enough to get a meaningful sample size (start
around 0.05-0.1 depending on how much data is in data/raw/, and tell me the
resulting row count).

1. Let it train ConstrainedLightGBM, DecisionTree, LogisticRegression, and
   SmallRandomForest across K=5,10,15,20, and confirm results/scorecard.csv
   and the saved models in models/ are produced without errors.
2. Print the full scorecard as a table, sorted by macro_f1 descending
   within each K.
3. Tell me: which model wins at each K, and how model size (KB) and latency
   (ms) trade off against macro_f1 as K decreases from 20 to 5. Summarize
   this in 3-4 sentences, don't just dump the table again.
4. If any model errors or produces suspiciously perfect scores (e.g.
   macro_f1 > 0.999), stop and flag it to me — that usually means a leakage
   bug, not a genuinely great model.
5. Repeat the same run with task="multiclass" (using the CATEGORY_MAP from
   Phase 2) and report the same summary for the 7-category task.
```

**Check before moving on:** you have two scorecards (binary + multiclass),
no leakage red flags, and a clear sense of which model/K to feature as your
"primary" result.

---

## Phase 5 — Results visualization

```
Using results/scorecard.csv (both the binary and multiclass runs from Phase
4, saved separately e.g. scorecard_binary.csv and scorecard_multiclass.csv),
write a new script src/plots.py that generates and saves these charts to
results/plots/:

1. macro_f1 vs K, one line per model (the accuracy-efficiency Pareto curve
   central to this project).
2. model_size_kb vs K, one line per model, log scale on the y-axis.
3. latency_ms vs K, one line per model.
4. A confusion matrix heatmap for the best-performing model at K=10 on the
   multiclass task.

Use matplotlib/seaborn, label all axes clearly, and save each as a PNG. Show
me the file paths when done. Don't use any hardcoded numbers — read
everything from the actual scorecard CSVs.
```

**Check before moving on:** 4 PNGs in results/plots/, matching what's
actually in your scorecard CSVs.

---

## Phase 6 — Streamlit dashboard

```
Build a Streamlit dashboard at dashboard.py in the project root with these
features:

1. A sidebar to pick: task (binary/multiclass), K (5/10/15/20), and which
   model to view (from the ones saved in models/).
2. A main panel showing that model's scorecard row (macro_f1, size_kb,
   latency_ms) as metric cards, plus the K-vs-metric charts from Phase 5
   embedded inline.
3. A "Try a prediction" section: let me upload a CSV (or paste a single row
   of feature values) and see the model's prediction (benign/attack, or the
   attack category for multiclass) along with the prediction latency for
   that one row.
4. Handle the case where a model file for the selected (task, K) combo
   doesn't exist yet — show a clear message instead of crashing.

Run it with `streamlit run dashboard.py` and confirm it loads without
errors. Walk me through what each section does once it's working.
```

**Check before moving on:** dashboard opens in browser, all sections work,
uploading a sample row gives a real prediction.

---

## Phase 7 — Live capture + real-time inference (VM lab)

```
I have a 3-VM lab set up (Attacker, Victim, IDS) on an isolated internal
network, with the IDS VM's network adapter in promiscuous mode. Build a
script src/live_capture.py that runs on the IDS VM and does the following:

1. Sniff live traffic on a given network interface (parameterize the
   interface name via a CLI argument) using Scapy or pyshark — pick
   whichever is more reliable for this, and explain your choice.
2. Aggregate packets into flows using a sliding time window (parameterize
   the window size, default 2 seconds), grouped by the 5-tuple (src ip,
   dst ip, src port, dst port, protocol).
3. Compute the same features the K=10 binary model was trained on (read the
   feature list from the saved model file in models/, don't hardcode it) —
   compute as many of them as are realistically derivable from a live flow
   window; if some CICIoT2023 features can't be computed live (e.g. ones
   needing a longer observation), tell me which ones and suggest whether to
   drop them from that model or approximate them.
4. Feed each completed flow's features into the loaded model and print a
   live log line per flow: timestamp, src->dst, prediction, confidence,
   inference latency in ms.
5. Also write each prediction as a JSON line to a file that the Streamlit
   dashboard could later tail and display live (don't build the dashboard
   side yet, just make the output format sane for that).

Test it by running it while I generate some traffic with ping and a basic
nmap scan from the attacker VM, and tell me what it printed.
```

**Check before moving on:** you see live log lines while traffic is
generated, and predictions look sane (benign for ping, attack-flagged for
the scan) even if not perfectly accurate yet.

---

## Phase 8 — Final integration, cleanup, and report artifacts

```
Do a final pass over the whole project:

1. Review every file in src/ for consistency — make sure config.py is the
   single source of truth for paths/parameters and nothing is hardcoded
   elsewhere.
2. Add basic error handling anywhere a missing file or bad input could
   crash the pipeline ungracefully (data_loader, live_capture, dashboard).
3. Regenerate the final scorecard CSVs and plots using the full dataset
   (DEV_SAMPLE_FRACTION = 1.0 or as high as is practical), and clearly
   label these as the "final" results, separate from earlier dev-run files.
4. Update README.md with: final setup steps, how to reproduce results, how
   to run the dashboard, and how to run live_capture.py in the VM lab
   setup.
5. Give me a short summary (bullet points) of the final best model per task
   (binary and multiclass) — its K, macro-F1, model size, and latency — so
   I can paste this directly into my project report.
```

**Check before moving on:** this is your submission-ready state — clean
code, final results, and a report-ready summary in hand.
