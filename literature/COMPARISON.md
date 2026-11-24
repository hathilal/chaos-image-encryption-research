# Benchmark comparison

## A. Internal project baseline

Previously recorded for 128×128 grayscale Python experiments. These values have not yet been regenerated from the current repository commit with raw outputs; treat them as provisional internal records.

| Method | NPCR | UACI | Conditions |
|---|---:|---:|---|
| XOR baseline | 93.07% | 30.29% | 128×128 grayscale; prior internal experiment |
| Permutation + diffusion | 99.5355% | 32.7599% | 128×128 grayscale; prior internal experiment |

Permutation + diffusion improved the recorded values over the simple XOR baseline. It is not evidence of superiority over published algorithms. Its recorded UACI is below several cited examples near 33.4–33.46%, and its NPCR is below many examples near 99.6%. Confirm that the same differential-test protocol was used before drawing even this cross-paper comparison.

## B. Selected published figures

| Paper | Hardware | NPCR | UACI | Entropy | Throughput | Qualification |
|---|---|---:|---:|---:|---:|---|
| Fractional-order multi-stage (2026) | Artix-7 XC7A35T | exact value pending | exact value pending | 7.99855 avg | 78.64 Mbps | Need full paper table and protocol |
| Embedded fast/light chaos (Wiley) | Nexys4 | 99.5978% avg | 33.4549% avg | 7.99943 | 1021.44 Mb/s | Verify resolution and definitions |
| Chaotic box partition / modular diffusion (2026) | FPGA-oriented | 99.605 ± 0.006% | 33.86 ± 1.05% | NR | NR | Preserve individual trial dispersion |
| Complex network / multi-direction diffusion (2022) | Software | 99.6063% | 33.4619% | NR | 1.618 Mbps | Image size requires verification |
| 4D-CSHA lightweight scheme (2026) | FPGA; exact device pending | NR | NR | NR | 557.28 Mbps | 69.66 MHz, 66.68 mW |
| Chaos-driven AES FPGA (2026) | PYNQ-Z2 | around 99.6% | around 33.4% | near 8 | resolution-specific frame rates | Different cipher architecture |

NR = not reliably available from abstract/indexed material. Do not replace NR with estimates.

## C. Honest conclusion

- Previous software record shows permutation + diffusion outperformed the simple XOR baseline on the recorded NPCR/UACI tests.
- Current evidence does not establish better NPCR/UACI than representative published methods.
- FPGA throughput, power and resource comparison is not possible: physical end-to-end FPGA measurements are not verified.
- Improve the algorithm and reproduce fair comparisons; do not cherry-pick metrics.

## D. Next experiments

1. Re-run software tests and metrics from current commit.
2. Use a fixed public grayscale test-image set with licenses and SHA-256 hashes.
3. Run independent trials under a documented one-pixel differential protocol.
4. Add entropy, horizontal/vertical/diagonal correlation, histogram chi-square, key sensitivity, and exact decryption checks.
5. Implement reproducible literature baselines where code/license permits.
6. Complete Zybo PS UART-to-DMA firmware and measure real end-to-end throughput.
7. Extract missing paper values from publisher PDFs, logging exact page/table/figure.
