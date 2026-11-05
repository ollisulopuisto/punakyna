# Bolt's Journal - Critical Learnings

## 2026-11-05 - Avoid morphological analysis on non-target tokens in narrow grammar rules
**Learning:** In Punakyna, `check_olla_agreement` targets copula agreement with the 3rd person present indicative forms of "olla" (`on` / `ovat`). However, the rule was querying `voikko.analyze()` across C-FFI for *every* adjacent token pair in every sentence. Because `libvoikko.analyze` is relatively expensive and most words are not "on" or "ovat", this accounted for over 84% of all rule-level analysis calls. Fast filtering with an exact set check (`cur.lower not in {'on', 'ovat'}`) before any C-FFI morphological calls cut standalone `check_olla_agreement` latency by ~79.4% (from 0.785s to 0.162s for 5400 checks) with zero behavioral impact.
**Action:** Before invoking expensive morphological analysis (`voikko.analyze`) in grammar rule loops, check whether the target grammatical category is restricted to a small, finite set of surface forms (e.g. specific auxiliaries or copulas) and fast-path/early-exit on string matching.

## 2026-11-03 - Dynamic `type()` generation inside token loops
**Learning:** Creating dynamic types via `type('T', (), {...})()` inside a hot per-sentence token loop incurs massive overhead due to repeated class creation, dictionary allocations, and type construction in Python. In Punakyna, replacing this with a dedicated slotted class (`_PipelineToken` with `__slots__`) dropped long paragraph checking times by ~58% (from ~0.675s down to ~0.278s for 20 runs) and reduced smoke test runtime by ~29%.
**Action:** Always define slotted classes or dataclasses at module level for per-token or per-element processing in pipelines instead of inline anonymous type factories.
