# Phase 7.2: Deterministic Exact Entity Matching

## Objective

Add a dedicated deterministic exact-matching service using normalized composite keys without changing the existing fuzzy matcher.

## Matching behavior

- Requires one or more valid, unique matching fields.
- Normalizes configured values using the existing similarity utility.
- Matches records only when all configured key fields are present and equal after normalization.
- Marks incomplete source keys as no_match with reason missing_matching_value.
- Marks complete source keys without a corresponding target as no_match with reason no_exact_match.
- Flags duplicate source or target keys for review instead of choosing arbitrarily.
- Prevents a target record from being assigned more than once.
- Returns the existing EntityMatch model with method exact, confidence, field scores, status, and reason.

## API

```python
from app.services.matching.exact_matcher import match_entities_exact

results = match_entities_exact(
    source_records,
    target_records,
    fields=["customer_id", "email"],
)
```

## Validation

Focused tests cover normalized equality, composite keys, missing values, duplicates, one-to-one assignment, empty inputs, invalid fields, and numeric/string normalization.

The full regression suite must pass before this checkpoint is committed.
