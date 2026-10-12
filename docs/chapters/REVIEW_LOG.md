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
| 1 Timing and rhythms | Skeptic pass (sonnet): night-hour arithmetic (9 hours, 37.5% expected) corrected; planning advice removed; incomplete last night excluded; 30-minute spike disclosed | Not yet run | Applied; see commit | a70313b, then correction commit |
| 2 Where sirens sound | Skeptic pass (sonnet): "a fifth" corrected to 23%; "quiet" wording removed; western list (eight oblasts); Chapter 8 cross-references; Luhanska and total-row wording | Not yet run | Applied | d9df2f6, 771515a |
| 3 Waves and clusters | Self-checked; then Skeptic pass (sonnet): "all widest waves in 2022" was false (194 waves touch all 24 names in every year); 1.5% share; "probably an artefact" softened; 2026 pace reworded | Not yet run | Applied | 06d0ebc, e3f9c0c, 771515a |
| 4 Feed reliability | Self-checked; then Skeptic pass (sonnet): Donetska 74% to 25%; recall direction; decline described as two steps, not a steady fall; matched-share and comparability caveats | Not yet run | Applied | 08ec40a, correction commit |
| 5 Long alerts | Skeptic pass (sonnet): must-fix on the official-feed level statement; wave wording; end-time test wording | Reader pass (haiku): definitions; "recording error" defined | Applied; see commit | caf5693 |
| 6 Granularity and official feed | Skeptic pass (sonnet): "four months" error corrected to the January 2025 first step; wording on Kyiv City rows | Reader pass (haiku): defined terms; reframed the opening | Applied | fd8877b |
| 7 Provenance and quality | Skeptic pass (sonnet): Luhanska volunteer count added (3 rows); durations stated as raw rows; UTC-year labels | Reader pass (haiku): defined terms; "error-free" wording removed; invented example removed | Applied | e9bb742 |
| 8 Reporting patterns | Skeptic pass (sonnet): "minute" corrected to "second" throughout; batching renamed "shared starts" in prose | Reader pass (haiku): plain-language fixes (16) | Applied; script labels relabelled | 18e6452 |

Notes:
- Chapters 1 to 4 received a Skeptic pass after the first draft and corrections were applied. A second
  Skeptic pass on the corrected text has not been run, and no Reader pass has been run for chapters 1 to 4.
- Corrections to earlier analysis notes (for example, the "same minute" wording in
  `docs/analysis/kirovohrad_poltava_gap.md` and `scripts/pair_gap_investigation.py`) are listed in
  `docs/PROJECT_SUMMARY.md` and are not yet fixed.
