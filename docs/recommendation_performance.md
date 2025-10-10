# Recommendation Engine Performance Notes

## Key Bottlenecks Identified
- **Full table scans for every request.** The recommendation flow eagerly loaded the entire `onsens` table on each call, even when the caller only needed a single distance bucket. This meant parsing usage hours, closed days, and calculating distances for hundreds of rows before any filtering happened.
- **Wide ORM payloads.** Each scan pulled every column for `Onsen`, including large text fields that are irrelevant for filtering, inflating query time and memory pressure.
- **Unbounded distance filtering.** Once the Python-side filters ran, the engine still computed distances for every candidate in the selected bucket and sorted the full list, even if the CLI only needed a handful of results.

## Optimizations Implemented
- **Spatially scoped queries.** The engine now derives an approximate search radius from the active distance bucket and uses it to constrain the ORM query by latitude/longitude, dramatically shrinking the working set before any Python logic executes. When milestones are unavailable, it falls back to the static distance defaults. The "far" bucket intentionally remains unconstrained so explorers can still reach every listing.
- **Column projection.** Recommendation queries are executed with `load_only` so we only hydrate the fields required for availability checks and CLI output.
- **Limited distance sorting.** `filter_onsens_by_distance` now accepts an optional `limit` and keeps a small heap of the closest onsens instead of sorting the entire list, which cuts both CPU time and intermediate allocations when the caller requests just a few results.

## Follow-up Opportunities
- Persist a denormalized distance table keyed by location to avoid recalculating Haversine distances for common searches.
- Precompute parsed usage hours and closed-day schedules during ingestion so requests do not reparse the same strings.
- Surface query planning metrics in telemetry so we can spot regressions when the dataset grows.
