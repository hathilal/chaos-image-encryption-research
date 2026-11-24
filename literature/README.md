# Literature review — chaotic image encryption and FPGA

Initial screening list, not an exhaustive systematic review. Values below come from publisher pages or indexed article text and must be checked against publisher PDFs (exact table, image size, and measurement conditions) before formal publication.

## 1. Fractional-order chaos-driven multi-stage image encryption (Scientific Reports, 2026)
Publisher: https://www.nature.com/articles/s41598-026-72848-6

- FPGA: Artix-7 XC7A35T.
- Reported throughput: 78.64 Mbps.
- Reported average encrypted-image entropy: 7.99855.
- Multi-stage permutation/substitution/diffusion using fractional-order chaotic generators.
- Exact NPCR/UACI and resource table still need extraction; do not infer missing values.

## 2. On the Embedded of a Fast, Light and Robust Chaos-Based Cryptosystem in NEXYS4 FPGA Card for Real Time Color Image Security (Engineering Reports / Wiley)
DOI: https://doi.org/10.1002/eng2.70319

- Platform: Nexys4 FPGA.
- Reported global entropy: 7.99943.
- Average NPCR: 99.5978%; average UACI: 33.4549%.
- Maximum operating frequency: 42.56 MHz.
- Throughput: 1021.44 Mb/s.
- Reported power: 115 mW.
- Confirm resolution, metric definitions, resource table, and measurement conditions from the paper before direct ranking.

## 3. Image Encryption Using Chaotic Box Partition–Permutation and Modular Diffusion with PBKDF2 Key Derivation (Cryptography, 2026)
Publisher: https://www.mdpi.com/2624-800x/6/1/21

- Five-trial summary visible in the publisher-indexed text: NPCR 99.605 ± 0.006%; UACI 33.86 ± 1.05%.
- UACI variability is material; preserve individual trials and examine the paper's exact test protocol.

## 4. An Image Encryption Algorithm Based on Complex Network Scrambling and Multi-Directional Diffusion (Entropy, 2022)
Publisher: https://www.mdpi.com/1099-4300/24/9/1247

- Reported NPCR: 99.6063%; UACI: 33.4619%.
- Reported encryption time: 0.324 s; speed: 1.618 Mbps.
- Verify image dimensions and implementation conditions before comparison.

## 5. A Difference-Equation-Based Robust Image Encryption Scheme with Chaotic Permutations and Logic Gates (Journal of Mathematical Imaging and Vision, 2022)
Publisher: https://link.springer.com/article/10.1007/s10851-022-01099-7

- Useful methodological reference for NPCR/UACI definitions and differential-image evaluation.
- Numerical results should be extracted from the original paper tables before inclusion in a ranked comparison.

## 6. FPGA implementation of 4D-CSHA chaotic system with hidden attractors for lightweight image encryption (2026)
Publisher: https://www.sciencedirect.com/science/article/pii/S0167926026002130

- Reported maximum operating frequency: 69.66 MHz.
- Reported throughput: 557.28 Mbps.
- Reported total power: 66.68 mW.
- Abstract indicates key-space, key-sensitivity, histogram, entropy, correlation, NPCR and UACI analyses.
- Extract exact device and resource metrics from full paper before comparison.

## 7. A high-throughput FPGA-based image encryption architecture using a CBC-inspired chaos-driven AES scheme (2026)
DOI: https://doi.org/10.1016/j.vlsi.2026.102817

- Platform: Xilinx PYNQ-Z2, AXI4-Stream + DMA, pipelined AES-128 and 3-D chaotic system.
- Abstract reports >11,400 frames/s for 256×256 grayscale, ~819 frames/s for 512×512 RGB, and ~100 frames/s for Full HD RGB.
- Different cipher construction: cite as an FPGA architecture/throughput reference, not proof of stronger chaotic cipher security.

## Review extraction fields
Record DOI/year, image size/channels, cipher structure, chaotic system, arithmetic precision, test images, NPCR, UACI, entropy, three-direction correlations, key space, key-sensitivity protocol, NIST details, software time, FPGA device, clock, LUT/FF/BRAM/DSP, power, throughput, and exact table/figure/page. Use NR for not reported. Do not invent or estimate missing values.

Do not claim state-of-the-art or superiority until the table is complete and conditions normalized.
