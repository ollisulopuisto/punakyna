# Bolt's Journal - Critical Learnings

## 2026-11-03 - Dynamic `type()` generation inside token loops
**Learning:** Creating dynamic types via `type('T', (), {...})()` inside a hot per-sentence token loop incurs massive overhead due to repeated class creation, dictionary allocations, and type construction in Python. In Punakyna, replacing this with a dedicated slotted class (`_PipelineToken` with `__slots__`) dropped long paragraph checking times by ~58% (from ~0.675s down to ~0.278s for 20 runs) and reduced smoke test runtime by ~29%.
**Action:** Always define slotted classes or dataclasses at module level for per-token or per-element processing in pipelines instead of inline anonymous type factories.
