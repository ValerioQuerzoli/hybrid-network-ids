# Data

Source: CIC-IDS2017, Kaggle mirror [`dhoogla/cicids2017`](https://www.kaggle.com/datasets/dhoogla/cicids2017)
(8 parquet files, 2,313,810 flows × 78 columns: 77 CICFlowMeter features + `Label`).

The parquet files are not in the repository. `python regenerate_split.py` downloads the mirror and
writes `train.parquet`, `val.parquet`, `test.parquet` here; the notebook also calls the same logic
if the files are missing.

## Cleaning

1. **Corrupted labels.** 2,143 rows had a `Label` with the replacement character U+FFFD
   (`Web Attack � XSS`): the original byte was lost upstream in the mirror. Replaced with `-`.
2. **Invalid negative values.** 12 columns contain negatives. Two of them (`Init Fwd Win Bytes`,
   `Init Bwd Win Bytes`) have a single negative value, `-1`, used as a sentinel: kept. The other 10
   (`Flow Duration`, `Flow IAT Min/Mean/Max`, `Flow Bytes/s`, `Flow Packets/s`, `Fwd/Bwd Header Length`,
   `Fwd Seg Size Min`, `Fwd IAT Min`) cannot be negative: the 2,843 affected rows were removed.

After cleaning: 2,310,967 rows.

## Split

Stratified on `Label`, `random_state=42`, 60/20/20:

| split | rows |
|---|---|
| train | 1,386,580 |
| validation | 462,193 |
| test | 462,194 |

Class counts after the label fix, before removing the 2,843 rows (full dataset, 2,313,810 rows):

| Label | rows |
|---|---|
| Benign | 1,977,318 |
| DoS Hulk | 172,846 |
| DDoS | 128,014 |
| DoS GoldenEye | 10,286 |
| FTP-Patator | 5,931 |
| DoS slowloris | 5,385 |
| DoS Slowhttptest | 5,228 |
| SSH-Patator | 3,219 |
| PortScan | 1,956 |
| Web Attack - Brute Force | 1,470 |
| Bot | 1,437 |
| Web Attack - XSS | 652 |
| Infiltration | 36 |
| Web Attack - Sql Injection | 21 |
| Heartbleed | 11 |
