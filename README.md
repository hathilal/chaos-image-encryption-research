# ChaosForge — Reproducible Chaos-Based Image Encryption on FPGA

**Research repository:** fixed-point chaotic image encryption, bit-accurate software modelling, RTL verification, and FPGA implementation.

> **Status:** Active research / hardware integration. This repository is being expanded from the Python reference implementation into a reproducible software–hardware project. FPGA image-transfer firmware and end-to-end on-board image tests are not yet verified. Do not interpret software metrics as FPGA measurements.

## Research goals

1. Build a deterministic, fixed-point reference model for a 3-D chaotic keystream generator.
2. Implement reversible image permutation and diffusion.
3. Verify RTL against the Python golden model and self-checking testbenches.
4. Integrate the accelerator on a Digilent Zybo Z7-10 (XC7Z010CLG400-1).
5. Measure image statistics, execution time, throughput, FPGA resource use, timing, and power reproducibly.
6. Compare results with published methods under equivalent conditions.

## Existing evidence (separate by implementation/configuration)

| Evidence | Current record | Scope |
|---|---:|---|
| Python test suite | 46/46 tests passed | Previously reported software test run; rerun from clean checkout |
| XOR baseline NPCR | 93.07% | Previous 128×128 grayscale software experiment |
| XOR baseline UACI | 30.29% | Same baseline experiment |
| Permutation + diffusion NPCR | 99.5355% | Previous software experiment |
| Permutation + diffusion UACI | 32.7599% | Same software experiment |
| FPGA RTL verification | V7 AXI-stream adapter testbench exists | Simulation evidence only |
| Physical FPGA image upload | Not yet verified | Requires matching ARM firmware / UART-to-DMA bridge |

These values are historical project notes, not a claim of superiority over published methods. Regenerate them with scripts, fixed test images, parameter files, and raw outputs before promotion to a final comparison.

## Hardware target and architecture

- Board: Digilent Zybo Z7-10
- FPGA: Xilinx Zynq-7000 XC7Z010CLG400-1
- Hardware datapath: AXI4-Stream adapter + AXI DMA + Processing System 7
- Image target: 128×128, 8-bit grayscale (16,384 pixels)
- Adapter framing: one 32-bit control/header word followed by 4,096 32-bit pixel words; final input word asserts TLAST.
- The AXI adapter is not a UART receiver. Host-side serial framing must be handled by ARM firmware before DMA submission.

## Repository map

- `docs/` — architecture, verification, literature and experiment protocols
- `literature/` — paper-by-paper evidence and comparison table
- `results/` — machine-readable software and FPGA results
- `python/` — reference model and tests
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
- Do not describe the physical FPGA path as complete until a host-to-board encrypt/decrypt round trip is demonstrated.

## Current next milestone

Complete and verify the Zynq ARM UART-to-AXI-DMA firmware path, transfer a known 128×128 grayscale image, encrypt it on the FPGA, decrypt it, and verify byte-for-byte recovery. See [docs/FPGA_STATUS.md](docs/FPGA_STATUS.md).

See [literature/README.md](literature/README.md) and [literature/COMPARISON.md](literature/COMPARISON.md) for the initial review.
