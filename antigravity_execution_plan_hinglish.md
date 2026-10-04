# Antigravity ke liye Execution Plan — Lightweight IoT IDS (Hinglish)

## Pehle samajh le — kaise use karna hai

Antigravity ek agentic coding tool hai — matlab tu usse bol sakta hai "yeh kar do"
aur woh khud code likh ke, run karke, fix karke result dega. Lekin ek hi bar
mein "poora project bana do" bolna risky hai — agent confuse ho sakta hai ya
galat direction mein chala jayega.

Isliye **phase-by-phase** chalna hai:
1. Ek phase ka prompt copy-paste kar Antigravity mein.
2. Usko kaam karne de, result dekh.
3. Jo "Check before moving on" likha hai, woh verify kar.
4. Sahi laga toh next phase pe jaa. Galat laga toh usi phase mein fix karwa,
   aage mat badh.

Shuru karne se pehle: `lightweight_iot_ids.zip` jo maine diya tha, usko
extract karke us folder mein Antigravity ko open kar — taaki usko pehle se
bana hua scaffold (config.py, data_loader.py, waghera) dikhe.

---

## Phase 0 — Agent ko project samjhao

Pehle Antigravity ko poora context de, taaki woh scaffold ko samjhe bina
kuch tod-phod kiye.

**Prompt (copy-paste karo):**
```
Read through the entire existing project in this directory: src/config.py,
src/data_loader.py, src/preprocess.py, src/feature_selection.py,
src/models.py, src/evaluate.py, main.py, requirements.txt, and README.md.

Give me a short summary of what each file does and how they connect to
each other in the pipeline. Do not modify anything yet — this is just so
you understand the existing code before we start building on top of it.
```

**Kyun zaroori hai:** Agar agent bina samjhe seedha code likhna shuru kar
de, toh woh purane scaffold se clash karega ya duplicate cheeze bana dega.
Yeh step usse "onboard" karta hai.

---

## Phase 1 — Environment set karo + dataset check karo

Yahan se actual kaam shuru. CICIoT2023 ke kuch CSV files download karke
`data/raw/` folder mein daal de pehle (link: `http://cicresearch.ca/IOTDataset/CIC_IOT_Dataset2023/`,
CSV folder wala).

**Prompt:**
```
I have downloaded some CICIoT2023 CSV files into data/raw/. Do the
following:
1. Set up a Python virtual environment and install requirements.txt
   (use --break-system-packages if needed).
2. Run `python -m src.data_loader` to inspect the label column and print
   the unique label values found across the files.
3. Report: how many CSV files in data/raw/, rows/columns in one sample
   file, exact column names, and the unique label values printed.
4. If something errors, fix only what's needed to make step 2 work, and
   explain what you changed.
```

**Check karna hai:** Attack labels ki list clean print honi chahiye
(jaise DDoS-ICMP_Flood, DoS-SYN_Flood, BenignTraffic) — koi error nahi
aana chahiye.

---

## Phase 2 — Category mapping + data cleaning verify karo

Isme hum 33 attack types ko 7 broad categories mein group karenge
(DDoS, DoS, Recon, Web-based, Brute Force, Spoofing, Mirai) — taaki
multiclass classification easy ho.

**Prompt:**
```
Using the unique label values from Phase 1, fill in config.CATEGORY_MAP in
src/config.py to group the raw CICIoT2023 labels into these 7 categories:
DDoS, DoS, Recon, Web-based, Brute Force, Spoofing, Mirai — plus Benign as
its own class. Use the CICIoT2023 paper's official attack-to-category
grouping as the source of truth; look it up if unsure rather than guessing.

Then:
1. Run data_loader + preprocess.prepare_features_and_labels() for both
   task="binary" and task="multiclass" on a small sample.
2. Print: rows before/after cleaning, which columns got dropped as
   leakage-prone, which got dropped as constant, and class distribution
   for both tasks.
3. Confirm the train/test split keeps class proportions similar — print
   proof.
4. Only change preprocess.py/config.py if something is broken.
```

**Check karna hai:** Koi bhi category 0 samples wali nahi honi chahiye,
train-test proportions lagbhag same hone chahiye.

---

## Phase 3 — Feature selection check karo

Yahan model ko decide karwana hai ki 40+ features mein se sabse zaroori
5, 10, 15, 20 kaunse hain.

**Prompt:**
```
Run src/feature_selection.get_feature_subsets() on the cleaned, scaled
binary-task training data from Phase 2.

1. Print the full mutual-information ranking and the pruned ranking after
   correlation-based redundancy removal.
2. Print the exact feature list for K=5, K=10, K=15, K=20.
3. Confirm each smaller-K set is a strict subset of each larger-K set — if
   not, find and fix the bug.
4. Flag anything suspicious — e.g. an identifier-like or near-constant
   feature making it into the top ranks — before proceeding.
```

**Check karna hai:** 4 clean nested feature lists milni chahiye, koi
identifier-type column unme nahi honi chahiye.

---

## Phase 4 — Model training + scorecard (main kaam)

Ab asli training hoga — 4 models (LightGBM, Decision Tree, Logistic
Regression, Random Forest) x 4 K-values (5,10,15,20).

**Prompt:**
```
Run the full pipeline: python main.py, task="binary" first, with
DEV_SAMPLE_FRACTION high enough for a meaningful sample (start around
0.05-0.1, tell me the resulting row count).

1. Confirm results/scorecard.csv and saved models in models/ are produced
   without errors.
2. Print the full scorecard sorted by macro_f1 within each K.
3. Summarize in 3-4 sentences: which model wins at each K, and how model
   size (KB) and latency (ms) trade off against macro_f1 as K decreases.
4. If any model shows macro_f1 > 0.999, STOP and flag it to me — that
   usually means a data leakage bug, not a great model.
5. Repeat with task="multiclass" and give the same summary.
```

**Check karna hai:** Do scorecards (binary + multiclass) milne chahiye,
koi suspiciously perfect score nahi hona chahiye.

---

## Phase 5 — Results ko graph mein dikhao

**Prompt:**
```
Using results/scorecard.csv (binary and multiclass versions), write
src/plots.py to generate and save these to results/plots/:
1. macro_f1 vs K, one line per model
2. model_size_kb vs K, one line per model, log scale y-axis
3. latency_ms vs K, one line per model
4. Confusion matrix heatmap for the best model at K=10, multiclass task

Use matplotlib/seaborn, clear axis labels, save as PNG. Show me file
paths. Read everything from the actual scorecard CSVs, no hardcoded
numbers.
```

**Check karna hai:** 4 PNGs `results/plots/` mein bane hone chahiye,
scorecard ke actual numbers ke saath match karne chahiye.

---

## Phase 6 — Dashboard banao (Streamlit)

Yeh woh UI hai jo evaluators ko live dikhane ke kaam aayegi.

**Prompt:**
```
Build a Streamlit dashboard at dashboard.py with:
1. Sidebar: pick task (binary/multiclass), K (5/10/15/20), model (from
   saved models in models/).
2. Main panel: that model's scorecard metrics as cards, plus the K-vs-
   metric charts from Phase 5 embedded inline.
3. "Try a prediction": upload a CSV or paste one row of feature values,
   show the model's prediction + inference latency for that row.
4. Handle missing model files gracefully — clear message, no crash.

Run with `streamlit run dashboard.py`, confirm it loads without errors,
walk me through each section.
```

Note: Tumhari saved preference ke hisaab se, agar agent koi heavy CSS
(gradients, animations) daalta hai, usse simple/plain UI banane ko bol
do — tum clean minimal look prefer karte ho.

**Check karna hai:** Dashboard browser mein khulna chahiye, saare
sections kaam karne chahiye, ek sample row upload karne pe real
prediction aana chahiye.

---

## Phase 7 — Live detection (VM lab wala part)

Yeh woh part hai jahan tumhara 3-VM lab (Attacker, Victim, IDS) kaam
aayega — real traffic pe live detection dikhega.

**Prompt:**
```
I have a 3-VM lab (Attacker, Victim, IDS) on an isolated internal network,
IDS VM's network adapter in promiscuous mode. Build src/live_capture.py
that runs on the IDS VM:

1. Sniff live traffic on a given interface (CLI argument) using Scapy or
   pyshark — pick whichever is more reliable, explain the choice.
2. Aggregate packets into flows using a sliding time window (parameterize,
   default 2s), grouped by 5-tuple (src ip, dst ip, src port, dst port,
   protocol).
3. Compute the same features the K=10 binary model was trained on (read
   the feature list from the saved model file, don't hardcode). If some
   features can't be computed live, tell me which and suggest whether to
   drop them or approximate.
4. Feed each completed flow into the loaded model, print a live log line:
   timestamp, src->dst, prediction, confidence, inference latency ms.
5. Also write each prediction as a JSON line to a file, so the dashboard
   could later tail it live.

Test by generating ping and a basic nmap scan traffic from the attacker
VM, tell me what it printed.
```

**Check karna hai:** Live log lines dikhni chahiye jab traffic generate
ho raha ho, predictions sensible lagni chahiye (ping = benign, scan =
attack-flagged), even agar perfectly accurate na ho abhi.

---

## Phase 8 — Final polish + report-ready summary

**Prompt:**
```
Do a final pass:
1. Review all of src/ for consistency — config.py should be the single
   source of truth, nothing hardcoded elsewhere.
2. Add basic error handling wherever a missing file/bad input could crash
   things (data_loader, live_capture, dashboard).
3. Regenerate final scorecard CSVs and plots using the full dataset
   (DEV_SAMPLE_FRACTION as high as practical), label clearly as "final"
   results, separate from dev-run files.
4. Update README.md: final setup steps, how to reproduce results, how to
   run the dashboard, how to run live_capture.py in the VM lab.
5. Give me a short bullet-point summary of the final best model per task
   (binary and multiclass) — K, macro-F1, model size, latency — so I can
   paste it directly into my project report.
```

**Check karna hai:** Yeh tumhara submission-ready state hai — clean code,
final results, report ke liye ready summary.

---

## Ek zaroori baat

Har phase ke baad **khud bhi check kar** — sirf agent pe blindly trust mat
karo. Especially Phase 4 mein agar accuracy bohot zyada perfect (99.9%+)
aaye, toh woh achievement nahi, bug hai — data leak ho raha hai matlab.
Agent ko yeh already bola gaya hai flag karne ke liye, par tum bhi dhyan
rakhna.
