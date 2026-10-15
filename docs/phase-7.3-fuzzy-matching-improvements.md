# Phase 7.3: Fuzzy Matching Improvements

## Objective

Improve fuzzy entity matching for Unicode data, missing values, and multi-field confidence scoring without changing the existing matcher API.

## Normalization and similarity

- Applies Unicode compatibility and canonical normalization.
- Uses case-insensitive `casefold()` comparison.
- Collapses repeated whitespace, including Unicode whitespace.
- Preserves numeric values and meaningful business text.
- Treats Python `None`, Python and NumPy floating-point NaN, pandas `pd.NA`, pandas `pd.NaT`, NumPy `datetime64("NaT")`, and established standalone missing tokens as missing.
- Keeps missing values as non-comparable at the matching boundary, so two missing identifiers cannot create a candidate, exact match, or fuzzy entity match.
- Returns exact normalized matches as `1.0`, missing comparisons as `0.0`, and keeps all scores finite and within `[0.0, 1.0]`.

## Combined scoring

Fields missing on either side are excluded from the comparable score. Populated fields remain comparable even when their similarity is `0.0`, so genuine conflicts cannot be silently discarded. Records with no comparable fields receive a zero score.

Existing thresholds, ambiguity handling, target uniqueness, and `EntityMatch` responses remain compatible with the prior matching API.

## Testing

Coverage includes Unicode normalization, whitespace, Python/pandas/NumPy missing values, numeric values, candidate exclusion, exact-key rejection, exact and partial matches, conflicting fields, zero-score conflicts, threshold decisions, ambiguity, target uniqueness, reconciliation workflow protection, and bounded confidence.

The complete backend regression suite passes with 366 tests and one pre-existing Starlette/httpx deprecation warning.

## Scope boundaries

This phase improves the existing fuzzy similarity and aggregation behavior. It does not change matching policy thresholds, introduce new matching dependencies, redesign candidate generation, or change persistence workflows. Reconciliation continues to treat two missing compared field values as equal when records have already been matched; missing matching identifiers cannot establish that match.