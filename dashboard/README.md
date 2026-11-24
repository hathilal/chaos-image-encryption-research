# FPGA Research Studio

Streamlit dashboard for grayscale chaos-image-encryption experiments.

## Features

- Python software encryption and decryption
- XOR baseline, forward permutation-diffusion and bidirectional diffusion
- FPGA UART transaction interface
- Software and FPGA experiment records
- Image, hash, timing and recovery evidence
- Paired software/FPGA experiment comparisons

## Requirements

Python 3.10 or newer is recommended.

Install dependencies from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r dashboard/requirements.txt
```

## Run

From the repository root:

```bash
streamlit run dashboard/app.py
```

## Research package

The software engine imports the canonical algorithms from:

`python/research/chaos_cipher/`

Do not maintain a separate copy of the cipher algorithms in this dashboard.

## FPGA interface

The current host interface expects the V8 UART protocol:

- Host to FPGA: `CHAO` + operation byte + 16384 image bytes
- FPGA to host: `RDY!` + `DONE` + 16384 output bytes

Default serial port: `/dev/ttyUSB1`

Verify that the connected FPGA firmware implements this exact protocol before
performing a physical transaction.

## Experiment evidence

- `experiments/`: current experiment records and artifacts
- `archive_before_fresh_start/`: preserved historical archive

Archived transaction records are historical evidence. They do not, by
themselves, identify the exact RTL, firmware or bitstream revision.

New experiment artifacts should be reviewed before committing them.
