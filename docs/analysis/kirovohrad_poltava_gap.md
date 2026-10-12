# Kirovohradska–Poltavska gap: volunteer vs official

The pair's Jaccard is 0.552 in the volunteer feed and 0.361 in the official feed (see
`western_cluster_check.md`). This note checks why.

Overlap window: up to 2026-09-07.

## 1. Timing of the pair

| Feed | Kirovohrad starts | Exact same second as Poltava | Same-second share | Median gap to Poltava (min) | Within 30 min |
|---|---:|---:|---:|---:|---:|
| Volunteer | 6,092 | 304 | 0.05 | 3.9 | 0.65 |
| Official | 3,344 | 21 | 0.006 | 19.1 | 0.543 |

## 2. Is batching general or specific to this pair?

Share of all oblast starts that share an exact second with another oblast: volunteer 0.047, official 0.045.
Batching is about the same across the whole feed. It is not a general volunteer-feed effect.

## 3. Same-second share by period

| Feed | Period | Kirovohrad starts | Same-second share with Poltava |
|---|---|---:|---:|
| Volunteer | before Dec 2025 | 5,029 | 0.058 |
| Volunteer | from Dec 2025 | 1,063 | 0.009 |
| Official | before Dec 2025 | 3,344 | 0.006 |
| Official | from Dec 2025 | 0 | nan |

The official feed has no oblast-level rows after the break in this window, so its post-break
value is not available.

## Reading

- The volunteer feed posts Kirovohrad and Poltava in the same second about eight times more
  often than the official feed does. The gap is specific to this pair.
- That batching was concentrated before December 2025 and fell to under 1% afterwards.
- The most likely reason is that volunteers report the two oblasts in one message. The dataset
  has no message IDs, so this is a hypothesis. Check it with the source posts before stating it.
- Consequence: the pair's pre-break volunteer Jaccard overstates how often the two oblasts were
  affected together. Do not present it as a geographic finding.
