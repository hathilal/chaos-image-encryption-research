# Experiment protocol

For every run, record the Git commit SHA, working-tree status, Python/tool versions, algorithm revision, chaotic/fixed-point parameters, image dimensions and SHA-256, seed/key policy, trial count, and whether the measurement is software, RTL simulation, or physical FPGA.

## Statistical diagnostics

Report cipher histogram and chi-square statistic; global Shannon entropy (maximum 8 bits/pixel for 8-bit grayscale); horizontal, vertical and diagonal adjacent-pixel correlations; NPCR and UACI; key sensitivity; exact correct-key decryption; wrong-key decryption; and NIST SP 800-22 only with sequence length, bitstream construction, configuration and pass criteria.

For two M×N ciphertexts C1 and C2:

- NPCR = 100 × count(C1(i,j) ≠ C2(i,j)) / (M×N)
- UACI = 100 × sum(|C1(i,j) − C2(i,j)|) / (255×M×N)

Document the exact plaintext/key perturbation protocol. NPCR/UACI are diagnostics, not proof against cryptanalysis.

## Performance

Software: report wall-clock time, throughput, warm-up policy, number of trials, mean/stddev, and whether I/O and key generation are included.

FPGA: report part, tool version, clock constraint, timing closure, LUT/FF/BRAM/DSP counts and percentages, end-to-end latency, sustained datapath throughput, DMA/ARM/UART inclusion, and power source (tool estimate vs measured board power).

## Reproducibility artifacts

Each result directory must include machine-readable CSV/JSON, commands/configuration, raw logs, image provenance/license/hash, output hashes, interpretation, and source commit.

A result is publishable only when repeatable from a clean checkout, supported by raw outputs, tied to an identifiable algorithm/configuration, and compared using equivalent definitions.
