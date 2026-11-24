# Software Reference Model and Research Dashboard

This document describes the software components currently present in this repository. It separates the installable Python reference package from the research algorithms used by the Streamlit dashboard. It also distinguishes saved dashboard records from verified physical FPGA execution.

## 1. Repository software components

There are two Python code areas with different purposes:

| Path | Purpose | Documentation |
|---|---|---|
| `python/src/chaos_image_encryption/` | Installable reference package: Lorenz model, fixed-point arithmetic, and grayscale byte-image cipher | `python/README.md` |
| `python/research/chaos_cipher/` | Research algorithms, analysis, and experiment modules used by the dashboard | `python/research/README.md` |
| `dashboard/` | Streamlit user interface, software experiment integration, saved experiment display, and host-side serial interface | `dashboard/README.md` |

Do not assume the two Python code areas implement identical algorithms or numerical formats. In particular, the Q19 fixed-point contract described in `python/README.md` belongs to the installable reference package. Research algorithms under `python/research/chaos_cipher/` have their own implementation and parameters.

## 2. Installable Python reference package

Location: `python/src/chaos_image_encryption/`

The package documentation describes:
- a floating-point Lorenz system using explicit midpoint RK2;
- signed fixed-point arithmetic;
- a fixed-point Lorenz/RK2 model;
- grayscale byte-image permutation and chained-XOR diffusion;
- inverse decryption and round-trip tests.

The documented default fixed-point format for this package is 32-bit signed with 19 fractional bits. Float conversion uses round-to-nearest, ties away from zero. Multiplication uses a full-width integer product followed by an arithmetic right shift. The overflow policy is explicit (`raise` by default or `wrap`).

These are reference-model semantics, not evidence that the format is optimal or that a particular RTL revision is bit-exact. RTL equivalence requires matching operation order, intermediate widths, rounding, overflow, and test vectors.

### Run package tests

From the repository root:

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
```

The package currently declares Python >=3.10 and no third-party runtime dependencies in `python/pyproject.toml`.

## 3. Research algorithms

Location: `python/research/chaos_cipher/`

This directory contains the research implementation and analysis modules used by the dashboard. The adjacent `tests/` directory contains its test suite, and `reports/` contains generated metrics, CSV/JSON results, and plots.

### Run research tests

From the repository root:

```bash
cd python/research
python3 -m unittest discover -s tests -v
```

Example analysis modules:

```bash
python3 -m chaos_cipher.validate_bidirectional
python3 -m chaos_cipher.test_key_sensitivity
```

Run these commands from `python/research/` so that the `chaos_cipher` package is on the module search path.

The research README warns that the implementations are experimental and not suitable for protecting sensitive data without further cryptographic analysis. Statistical image metrics alone do not establish cryptographic security.

## 4. Streamlit research dashboard

Location: `dashboard/`

The application entry point is `dashboard/app.py`. It integrates research algorithms through `dashboard/software_engine.py` and contains a host-side serial interface in `dashboard/fpga_link.py`.

Documented dashboard capabilities include:
- software encryption and decryption experiments;
- XOR baseline, forward permutation-diffusion, and bidirectional diffusion;
- saved software and FPGA-labelled experiment records;
- image, hash, timing, recovery, and statistical metric presentation;
- paired software/FPGA experiment comparisons where records are available.

### Local installation and launch

From the repository root:

```bash
python3 -m venv .venv-dashboard
source .venv-dashboard/bin/activate
python -m pip install --upgrade pip
python -m pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

The dashboard dependencies are listed in `dashboard/requirements.txt`. The app stores local artifacts and experiment records in the dashboard workspace. Do not assume records created on one machine are automatically available on another.

### Hosted deployment status

This repository contains the dashboard source code and local run instructions. A public hosted deployment URL has not been verified. Running `streamlit run` locally is not the same as deploying a public website.

## 5. Experiment provenance and archived records

Dashboard records are stored under `dashboard/experiments/`; preserved historical files are under `dashboard/archive_before_fresh_start/`. The dashboard classifies records without explicit `execution_provenance: live_execution` metadata as historical/restored.

The archived records documented in `results/fpga/ARCHIVED_DASHBOARD_RUNS.md` must be treated as historical evidence. The dashboard has previously displayed a demonstration-fallback notice indicating that it was reading saved experiment folders rather than performing a live hardware transaction.

A dashboard label, a PASS label, an image, or a metric is not sufficient by itself to prove a physical FPGA run. To support a hardware claim, retain at minimum:
- exact board and device;
- exact bitstream hash and firmware identity;
- source revision and build reports;
- input image and SHA-256;
- raw ciphertext/recovered payloads and SHA-256 values;
- timestamped host/board transaction log;
- exact recovery comparison;
- metric script, parameters, and raw outputs.

Do not count duplicate backup folders or UI-fix copies as independent experiments.

## 6. FPGA host interface and protocol limitation

The host-side dashboard interface documents a serial framing protocol:
- host to target: `CHAO` + operation byte + 16,384 image bytes;
- target to host: `RDY!` + `DONE` + 16,384 output bytes;
- default host serial port: `/dev/ttyUSB1`.

The V7 FPGA architecture described in `docs/FPGA_STATUS.md` uses a Zynq Processing System, AXI DMA, and an AXI4-Stream adapter. That adapter does not parse the host serial framing. Matching Zynq PS firmware is required to receive the serial data and submit it through DMA.

**Do not treat the dashboard's host serial interface and the V7 AXI-stream adapter as an integrated, verified hardware path.** Verify the firmware, protocol, bitstream, and board identity before attempting a physical transaction.

## 7. Reproducible research reporting

For each experiment, record:
- algorithm name and source revision;
- input image, dimensions, pixel format, and SHA-256;
- key, initialization values, warm-up count, and all algorithm parameters;
- number of trials and perturbation/randomization protocol;
- metric definitions and implementation revision;
- raw per-trial outputs, not only averages;
- Python/dependency versions and execution environment;
- evidence class: software, RTL simulation, FPGA implementation report, archived record, or physical board.

Separate security diagnostics (entropy, correlation, NPCR, UACI, key sensitivity) from implementation metrics (latency, throughput, LUT/FF/BRAM/DSP, timing, and power). Neither category alone proves cryptographic security.

## 8. Known limitations

- The image-cipher reference package accepts raw grayscale pixel bytes; its README does not document general image-file I/O as part of the package API.
- The algorithms are experimental baselines, not production cryptography.
- The dashboard's saved experiment view does not independently establish live hardware execution.
- The physical FPGA encrypt/decrypt round trip remains unverified in the repository's current status notes.
- A public hosted dashboard deployment has not been verified.
