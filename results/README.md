# Experimental results

Only store values with traceable raw evidence. Each experiment should have its own directory named with date and short experiment ID, containing:

- `metrics.csv` or `metrics.json`
- `config.yaml` / command line
- `raw.log`
- `README.md` interpretation
- hashes and provenance of input/output images
- commit SHA and tool versions

Directories:
- `software/` — Python model metrics
- `fpga/` — RTL simulation and physical FPGA reports

Historical values copied into this repository are explicitly marked provisional in `software/provisional_baseline.csv`; they are not reproduced results.
