# FPGA V7 status

## Target
- Board: Digilent Zybo Z7-10
- Device: XC7Z010CLG400-1
- Vivado: 2026.1 (reported environment)
- Design: Processing System 7, AXI DMA, AXI-stream chaos adapter.

## Verified from project inspection / logs
- V7 block design contains AXI DMA and custom `chaos_v7_axis_adapter`.
- Adapter is an AXI4-Stream endpoint, not a UART parser.
- Adapter protocol: one 32-bit header, then 4,096 32-bit image words for 128×128 8-bit grayscale. Header bit 0 selects decrypt mode (0 encrypt, 1 decrypt); final data word asserts TLAST.
- Self-checking testbench `tb_chaos_v7_axis_adapter.v` exists; reported tests cover encrypt/decrypt framing, output backpressure, TKEEP/TLAST, output count, and recovered image.
- FPGA observed DONE high and PLL lock asserted in Hardware Manager. This proves configuration status only, not which bitstream was loaded or that encryption works physically.
- Multiple XSA exports exist in V7 project directories.

## Not yet verified
- Matching ARM application source and ELF for the current V7 XSA.
- UART-to-DMA firmware implementing the host protocol.
- Exact correspondence between Python host script and V7 FPGA.
- End-to-end on-board image encrypt/decrypt round trip.
- Exact bitstream loaded on board.

## Protocol mismatch
The existing host script `fpga_link.py` uses byte serial framing: `CHAO`, operation byte, 16,384 image bytes, expected `RDY!` / `DONE` markers. V7 adapter expects AXI4-Stream words and does not parse those serial markers. Do not run host upload against V7 until matching Zynq PS firmware exists and is loaded.

## Integration checklist
- [ ] Select authoritative V7 project and XSA.
- [ ] Record XSA and bitstream hashes.
- [ ] Confirm AXI DMA base address, MM2S/S2MM settings, interrupt/polling mode, memory map.
- [ ] Implement Zynq PS UART command parser.
- [ ] Receive exactly 16,384 bytes.
- [ ] Submit header + image through MM2S.
- [ ] Receive adapter output through S2MM.
- [ ] Return host-compatible RDY!/DONE and output bytes.
- [ ] Demonstrate physical Zybo encrypt/decrypt round trip.
- [ ] Save serial logs, input/output hashes, and setup photos/video.
