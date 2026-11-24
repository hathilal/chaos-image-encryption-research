# Archived FPGA dashboard records — 24 November 2026

These three records were transcribed from user-provided screenshots of the CHAOS / LAB “Previous Results” page. The dashboard identifies the target as Zybo Z7-10 and displays exact recovery PASS, 16,384 matching pixels, 16,384 input bytes, ciphertext entropy, NPCR, and UACI.

**Critical provenance limitation:** the screenshot itself displays a banner stating that this page is a “Demonstration fallback” that reads saved experiment folders and does not perform a live hardware transaction. Therefore, these values are archived dashboard records, not independently verified live FPGA measurements. They must not be presented as proof that the physical Zybo board performed these transactions until raw run artifacts and board/host logs establish that provenance.

## Transcribed values

| Run ID | Exact recovery | Matching pixels | Entropy (bits/pixel) | NPCR | UACI |
|---|---|---:|---:|---:|---:|
| paired_20261124_094043_935727_fpga | PASS | 16,384 | 7.9892 | 99.8596% | 30.8834% |
| paired_20261124_070145_627667_fpga | PASS | 16,384 | 7.9901 | 99.8596% | 30.6938% |
| 20261124_094235_999667 | PASS | 16,384 | 7.9869 | 99.8596% | 30.3743% |

Input size shown: 16,384 bytes (128×128 8-bit grayscale).

“Distinct ciphertext values” is shown as “Not recorded” in all screenshots.

## Descriptive summary

- Exact recovery is displayed as PASS in all three archived records.
- Matching pixel count is 16,384 in all three.
- NPCR is 99.8596% in all three.
- UACI ranges from 30.3743% to 30.8834%.
- Entropy ranges from 7.9869 to 7.9901 bits/pixel.

Across these three records, the arithmetic mean UACI is 30.6505% (descriptive statistic calculated from the displayed values). Mean entropy is 7.9887 bits/pixel. Do not treat three archived records as independent scientific trials unless their input images, keys, perturbation protocol, and run independence are established.

## Comparison to prior internal software record

Prior internal permutation+diffusion record: NPCR 99.5355%, UACI 32.7599%. The archived dashboard NPCR is numerically higher by 0.3241 percentage points, while its UACI values are numerically lower by 1.8765–2.3856 percentage points. This is not a valid algorithm ranking unless both use the same input image, key, one-pixel perturbation protocol, and metric implementation.

## Required evidence before calling these physical FPGA results

1. Original JSON/CSV/raw result folder for each run.
2. Host application logs with timestamps and image hashes.
3. Exact bitstream/XSA hashes and firmware ELF/source revision.
4. UART/DMA transaction logs showing data transfer to and from the board.
5. Reproduction of at least one run with the physical Zybo connected.
6. A documented metric script and identical NPCR/UACI protocol across software and FPGA.

Machine-readable transcription: [archived_fpga_dashboard_runs.csv](../results/fpga/archived_fpga_dashboard_runs.csv).
