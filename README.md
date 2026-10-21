# Chaos-Based Image Encryption Research

A hardware-oriented research project exploring a fixed-point chaotic image encryption engine for 128×128 8-bit grayscale images.

## Objectives

- Develop a Python bit-accurate reference model.
- Implement a three-dimensional chaotic system using fixed-point arithmetic and RK2 integration.
- Design reversible image permutation and diffusion stages.
- Implement RTL modules and verify them against the Python model.
- Integrate UART image input, VGA display, and embedded histogram analysis.
- Evaluate finite-precision degradation, image statistics, keystream properties, throughput, and hardware resource usage.

## Development milestones

1. Project specification and architecture.
2. Fixed-point arithmetic and unit tests.
3. Chaotic RK2 generator and golden test vectors.
4. Reversible permutation and diffusion.
5. RTL implementation and bit-exact verification.
6. FPGA integration and demonstration.
7. Security experiments, performance measurements, and final report.

## Repository structure

- `docs/` — project specification, architecture, and verification plan.
- `python/` — reference model and tests.
- `rtl/` — hardware modules and testbenches.
- `firmware/` — embedded software.
- `images/` — test-image documentation and permitted assets.
- `reports/` — experiments and measured results.

## Current status

**Stage 0: Repository setup.** No implementation or experimental results are claimed complete.

## Security note

Chaotic behavior and image metrics such as histogram uniformity, correlation, NPCR, UACI, and statistical test results do not independently establish cryptographic security. Any security claims must be supported by a defined threat model and reproducible evidence.
