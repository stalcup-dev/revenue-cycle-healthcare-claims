# Public Release Policy

## Public (safe to publish)
- docs/story/* (story pages)
- docs/*.md (memos, definitions, architecture)
- docs/images/* (rendered visuals)
- docs/fixtures/* (small, synthetic marts exports used for OFFLINE runs)

## Private (do not publish)
- Any credentials (.env, service accounts, keys)
- Raw extracts beyond synthetic fixtures
- Full dbt project internals if treated as proprietary (macros, models, seeds, snapshots)
