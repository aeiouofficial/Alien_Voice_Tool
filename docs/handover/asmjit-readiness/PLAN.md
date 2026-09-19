# AsmJit Readiness Plan — Alien_Voice_Tool

Status: PREPARED_ONLY
Branch: `prep/asmjit-readiness-2026-09-19`
Relevance: LOW / CONDITIONAL

Current stack already uses NumPy/SciPy-style vectorized processing. AsmJit is not a first-line optimization.

## Order of investigation
1. Profile end-to-end processing.
2. Remove Python-level loops and unnecessary copies.
3. Validate NumPy/SciPy vectorization.
4. Evaluate Numba or a small static native extension if needed.
5. Consider AsmJit only for runtime-generated DSP chains with proven repeated execution.

## Success requirement
AsmJit must beat simpler alternatives on wall time while preserving audio output tolerances and packaging reliability.

No code/dependency changes or merge are authorized on this prepared branch.
