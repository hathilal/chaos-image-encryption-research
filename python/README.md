# Chaos-Based Image Encryption Engine — Python Reference

Research-oriented Python reference model for a hardware-oriented chaos-based image encryption project.

## Project status

**Milestone 1:** Floating-point Lorenz system with midpoint RK2 integration and basic automated tests.

This is a research scaffold, not a secure encryption implementation. The floating-point model is the first reference point. Later milestones will add bit-accurate fixed-point arithmetic, keystream generation, reversible image permutation/diffusion, metrics, and FPGA comparison.

## Requirements

- Python 3.10+
- Milestone 1 uses only the Python standard library.

## Run the demo

From the repository root:

```bash
cd python
python scripts/run_lorenz_demo.py
```

## Run tests

From the `python/` directory:

```bash
python -m unittest discover -s tests -v
```

## Current model

The Lorenz equations are

- dx/dt = sigma * (y - x)
- dy/dt = x * (rho - z) - y
- dz/dt = x * y - beta * z

The integrator is the explicit midpoint RK2 method. Parameters and initial conditions are configurable. Defaults are conventional demonstration values, not a claim of optimal cryptographic settings.

## Research discipline

- Do not claim that a chaotic trajectory alone provides cryptographic security.
- Keep the floating-point model separate from the future fixed-point, bit-accurate model.
- Record parameter values, time step, initial conditions, software version, and experiment seeds for reproducibility.
- Do not report measurements until they have been run and saved.
