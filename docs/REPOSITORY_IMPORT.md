# Importing the V7 Vivado project

The V7 Vivado project is currently outside this GitHub repository on the developer workstation. The repository does not yet contain the full FPGA source tree.

## Include
- RTL source files and testbenches.
- Vivado project Tcl / reproducible generation scripts.
- Block-design Tcl and metadata needed to recreate Zynq + AXI DMA.
- XDC constraints.
- Hardware revision README.
- XSA/bitstream only when licensing, size, and provenance permit; otherwise publish hashes and reproducible generation steps.

## Exclude
- `.Xil/`, `.cache/`, `.gen/`, `.runs/`, `.sim/`, transient `.hw/`, logs/journals, editor backups, OS files, local absolute paths, and unrelated workspaces.
- Vitis build output, caches, temporary Java workspaces, and unverified ELF.
- Proprietary PDKs, encrypted IP, licensed vendor libraries, credentials and private data.
- Large raw images unless redistribution is permitted.

## Candidate source root
`Chaos_Image_Encryption_FPGA/V7_ILA_Debug`

Before importing, list source files:

```bash
cd /media/hathilal13/ubuntu_data/Vivado_Downloads/Chaos_Image_Encryption_FPGA
find V7_ILA_Debug -maxdepth 3 -type f \
  \( -name '*.v' -o -name '*.sv' -o -name '*.vhd' -o -name '*.xdc' -o -name '*.tcl' \) \
  -not -path '*/.Xil/*' -not -path '*/.cache/*' -not -path '*/.gen/*' \
  -not -path '*/.runs/*' -not -path '*/.sim/*' | sort
```

Create a source-only staging directory and review every file before committing. Do not copy the entire Vivado project folder into Git.
