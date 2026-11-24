# Chaos Image Encryption Research

This directory contains experimental implementations, validation scripts,
and evaluation results for chaos-based image encryption.

## Contents

- `chaos_cipher/`: cipher implementations and experimental analysis scripts
- `tests/`: tests for the research implementation
- `reports/`: generated metrics, CSV/JSON results, and plots

## Running tests

From this directory:

    python3 -m unittest discover -s tests -v

Run individual experiments as Python modules from this directory, for example:

    python3 -m chaos_cipher.validate_bidirectional
    python3 -m chaos_cipher.test_key_sensitivity

## Research limitations

These implementations are experimental and are not suitable for protecting
sensitive data without further cryptographic analysis. Statistical image
metrics alone do not establish cryptographic security. Fixed-point
quantization, key sensitivity, finite-precision behavior, and resistance
to relevant attacks require additional evaluation.
