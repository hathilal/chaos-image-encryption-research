# Chaos-Based Image Encryption Engine — Python Reference

Research-oriented Python reference model for a hardware-oriented chaos-based image encryption project.

## Project status

- **Milestone 1:** Floating-point Lorenz system with explicit midpoint RK2 and tests.
- **Milestone 2:** Signed fixed-point arithmetic and a fixed-point Lorenz/RK2 model with tests. The default format is 32-bit signed with 19 fractional bits; treat this as a candidate to validate, not a final hardware choice.
- **Milestone 3 (baseline implementation):** Pure-Python grayscale byte-image permutation and chained-XOR diffusion, with inverse decryption and round-trip tests.

This is a research baseline, **not a production-secure cipher**. The permutation uses a modulo-based Fisher-Yates index and the diffusion keystream is a simple byte extraction from the fixed-point Lorenz state. These design choices are for reproducible hardware/software experiments, not claims of cryptographic strength. Do not use this code to protect sensitive images. A chaotic trajectory, key sensitivity, or passing statistical tests alone do not establish cryptographic security.

## Requirements

- Python 3.10+
- Current models and tests use only the Python standard library.

## Run the demo

From the repository root:

```bash
cd python
python scripts/run_lorenz_demo.py
```

## Run tests

From the `python/` directory:

```bash
python3 -m unittest discover -s tests -v
```

## Image cipher API

Module: `src/chaos_image_encryption/image_cipher.py`

The API accepts a flat sequence of 8-bit grayscale pixels and explicit width/height. The image length must equal `width * height`.

```python
from chaos_image_encryption.image_cipher import ChaosKey, encrypt_image, decrypt_image

pixels = bytes((i * 17) & 0xFF for i in range(128 * 128))
key = ChaosKey(x=0.1, y=0.2, z=0.3)
cipher = encrypt_image(pixels, 128, 128, key, warmup_steps=1000)
recovered = decrypt_image(cipher, 128, 128, key, warmup_steps=1000)
assert recovered == pixels
```

Encryption and decryption must use identical key, dimensions, warm-up count, step size, and fixed-point format. The implementation first shuffles source-pixel indices with Fisher-Yates, then applies chained XOR diffusion. The inverse operation reconstructs the original pixel order.

Current limitations:
- The code accepts raw pixel bytes; image-file decoding/encoding (for example PNG) is not yet included.
- No claims are made about NIST SP 800-22, NPCR/UACI, correlation, throughput, or FPGA resource use; these must be measured separately.
- The current byte extraction and modulo shuffle are baseline choices to evaluate and potentially replace during the research.

## Floating-point model

The Lorenz equations are

- dx/dt = sigma * (y - x)
- dy/dt = x * (rho - z) - y
- dz/dt = x * y - beta * z

The integrator is the explicit midpoint RK2 method. Parameters and initial conditions are configurable. Defaults are conventional demonstration values, not a claim of optimal cryptographic settings.

## Fixed-point model contract

Module: `src/chaos_image_encryption/fixed_point.py`

- Values are signed two's-complement raw integers; real value = raw / 2**fractional_bits.
- Default format: 32-bit words, 19 fractional bits; nominal range is [-4096, 4096 - 2^-19].
- Float-to-fixed conversion uses round-to-nearest, ties away from zero.
- Multiplication computes a full-width integer product, then uses an arithmetic right shift by the fractional-bit count.
- Intermediate stored results use the selected overflow policy: `raise` (default, to expose range problems) or `wrap` (two's-complement wraparound).
- Right shift of negative values follows Python's arithmetic-shift behavior. The RTL must implement the same semantics, operation order, and intermediate widths for bit-exact agreement.

This is an explicit reference contract, not yet evidence that the format is optimal. Measure state/intermediate ranges and numerical divergence over the intended warm-up and keystream lengths before locking the hardware format.

## Research discipline

- Do not claim that a chaotic trajectory alone provides cryptographic security.
- Keep floating-point and fixed-point models separate.
- Record parameters, time step, initial conditions, format, overflow policy, software version, and experiment seeds for reproducibility.
- Do not report measurements until they have been run and saved.
