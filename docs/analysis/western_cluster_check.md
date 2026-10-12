# Western co-occurrence cluster: volunteer vs official feed

Overlap window: volunteer and official alerts up to 2026-09-07. Gap 30 min.
Jaccard = shared waves / waves either oblast is in. Pairs with fewer than 20 shared waves in a feed are not scored.

## Top 15 volunteer pairs, with the official feed's value for each pair

| Oblast A | Oblast B | Volunteer Jaccard | Official Jaccard | Western pair |
|---|---|---:|---:|---|
| Ivano-Frankivska oblast | Zakarpatska oblast | 0.789 | 0.851 | yes |
| Chernivetska oblast | Zakarpatska oblast | 0.772 | 0.822 | yes |
| Ivano-Frankivska oblast | Ternopilska oblast | 0.744 | 0.815 | yes |
| Chernivetska oblast | Ivano-Frankivska oblast | 0.722 | 0.806 | yes |
| Ternopilska oblast | Zakarpatska oblast | 0.694 | 0.745 | yes |
| Chernivetska oblast | Ternopilska oblast | 0.684 | 0.742 | yes |
| Rivnenska oblast | Ternopilska oblast | 0.672 | 0.721 | yes |
| Ivano-Frankivska oblast | Rivnenska oblast | 0.608 | 0.682 | yes |
| Khmelnytska oblast | Ternopilska oblast | 0.603 | 0.593 | yes |
| Rivnenska oblast | Zakarpatska oblast | 0.59 | 0.671 | yes |
| Khmelnytska oblast | Rivnenska oblast | 0.588 | 0.615 | yes |
| Ivano-Frankivska oblast | Khmelnytska oblast | 0.569 | 0.57 | yes |
| Chernivetska oblast | Rivnenska oblast | 0.569 | 0.641 | yes |
| Chernivetska oblast | Khmelnytska oblast | 0.568 | 0.607 | yes |
| Kirovohradska oblast | Poltavska oblast | 0.552 | 0.361 | no |

## Western pairs in each feed (mean Jaccard)

- Volunteer: 28 western pairs scored, mean Jaccard 0.546.
- Official: 28 western pairs scored, mean Jaccard 0.718.

## Result

The western pairs score as high or higher in the official feed. The cluster is therefore
not only a volunteer-channel artefact: the official feed shows the same oblasts alerting together.
The exception is Kirovohradska–Poltavska, which scores much higher in the volunteer feed. That pair
is a candidate for reporting behaviour.

Limits: the overlap window ends 2026-09-07, and the official feed is oblast-level only in the
rows used here. Jaccard describes co-occurrence, not cause.
