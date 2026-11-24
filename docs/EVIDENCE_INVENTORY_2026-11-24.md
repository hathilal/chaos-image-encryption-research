# Evidence inventory from local project inspection

Inspection date: 2026-11-24 (based on the supplied terminal sessions).
Source: terminal output supplied by the project maintainer. This document inventories files and log messages; it is not an independent rerun.

## 1. RTL simulation evidence found

The following log messages were visible in `P5_Project_Evidence/03_Testbench_Results`:

| Revision / test | Evidence visible in log | Interpretation |
|---|---|---|
| Full-frame integration | Encryption output count 16,384; decryption output count 16,384; pixel mismatches 0; RESULT: PASS | Full-frame simulation round-trip passed for that test |
| V2 baseline | Encryption/decryption output count 16,384; pixel mismatches 0; RESULT: PASS | V2 full-frame simulation passed |
| V2 BRAM refactor | Encryption/decryption output count 16,384; pixel mismatches 0; RESULT: PASS | V2 BRAM-refactor full-frame simulation passed |
| V3 Zybo wrapper | RESULT: PASS; encryption and decryption completed; wrapper functional test passed | Wrapper simulation passed |
| V5 keystream | Key loaded, warm-up completed, keystream test passed | Keystream simulation passed |
| V5 Lorenz | TEST 1 PASSED | At least the logged Lorenz test passed; inspect full log for coverage |
| V5 rekey | Both key warm-ups completed; rekey handshake passed; error count 0 | Rekey handshake simulation passed |
| V5 Zybo demo | RESULT: PASS; encryption/decryption completed; wrapper functional test passed | V5 wrapper simulation passed |
| V6 diffusion | Encryption and decryption each matched all 16,384 pixels; exact round-trip recovery passed | Diffusion simulation passed |
| V6 wrapper | Total errors 0; chaotic keystream integration passed; exact diffusion reference match passed | Wrapper integration simulation passed |
| V6 Zybo / BRAM | RESULT: PASS; encryption/decryption completed; wrapper functional test passed | V6 wrapper simulations passed |

These are simulation results. They do not, by themselves, prove that the same design completed a live host-to-board image transaction.

## 2. Source and testbench artifacts found

The supplied inventory includes:
- V1 top-level RTL and testbench.
- V5 Lorenz, keystream/rekey and Zybo demo testbenches.
- V6 frozen RTL snapshots, including top-level, keystream, permutation, diffusion, Lorenz, frame controller and wrapper modules.
- V6 testbenches for top-level, keystream, rekey, diffusion, permutation, frame controller and Zybo demo.
- V6 XDC and Tcl scripts for synthesis, implementation, programming and JTAG inspection.

The V6 frozen source snapshot is a valuable historical baseline. Preserve its SHA256 manifest and do not silently replace it with V7 sources.

## 3. Vivado reports and hardware artifacts found

The supplied inventory includes:
- Full-top synthesis timing, critical-path, timing-check and utilization reports.
- V2 BRAM-refactor synthesis and timing reports.
- Zybo demo synthesis reports for several revisions.
- V5 implementation reports: routed timing, hold paths, route status, placed/routed utilization and routed checkpoint.
- V6 implementation reports: DRC, routed timing, hold paths, route status and placed/routed utilization.
- V6 bitstream log, programming log, JTAG scan log, and a V6 bitstream.
- V6 bitstream SHA256 manifest.
- V7 development logs covering block design, PS7, AXI interconnect, BRAM, clocks, resets, address map and board inspection.

Important: the presence of a report or bitstream is not proof that it corresponds to the currently loaded board image. Each report/bitstream must be tied to a revision, part, tool version and hash.

## 4. Experiment archive discovery

The dashboard's experiment data was not found under the FPGA project root. A broader search located experiment JSON files in:
- `~/Documents/chaos-image-encryption-research/fpga-research-studio-dev/experiments/`
- `~/Documents/chaos-image-encryption-research/P5_Project_Evidence/05_Website_Demonstration/live_runs/`
- Several UI-fix copies and an `archive_before_fresh_start` directory.

The canonical source must be selected before importing records. Do not combine duplicated UI-fix copies or archived backups as independent experiments. Pair manifests and their linked software/FPGA experiment folders must remain associated.

The same search found software analysis outputs under `python/reports/` and `reports/`, including:
- cipher evaluation and cipher comparison
- differential batch and differential comparison
- bidirectional validation
- key sensitivity and permutation key sensitivity
- finite-precision analysis
- warm-up sensitivity
- five-image validation
- diffusion direction comparison

These files need schema, provenance, algorithm revision, image identity and test-protocol review before publication.

## 5. V6 routed implementation metrics (from supplied Vivado reports)

Report identity:
- Design: `zybo_chaos_demo_top_v6`
- Device: `xc7z010clg400-1` (7z010-clg400)
- Tool: Vivado 2026.1, build 6511674
- Report date: 2026-11-13
- Design state: Routed

| Metric | Reported value |
|---|---:|
| Clock period | 8.000 ns |
| Clock frequency | 125.000 MHz |
| WNS (setup) | +0.663 ns |
| TNS | 0.000 ns |
| Setup failing endpoints | 0 / 4,143 |
| WHS (hold) | +0.028 ns |
| THS | 0.000 ns |
| Hold failing endpoints | 0 / 4,143 |
| Pulse-width slack | +3.500 ns |
| Slice LUTs | 1,341 / 17,600 (7.62%) |
| Slice registers | 1,149 / 35,200 (3.26%) |
| Block RAM tiles | 48 / 60 (80.00%) |
| DSP48E1 | 6 / 80 (7.50%) |
| Bonded IOB | 6 / 100 (6.00%) |
| BUFGCTRL | 1 / 32 (3.13%) |

Timing interpretation:
- The report states that all user-specified timing constraints are met for the routed design.
- The worst setup path is from the diffusion engine key BRAM output to `calculated_value_reg[3]`, with 0.663 ns positive slack and 7.276 ns data-path delay.
- The worst hold slack is only +0.028 ns. It is passing in this report, but has little margin.
- The check_timing section flags one input port without an input delay and four output ports without output delays (HIGH). Therefore, do not describe this as complete external-I/O timing sign-off. Review and add appropriate I/O constraints for the actual board interfaces.
- BRAM use is 80%, the main reported resource pressure. LUT, register and DSP use are comparatively low.

V6 bitstream SHA256 (from the supplied manifest):
`b6f29c4b2c45f8830e6d0e394caea7b9a83855adfd1bef4f80768fefefdf57dc`

Other hashes in the same manifest:
- Programming log: `f466aeaf18c47280f414f0fcd83975b3b2fee2afc29015d6d5c092eef16566d3`
- Routed checkpoint: `d434213025724bd97f9ae381d584d20b35c770d4c7ac14f862e38058dee384eb`
- V6 BRAM test log: `eacef4402d8b5c4a0c565123f4e6f23e23b6dd5d858528d56aaf60321a885370`

These hashes identify the files in the supplied manifest; they do not prove that this exact bitstream is currently loaded on the physical board.

## 6. Recommended evidence import policy

1. Keep source snapshots under versioned directories such as `rtl/archive/v6/` and `rtl/v7/`.
2. Import text logs and reports after checking they contain no local secrets, private paths that should be redacted, or licensed content.
3. Avoid committing generated `.vvp`, `.dcp`, `.bit`, `.wdb`, cache and temporary build artifacts by default. Publish hashes and reproducible build instructions; selectively release binaries only when justified.
4. Store raw experiment JSON only after selecting one canonical archive and removing secrets or machine-specific information.
5. Label all evidence as software, RTL simulation, synthesis, implementation, or physical-board measurement.
6. Do not call an experiment a physical FPGA result unless the transaction log establishes the board, bitstream identity, host transfer, operation, output, and successful recovery.

## 7. Next inspection required

- Inspect V6 programming log and confirm which exact bitstream it programmed.
- Inspect V7 development logs and current V7 RTL/testbench files.
- Inspect the paired experiment JSON manifests and linked experiment folders to determine whether the archived dashboard runs represent software-generated records, simulated records, or physical-board transactions.
- Review missing input/output delay constraints and hold margin before treating V6 as fully timing signed off.
- Re-run selected simulations from a clean checkout and preserve tool commands and raw output.
