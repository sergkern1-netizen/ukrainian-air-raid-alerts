# Chapter review log

Each chapter goes through three checks before it is committed. This log records what was checked
and by whom. It does not replace the chapter's own "What this chapter cannot tell you" section.

Checks:
1. **Writer** drafts the chapter from numbers that a script has already produced.
2. **Skeptic** checks every number against the script's output and against fresh computation from the
   raw files, and checks overstatement and safety wording (see `docs/SAFETY.md`).
3. **Reader** checks plain-language wording as an ordinary reader would read it.
4. Corrections from each check are applied, and the chapter is committed with its script and figures.

| Chapter | Skeptic pass | Reader pass | Main corrections made | Commit |
|---|---|---|---|---|
| 1 Timing and rhythms | Self-checked against script output; no separate Skeptic pass | Self-checked | Rounding of one count (99.6%) | a70313b |
| 2 Where sirens sound | Self-checked against script output; no separate Skeptic pass | Self-checked | Median rounding; softened a reporting claim | d9df2f6 |
| 3 Waves and clusters | Self-checked; four statements corrected (48% under one hour; 2026 pace; 23-oblast threshold; four-hour share) | Self-checked | As listed | 06d0ebc, e3f9c0c |
| 4 Feed reliability | Self-checked; pre-break figure corrected to 70.0%; "break is a step" framing corrected | Self-checked | As listed | 08ec40a |
| 5 Long alerts | Skeptic pass (sonnet): must-fix on the official-feed level statement; wave wording; end-time test wording | Reader pass (haiku): definitions; "recording error" defined | Applied; see commit | caf5693 |
| 6 Granularity and official feed | Skeptic pass (sonnet): "four months" error corrected to the January 2025 first step; wording on Kyiv City rows | Reader pass (haiku): defined terms; reframed the opening | Applied | fd8877b |
| 7 Provenance and quality | Skeptic pass (sonnet): Luhanska volunteer count added (3 rows); durations stated as raw rows; UTC-year labels | Reader pass (haiku): defined terms; "error-free" wording removed; invented example removed | Applied | e9bb742 |
| 8 Reporting patterns | Skeptic pass (sonnet): "minute" corrected to "second" throughout; batching renamed "shared starts" in prose | Reader pass (haiku): plain-language fixes (16) | Applied; script labels relabelled | 18e6452 |

Notes:
- The "Self-checked" entries are checks done by the author against the script's output. They are not
  independent. Chapters 1 to 4 would benefit from a separate Skeptic pass before any public release.
- Corrections to earlier analysis notes (for example, the "same minute" wording in
  `docs/analysis/kirovohrad_poltava_gap.md` and `scripts/pair_gap_investigation.py`) are listed in
  `docs/PROJECT_SUMMARY.md` and are not yet fixed.
