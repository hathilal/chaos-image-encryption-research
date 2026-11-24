# Benchmark comparison

## A. Internal project baseline

Previously recorded for 128×128 grayscale Python experiments. These values have not yet been regenerated from the current repository commit with raw outputs; treat them as provisional internal records.

| Method | NPCR | UACI | Conditions |
|---|---:|---:|---|
| XOR baseline | 93.07% | 30.29% | 128×128 grayscale; prior internal experiment |
| Permutation + diffusion | 99.5355% | 32.7599% | 128×128 grayscale; prior internal experiment |

## B. New archived dashboard records (24 November 2026)

Transcribed from three user-provided screenshots of the CHAOS / LAB “Previous Results” page.

| Run | Recovery | Matching pixels | Entropy (bits/pixel) | NPCR | UACI |
|---|---|---:|---:|---:|---:|
| paired_20261124_094043_935727_fpga | PASS | 16,384 | 7.9892 | 99.8596% | 30.8834% |
| paired_20261124_070145_627667_fpga | PASS | 16,384 | 7.9901 | 99.8596% | 30.6938% |
| 20261124_094235_999667 | PASS | 16,384 | 7.9869 | 99.8596% | 30.3743% |

All show 16,384 input bytes (128×128 grayscale). Distinct ciphertext values were not recorded.

**Provenance warning:** the screenshot banner explicitly says the page is a demonstration fallback that reads saved experiment folders and does not perform a live hardware transaction. Therefore these are archived dashboard records with a Zybo Z7-10 label, not independently verified physical FPGA measurements. See [ARCHIVED_DASHBOARD_RUNS.md](../results/fpga/ARCHIVED_DASHBOARD_RUNS.md) and the machine-readable [CSV](../results/fpga/archived_fpga_dashboard_runs.csv).

### Descriptive comparison to prior software record

- Archived dashboard NPCR: 99.8596%, numerically +0.3241 percentage points over the prior software record (99.5355%).
- Archived dashboard UACI: 30.3743–30.8834%, numerically 1.8765–2.3856 percentage points below the prior software record (32.7599%).
- Archived entropy: 7.9869–7.9901 bits/pixel.

This is not a valid algorithm ranking unless the same input images, key, one-pixel perturbation protocol, and metric implementation were used. The three archived entries are not necessarily independent trials. Do not claim the FPGA implementation is superior based on these records.

## C. Selected published figures

| Paper | Hardware | NPCR | UACI | Entropy | Throughput | Qualification |
|---|---|---:|---:|---:|---:|---|
| Fractional-order multi-stage (2026) | Artix-7 XC7A35T | exact value pending | exact value pending | 7.99855 avg | 78.64 Mbps | Need full paper table and protocol |
| Embedded fast/light chaos (Wiley) | Nexys4 | 99.5978% avg | 33.4549% avg | 7.99943 | 1021.44 Mb/s | Verify resolution and definitions |
| Chaotic box partition / modular diffusion (2026) | FPGA-oriented | 99.605 ± 0.006% | 33.86 ± 1.05% | NR | NR | Preserve individual trial dispersion |
| Complex network / multi-direction diffusion (2022) | Software | 99.6063% | 33.4619% | NR | 1.618 Mbps | Image size requires verification |
| 4D-CSHA lightweight scheme (2026) | FPGA; exact device pending | NR | NR | NR | 557.28 Mbps | 69.66 MHz, 66.68 mW |
| Chaos-driven AES FPGA (2026) | PYNQ-Z2 | around 99.6% | around 33.4% | near 8 | resolution-specific frame rates | Different cipher architecture |

NR = not reliably available from abstract/indexed material. Do not replace NR with estimates.

## D. Honest conclusion

- Previous software record shows permutation + diffusion improved on the simple XOR baseline.
- The archived dashboard records show higher NPCR but lower UACI than the previous software record; protocol equivalence and provenance are not established.
- Current evidence does not establish better overall security or superiority over representative published methods.
- FPGA throughput, power and resource comparison is not possible: no independently verified physical end-to-end measurement is documented.
- Improve the algorithm and reproduce fair comparisons; do not cherry-pick metrics.

## E. Next experiments

1. Obtain raw JSON/CSV and logs for the three archived dashboard records.
2. Verify whether the records came from a physical Zybo transaction or a software/demo archive.
3. Re-run software tests and metrics from current commit.
4. Use a fixed public grayscale test-image set with licenses and SHA-256 hashes.
5. Run independent trials under a documented one-pixel differential protocol.
6. Add entropy, horizontal/vertical/diagonal correlation, histogram chi-square, key sensitivity, and exact decryption checks.
7. Complete Zybo PS UART-to-DMA firmware and measure real end-to-end throughput.
8. Extract missing paper values from publisher PDFs, logging exact page/table/figure.
