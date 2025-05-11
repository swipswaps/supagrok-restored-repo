# PRF-SUPAGROK-TIMESCALE-LOADER
# Loads EEG-style rotated log files into Supagrok TimescaleDB

import psycopg2
import os

conn = psycopg2.connect(
    dbname="supagrok",
    user="user",
    password="password",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

for fname in sorted(os.listdir("./logs")):
    if not fname.endswith(".log"):
        continue
    with open(os.path.join("./logs", fname)) as f:
        for line in f:
            try:
                ts, val = line.strip().split("\t")
                cursor.execute(
                    "INSERT INTO eeg_logs (timestamp, magnitude) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (ts, val)
                )
            except Exception as e:
                print(f"❌ Skipping line: {line.strip()} — {e}")

conn.commit()
cursor.close()
conn.close()
