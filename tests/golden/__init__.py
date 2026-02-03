"""Golden tests for determinism validation.

Golden tests ensure that the pipeline produces identical outputs
for identical inputs across runs. This validates:

1. Passage segmentation is deterministic (same char offsets)
2. Entity resolution produces stable IDs
3. Obligation extraction is reproducible
4. Evidence anchor positions are consistent

Usage:
    pytest tests/golden -v

To update golden files after intentional changes:
    pytest tests/golden --update-golden
"""
