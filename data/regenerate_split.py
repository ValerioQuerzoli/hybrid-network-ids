# Rebuilds the cleaned CIC-IDS2017 split (train/val/test parquet) used by the notebook.
# Usage: python regenerate_split.py [output_dir]   (default: this script's directory)
import os, sys
import pandas as pd, kagglehub
from sklearn.model_selection import train_test_split

out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
path = kagglehub.dataset_download("dhoogla/cicids2017")
# Fixed file order (the os.listdir order of the original run): row order changes the split.
order = ['Infiltration-Thursday-no-metadata.parquet', 'Botnet-Friday-no-metadata.parquet',
         'Benign-Monday-no-metadata.parquet', 'DDoS-Friday-no-metadata.parquet',
         'WebAttacks-Thursday-no-metadata.parquet', 'Bruteforce-Tuesday-no-metadata.parquet',
         'Portscan-Friday-no-metadata.parquet', 'DoS-Wednesday-no-metadata.parquet']
dataset = pd.concat([pd.read_parquet(os.path.join(path, f)) for f in order])
print("initial shape", dataset.shape)

# Some labels lost a byte upstream ("Web Attack � XSS"); the original character is not recoverable.
corrupted = dataset["Label"].str.contains("�").sum()
dataset["Label"] = dataset["Label"].str.replace("�", "-", regex=False)
print("corrupted labels:", corrupted)

# Columns that must never be negative (CICFlowMeter bug). Init Fwd/Bwd Win Bytes are left alone:
# there -1 is a legitimate sentinel.
dirty_cols = ['Flow IAT Min', 'Flow IAT Mean', 'Flow Duration', 'Flow Packets/s', 'Flow IAT Max',
              'Flow Bytes/s', 'Fwd Header Length', 'Fwd Seg Size Min', 'Bwd Header Length', 'Fwd IAT Min']
dirty_rows = (dataset[dirty_cols] < 0).any(axis=1)
print("rows removed:", dirty_rows.sum())
clean = dataset[~dirty_rows]

train, temp = train_test_split(clean, train_size=0.6, stratify=clean["Label"], random_state=42)
val, test = train_test_split(temp, test_size=0.5, stratify=temp["Label"], random_state=42)
print(train.shape, val.shape, test.shape)
for name, df in [("train", train), ("val", val), ("test", test)]:
    df.to_parquet(os.path.join(out, f"{name}.parquet"))
