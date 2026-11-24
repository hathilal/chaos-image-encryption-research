# ChaosForge — Reproducible Chaos-Based Image Encryption on FPGA

**Research repository:** fixed-point chaotic image encryption, bit-accurate software modelling, RTL verification, and FPGA implementation.

> **Status:** Active research / hardware integration. Archived dashboard records now show three exact-recovery PASS entries for the Zybo Z7-10 label, but the dashboard explicitly identifies itself as a demonstration fallback reading saved experiment folders rather than performing a live hardware transaction. These are archived records, not yet independently verified physical FPGA measurements.

## Research goals

1. Build a deterministic, fixed-point reference model for a 3-D chaotic keystream generator.
2. Implement reversible image permutation and diffusion.
3. Verify RTL against the Python golden model and self-checking testbenches.
4. Integrate the accelerator on a Digilent Zybo Z7-10 (XC7Z010CLG400-1).
5. Measure image statistics, execution time, throughput, FPGA resource use, timing, and power reproducibly.
6. Compare results with published methods under equivalent conditions.

## Evidence summary

| Evidence | Current record | Scope |
|---|---:|---|
| Python test suite | 46/46 tests passed | Previously reported software test run; rerun from clean checkout |
| XOR baseline NPCR / UACI | 93.07% / 30.29% | Previous 128×128 grayscale software experiment |
| Permutation + diffusion NPCR / UACI | 99.5355% / 32.7599% | Previous software experiment |
| Archived dashboard recovery | 3 × PASS; 16,384 matching pixels each | User screenshots; dashboard states demonstration fallback, not live hardware transaction |
| Archived dashboard NPCR | 99.8596% in all 3 records | Same provenance limitation; metric protocol/raw files not yet audited |
| Archived dashboard UACI | 30.8834%, 30.6938%, 30.3743% | Same provenance limitation |
| Archived dashboard entropy | 7.9892, 7.9901, 7.9869 bits/pixel | Same provenance limitation |
| Physical FPGA image upload | Not independently verified | Requires raw transaction evidence and matching ARM firmware / UART-to-DMA bridge |

Full transcription and provenance notes: [Archived FPGA dashboard runs](results/fpga/ARCHIVED_DASHBOARD_RUNS.md).

The archived NPCR values are numerically above the prior software record, while the UACI values are below it. Do not claim overall improvement or superiority until both implementations are measured with the same image, key, perturbation protocol, and metric code. Regenerate results with scripts, fixed test images, parameter files, and raw outputs.

## Software and web platform

The repository includes a Python golden/reference model for Lorenz RK2 dynamics, signed fixed-point arithmetic, reversible grayscale permutation and chained-XOR diffusion. It also includes a research web dashboard used to inspect saved experiment folders and display experiment metrics. The dashboard screenshots identify a demonstration-fallback mode; saved records are not proof of live FPGA transactions. See [Software Golden Model and Research Web Platform](docs/SOFTWARE_AND_WEB_PLATFORM.md) and [Python reference documentation](python/README.md).

## Hardware target and architecture

- Board: Digilent Zybo Z7-10
- FPGA: Xilinx Zynq-7000 XC7Z010CLG400-1
- Hardware datapath: AXI4-Stream adapter + AXI DMA + Processing System 7
- Image target: 128×128, 8-bit grayscale (16,384 pixels)
- Adapter framing: one 32-bit control/header word followed by 4,096 32-bit pixel words; final input word asserts TLAST.
- The AXI adapter is not a UART receiver. Host-side serial framing must be handled by ARM firmware before DMA submission.

## Repository map

- `docs/` — architecture, verification, software/web platform, literature and experiment protocols
- `literature/` — paper-by-paper evidence and comparison table
- `results/` — machine-readable software and FPGA results
- `python/` — Python golden/reference model and tests
- `fpga-research-studio-dev/` — research dashboard workspace is maintained in the wider project workspace; canonical source and deployment details still need to be imported/documented
- `rtl/` — RTL modules and testbenches (V7 sources to be integrated)
- `firmware/` — Zynq PS UART/DMA application (not yet verified)
- `scripts/` — reproducible experiment and analysis scripts

## Reproduce the Python reference

```bash
cd python
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
pytest
```

## Comparison policy

We compare only like-for-like measurements. Security diagnostics (entropy, adjacent-pixel correlation, NPCR, UACI, key sensitivity) are distinct from implementation metrics (clock frequency, LUT/FF/BRAM/DSP, power, latency, throughput). State image resolution, channels, test images, number of trials, arithmetic precision, clock, device, and measurement method. Do not claim a better cipher based on a single metric.

## Research integrity

- No fabricated measurements or paper results.
- Distinguish published-paper values from our own measured values.
- Cite original papers and identify exact table/figure/page for extracted results.
- NPCR/UACI and histogram/entropy tests are statistical diagnostics, not proof of cryptographic security.
- Do not describe the physical FPGA path as complete until a host-to-board encrypt/decrypt round trip is demonstrated and supported by transaction logs.

## Current next milestone

Obtain the raw archived run folders and verify their provenance. Then complete the Zynq ARM UART-to-AXI-DMA firmware path, transfer a known 128×128 grayscale image, encrypt it on the physical FPGA, decrypt it, and verify byte-for-byte recovery. See [docs/FPGA_STATUS.md](docs/FPGA_STATUS.md).

See [literature/README.md](literature/README.md) and [literature/COMPARISON.md](literature/COMPARISON.md) for the initial review.
