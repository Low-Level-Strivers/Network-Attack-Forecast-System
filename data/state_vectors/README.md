# Network State Vectors Directory

Stores the 1-minute aggregated network state tables $S(t)$ produced by `src/state_builder/`.
- Format: `.parquet` (primary, fast binary format) or `.csv`
- Schema: `Timestamp`, 20-25 behavioural feature dimensions, ground truth risk and stage annotations.
- Used directly by `src/sequence_builder/` to construct LSTM lookback windows without re-processing raw flows.
