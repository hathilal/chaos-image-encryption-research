# FPGA Research Studio Dashboard

A Streamlit research interface for grayscale chaos-image-encryption experiments.

## Features

- Python software encryption and decryption
- XOR baseline, forward permutation-diffusion, and bidirectional diffusion
- Saved software and FPGA-labelled experiment records
- Image, hash, timing, recovery, and metric presentation
- Paired software/FPGA record comparisons where matching records exist
- Host-side serial transaction interface (requires compatible target firmware)

## Requirements

- Python 3.10 or newer
- Dependencies listed in `requirements.txt`

## Install and run

Run from the repository root:

```bash
python3 -m venv .venv-dashboard
source .venv-dashboard/bin/activate
python -m pip install --upgrade pip
python -m pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

Streamlit prints a local URL, normally `http://localhost:8501`. This repository contains the application source and local setup instructions; a public hosted deployment URL has not been verified.

## Research algorithm integration

The dashboard imports the research algorithms from:

`python/research/chaos_cipher/`

The integration layer is `dashboard/software_engine.py`. Keep the research implementation canonical; do not create an undocumented duplicate copy of the algorithms in the dashboard.

## Experiment data

- `experiments/`: saved experiment records and artifacts
- `archive_before_fresh_start/`: preserved historical archive
- `artifacts/`: local application artifacts created during use

The dashboard reads saved experiment folders. Records without explicit live-execution provenance are labelled historical/restored. Archived records and screenshots are not proof of a live physical FPGA transaction.

## Host serial interface and FPGA limitations

The host interface currently expects this serial framing:

- Host to target: `CHAO` + operation byte + 16,384 image bytes
- Target to host: `RDY!` + `DONE` + 16,384 output bytes
- Default serial port: `/dev/ttyUSB1`

The documented V7 FPGA adapter is an AXI4-Stream endpoint, not a UART parser. Compatible Zynq PS firmware must receive the serial payload and pass it to the adapter through AXI DMA. Do not attempt a physical transaction until the firmware, protocol, bitstream, and board setup have been verified together. See [`docs/FPGA_STATUS.md`](../docs/FPGA_STATUS.md).

## Security and research limitations

This is experimental research software, not production cryptography. Statistical metrics such as entropy, NPCR, UACI, and adjacent-pixel correlation do not prove cryptographic security. Do not use the project to protect sensitive data.
