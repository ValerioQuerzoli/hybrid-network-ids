# Hybrid network IDS: XGBoost + Benign-only autoencoder

Intrusion detection on network flows (CIC-IDS2017). XGBoost classifies known attacks. Every flow it labels
Benign is checked again by an autoencoder trained only on normal traffic; a high reconstruction error
raises an alert.

University project work (Python, deep learning and computer vision course). Slides, in Italian:
[`slides/presentazione_design_origin_v2.pdf`](slides/presentazione_design_origin_v2.pdf).

## Why a second stage

On tabular flow features, tree ensembles are hard to beat: XGBoost trained on all classes already reaches
97.9% attack recall on the test set. The weak point is attacks that never appeared in training. A supervised
model can only recognise what it has seen. An autoencoder trained on Benign traffic does not need attack
labels, so for it every attack is unseen. The question this project answers is how much of a zero-day the
second stage recovers, and at what false-alarm cost.

## Method

- **Data.** CIC-IDS2017, 77 CICFlowMeter features per flow. Fixed corrupted labels, removed 2,843 rows with
  impossible negative values, stratified 60/20/20 split (seed 42). Details in [`data/README.md`](data/README.md).
- **Classifier.** Random Forest and XGBoost baselines, with and without class weights.
- **Autoencoder.** MLP 77 → 32 → 16 → 32 → 77, dropout 0.1, trained full-batch on Benign flows only.
  Two models, one on standardised features and one on signed-log features; the anomaly score is the mean of
  their errors, each normalised by its own 99th Benign percentile.
- **Threshold.** A percentile of the Benign validation score: the 99th percentile means ~1% extra false
  positives by construction, the 99.9th ~0.1%.
- **Zero-day test.** A binary XGBoost is retrained without one attack family at a time; the autoencoders
  are unchanged.
- All weights, thresholds and model choices are made on validation. The test set is used once, at the end.

## Results (test set)

Zero-day, one family left out of XGBoost training, threshold at the 99th percentile:

| Family left out | Test cases | XGBoost alone | XGBoost + autoencoder |
|---|---|---|---|
| DoS / DDoS | 64,317 | 18.1% | **74.7%** |
| Web attack | 428 | 61.7% | 61.7% |
| PortScan | 391 | 12.8% | 12.8% |
| Brute force (FTP/SSH) | 1,829 | 0.3% | 0.4% |
| Bot | 287 | 0.0% | 3.8% |
| Infiltration | 7 | 0.0% | 42.9% |
| Heartbleed | 1 | 0.0% | 100% |

Cost: 3,944 extra false alarms out of 394,934 Benign test flows (1.0%). "Extra" counts only those added by the autoencoder; the pipeline's total false alarms also include XGBoost's (3,988 in total in this DoS zero-day scenario). At the 99.9th percentile the DoS
recall is 47.4% with 393 extra false alarms.

Retraining the autoencoders with 5 different seeds (thresholds always from validation): DoS zero-day recall
74.1% ± 0.5% at the 99th percentile, 44.0% ± 1.6% at the 99.9th.

When XGBoost has seen every class, the autoencoder moves recall only from 97.9% to 98.4%. The second stage
is useful for attacks missing from the training data, not as a general improvement.

What the numbers say:

- The gain is on DoS, whose flows look anomalous one at a time.
- Port scans, brute force and bots look normal flow by flow; the anomaly is in the sequence of flows, which a
  per-flow model does not see.
- Web attacks live in the request payload, which flow features do not contain.
- Infiltration and Heartbleed have 7 and 1 test cases: those percentages are not estimates.

Autoencoder inference on a GTX 1070 runs at ~94 million flows/s with data already in GPU memory. This
excludes feature extraction and the CPU→GPU copy; it only shows the autoencoder is not the bottleneck.

## Limits

- **Flow features only.** No packet content: payload attacks (SQL injection, XSS) are out of reach by
  construction, and on encrypted traffic no network-level fix exists.
- **In-domain numbers are optimistic.** Random split: flows of the same attack session end up in both train
  and test.
- **No transfer across networks.** Models trained on CIC-IDS2017 fail on CSE-CIC-IDS2018 and CIC-DDoS2019
  (XGBoost ~0% recall; the 2017 autoencoder flags 37% of 2018 normal traffic). Normal traffic differs between
  networks, so the autoencoder needs a baseline trained on the network where it runs. These are results of an
  earlier run, reported in section 9 of the notebook; its cells are switched off by default
  (`ESEGUI_CROSS_DATASET = False`), so the saved notebook has no outputs for them.
- **An alert is not a classification.** The autoencoder flags deviations from learned normal traffic; part of
  the false alarms is likely legitimate but unusual traffic.

## Repository

```
notebook/hybrid_ids.ipynb   full pipeline, with saved outputs
data/regenerate_split.py    downloads CIC-IDS2017 and rebuilds the cleaned split
data/README.md              cleaning rules and split sizes
slides/                     presentation (Italian), PDF and PPTX
requirements.txt
```

Variable and function names in the notebook are in Italian; everything else is in English.

## Reproduce

```bash
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu126
python data/regenerate_split.py      # ~300 MB of parquet in data/
jupyter notebook notebook/hybrid_ids.ipynb
```

The notebook expects a CUDA GPU: XGBoost uses `device="cuda"`; PyTorch falls back to CPU.

## References

- I. Sharafaldin, A. H. Lashkari, A. A. Ghorbani, "Toward Generating a New Intrusion Detection Dataset and
  Intrusion Traffic Characterization", ICISSP 2018 (CIC-IDS2017).
- M. Lanvin et al., "Errors in the CICIDS2017 dataset and the significant differences in detection
  performances it makes", CRiSIS 2022.
- Kaggle mirror used: [`dhoogla/cicids2017`](https://www.kaggle.com/datasets/dhoogla/cicids2017).
