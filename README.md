# ChaosForge — Reproducible Chaos-Based Image Encryption Research

Research code and a Streamlit dashboard for studying chaos-based grayscale image encryption, with an FPGA-oriented development track targeting the Digilent Zybo Z7-10.

> **Project status:** Experimental research. The software implementations and dashboard are available in this repository. Physical FPGA end-to-end operation is **not yet independently verified**. Archived experiment records must not be interpreted as fresh hardware measurements.

## What is in this repository?

- **Python reference implementations** — two code areas are maintained separately:
  - `python/src/chaos_image_encryption/`: installable Python package with the Lorenz/fixed-point model and grayscale image-cipher baseline.
  - `python/research/chaos_cipher/`: research algorithms and analysis modules used by the research dashboard.
- **Research dashboard** — `dashboard/`, a Streamlit application for running software experiments, reviewing saved records, and examining metrics.
- **Tests and experiment outputs** — `python/tests/`, `python/research/tests/`, `python/research/reports/`, and `dashboard/experiments/`.
- **Documentation** — `docs/` and the READMEs within the Python and dashboard directories.
- **FPGA status and evidence** — `docs/FPGA_STATUS.md` and `results/fpga/ARCHIVED_DASHBOARD_RUNS.md`.

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/hathilal/chaos-image-encryption-research.git
cd chaos-image-encryption-research
```

### 2. Run the installable Python package tests

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
```

The package currently uses the Python standard library. See [python/README.md](python/README.md) for its API, fixed-point contract, and limitations.

### 3. Run the research algorithm tests

From the repository root, in a separate terminal or after returning to the root:

```bash
cd python/research
python3 -m unittest discover -s tests -v
```

Run a research module from `python/research/`, for example:

```bash
python3 -m chaos_cipher.validate_bidirectional
python3 -m chaos_cipher.test_key_sensitivity
```

See [python/research/README.md](python/research/README.md) for the research package structure and commands.

### 4. Launch the research dashboard

From the repository root:

```bash
python3 -m venv .venv-dashboard
source .venv-dashboard/bin/activate
python -m pip install --upgrade pip
python -m pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`. The repository contains dashboard source code; it does **not** currently establish a publicly hosted dashboard URL.

See [dashboard/README.md](dashboard/README.md) for dashboard features, local setup, experiment storage, and FPGA interface limitations.

## Evidence and research results

The repository contains historical software metrics and archived dashboard records. Treat each result according to its provenance:

| Result | Reported value | Interpretation |
|---|---:|---|
| Earlier XOR baseline | NPCR 93.07%; UACI 30.29% | Previously reported 128×128 grayscale software experiment |
| Earlier permutation + diffusion | NPCR 99.5355%; UACI 32.7599% | Previously reported software experiment |
| Archived dashboard recovery records | 3 PASS records; 16,384 matching pixels each | Archived records; dashboard fallback is not evidence of a live FPGA transaction |
| Archived dashboard NPCR | 99.8596% | Historical record; verify raw inputs, protocol, and metric implementation before comparison |
| Archived dashboard UACI | 30.8834%, 30.6938%, 30.3743% | Historical records; not directly comparable without matching protocol |
| Physical FPGA round trip | Not independently verified | Requires traceable host-to-board encryption and decryption evidence |

See [archived dashboard records](results/fpga/ARCHIVED_DASHBOARD_RUNS.md) and [FPGA status](docs/FPGA_STATUS.md).

Do not claim that one cipher is superior based on a single metric. NPCR, UACI, entropy, and correlation are statistical diagnostics; they do not establish cryptographic security. Comparisons require the same image, key/perturbation protocol, dimensions, metric implementation, and number of trials.

## FPGA development status

The documented target is the Digilent Zybo Z7-10 (XC7Z010CLG400-1). The V7 design notes describe a Processing System 7, AXI DMA, and AXI4-Stream adapter. The adapter is **not** itself a UART receiver. The host-side serial protocol requires matching Zynq PS firmware to receive the serial payload and submit the data through DMA.

The current host interface and the documented V7 AXI-stream adapter are not, by themselves, a verified end-to-end system. Do not connect and run a physical transfer until the exact firmware/bitstream pair and protocol have been checked. Follow the checklist in [docs/FPGA_STATUS.md](docs/FPGA_STATUS.md).

## Research integrity and limitations

- This is experimental research software, not a production-secure encryption product.
- Do not use it to protect sensitive or valuable data.
- Statistical image metrics and chaotic dynamics do not prove resistance to cryptanalysis.
- Distinguish software execution, RTL simulation, implementation reports, archived records, and physical-board measurements.
- Preserve input data, parameters, source revision, raw outputs, hashes, and environment details for reproducibility.
- Do not present archived or demonstration-fallback records as newly executed FPGA experiments.

## Contributing and reuse

The repository is released under the MIT License. See [LICENSE](LICENSE). If you reuse the algorithms, dashboard, or results in academic work, cite the repository using [CITATION.cff](CITATION.cff) and cite any original papers whose methods you build upon.

For known limitations and the current implementation details, start with:
- [Python reference model](python/README.md)
- [Research algorithms](python/research/README.md)
- [Dashboard guide](dashboard/README.md)
- [Software and web platform notes](docs/SOFTWARE_AND_WEB_PLATFORM.md)
- [FPGA status](docs/FPGA_STATUS.md)
