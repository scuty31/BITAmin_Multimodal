# EDA Report for the Audio and Fusion Tracks

This note summarizes the dataset-level evidence that matters for the audio and fusion teams. The figures below are reused from the existing analysis outputs in [reports/figures](figures) rather than regenerated here.

## Summary

- The current manifest is a four-way category split with 10,835 FakeVideo-FakeAudio rows, 9,709 FakeVideo-RealAudio rows, 500 RealVideo-FakeAudio rows, and 500 RealVideo-RealAudio rows; this is the canonical row count in [reports/eda/index.csv](eda/index.csv).
- The label rule is simple and strict: all 20,544 fake rows carry label 1 and all 1,000 real rows carry label 0, so the branch is strongly class-imbalanced and should be handled with class weighting or balanced sampling; source [reports/eda/index.csv](eda/index.csv).
- Unknown is unresolved, not a manipulation label: 4,315 rows have method `unknown`, and those rows span all 500 identities; source [reports/eda/method_validation_detailed.txt](eda/method_validation_detailed.txt) and [notebooks/method_schema.ipynb](../notebooks/method_schema.ipynb).
- The metadata shortcut is real but not a compression artifact: the earlier GroupKFold analysis reported AUROC 0.7025 with ±0.0085, and the strongest signal was clip duration rather than bit-rate or bpp; source [AGENTS.md](../AGENTS.md).
- The method schema should be split across video and audio axes: the current resolved manifest contains 1,763 multi-token rows and 4,315 unresolved rows, so the legacy single `method` column is not sufficient for downstream loaders; source [reports/eda/method_validation_detailed.txt](eda/method_validation_detailed.txt) and [reports/eda/method_resolved.csv](eda/method_resolved.csv).
- For a first training slice, the unknown-excluded cap-500 option is the smallest policy that still preserves the real set and the faceswap distribution while avoiding the unresolved pool; source [reports/eda/method_sampling_comparison.csv](eda/method_sampling_comparison.csv).

## Decision table

| Parameter | Decision | Evidence | Reference |
| --- | --- | --- | --- |
| Label handling | Keep a binary label and do not report bare accuracy; use AUROC/AP/EER/TPR@FPR instead | 20,544 fake rows and 1,000 real rows in the index | [reports/eda/index.csv](eda/index.csv) |
| Identity split | Split by identity, not by video, for all train/test folds | The dataset contains 500 identities and the analysis uses identity-level coverage | [reports/eda/index.csv](eda/index.csv), [notebooks/method_schema.ipynb](../notebooks/method_schema.ipynb) |
| Unknown handling | Treat `method = unknown` as unresolved and do not promote it to a manipulation class | 4,315 unknown rows; no evidence that they form a clean FSGAN subset | [reports/eda/method_validation_detailed.txt](eda/method_validation_detailed.txt) |
| Method schema | Add explicit columns for video swap, video lipsync, and audio method; keep the legacy `method` column as raw input | The resolved manifest contains `video_swap`, `video_lipsync`, `audio_method`, `method_source`, and `method_confidence` | [reports/eda/method_resolved.csv](eda/method_resolved.csv) |
| Sampling policy | Start with unknown-excluded cap 500 for the first pilot run | Unknown-excluded cap 500 gives 1,379 videos and 44,128 frames | [reports/eda/method_sampling_comparison.csv](eda/method_sampling_comparison.csv) |

## Dataset composition

The manifest in [reports/eda/index.csv](eda/index.csv) contains 21,544 rows and 13 columns. The four categories are shown below.

| Category | Rows | Share of manifest | Label rule |
| --- | ---: | ---: | --- |
| FakeVideo-FakeAudio | 10,835 | 50.3% | label 1 |
| FakeVideo-RealAudio | 9,709 | 45.1% | label 1 |
| RealVideo-FakeAudio | 500 | 2.3% | label 0 |
| RealVideo-RealAudio | 500 | 2.3% | label 0 |

The label rule is therefore straightforward: fake examples are all label 1 and real examples are all label 0. In practice, the real set is only 1,000 rows, so the video branch should be treated as heavily imbalanced and should use balanced sampling or class weights.

### Identity and demographics

The index contains 500 identities. The raw row distribution by race and gender is not perfectly balanced, but it spans five race groups and both genders:

| Race | Rows | Gender split (men/women) |
| --- | ---: | --- |
| African | 4,089 | 2,227 / 1,862 |
| Asian (East) | 3,484 | 1,711 / 1,773 |
| Asian (South) | 4,414 | 2,195 / 2,219 |
| Caucasian (American) | 4,864 | 2,531 / 2,333 |
| Caucasian (European) | 4,693 | 2,429 / 2,264 |

The demographic balance should be checked with grouped splits, because the identity column is the correct grouping key for avoiding leakage.

## Metadata shortcut: why the shortcut works

The dataset-level shortcut is not a mystery anymore. The project-wide finding in [AGENTS.md](../AGENTS.md) is that container metadata alone predicts the label at AUROC 0.7025 with ±0.0085 under a 5-fold GroupKFold split, and the strongest signal is clip duration rather than compression. In that analysis, duration, number of frames, and size bytes carry the signal, while bit-rate and bpp have negative permutation importance. The practical implication is that the model should not rely on raw metadata as a proxy for content, and fixed-length clip sampling is a better control than re-encoding.

![Unknown rows per identity](figures/unknown_identity_distribution.png)

Figure 1. The unknown-row count per identity is spread across the full identity set; the histogram shows that the unresolved pool is not a narrow subset.

## Method label problem and schema redesign

The current single-column `method` field is too weak for downstream training because it mixes unresolved cases, multi-token manipulations, and legacy labels. The EDA found 1,763 rows that are multi-token cases and 4,315 rows whose method is `unknown`.

| Issue | Count | Interpretation |
| --- | ---: | --- |
| `method = unknown` | 4,315 | Unresolved; do not treat as a manipulation technique |
| Multi-token video manipulations | 1,763 | Evidence of combined face-swap and lip-sync signals |
| Pure faceswap rows in FakeVideo-RealAudio | 379 | Explicit faceswap-only subset |

The resolved schema in [reports/eda/method_resolved.csv](eda/method_resolved.csv) is a contract for loaders. The columns and allowed values are:

| Column | Allowed values | Purpose |
| --- | --- | --- |
| `video_swap` | `none`, `faceswap`, `unresolved` | Distinguishes swap-like video edits from no swap |
| `video_lipsync` | `none`, `wav2lip` | Distinguishes lip-sync edits from no lip-sync |
| `audio_method` | `none`, `rtvc` | Captures the audio-side edit family |
| `method_source` | `filename`, `inferred`, `metadata` | Indicates how the label was derived |
| `method_confidence` | `high`, `low` | Indicates confidence in the resolution |

The legacy `method` column should remain in the manifest as the raw source field, but downstream training and evaluation should use the new columns. This is a breaking change for loaders, so the contract should be versioned and announced explicitly.

![Method combination counts](figures/method_combo_counts.png)

Figure 2. The most common combination is `none / wav2lip / rtvc`, followed by `none / wav2lip / none`; the unresolved bucket is large enough to affect any naive sampling plan.

## Sampling plan

The sampling options are compared in [reports/eda/method_sampling_comparison.csv](eda/method_sampling_comparison.csv). All candidates use the fixed real set of 500 rows; the difference comes from whether the unresolved pool is included.

| Variant | Cap | Total videos | Total frames | Expected GB | Real/fake ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unknown included | 500 | 1,879 | 60,128 | 3.01 | 0.36 |
| Unknown included | 1,000 | 2,879 | 92,128 | 4.61 | 0.21 |
| Unknown included | 2,000 | 4,879 | 156,128 | 7.81 | 0.11 |
| Unknown excluded | 500 | 1,379 | 44,128 | 2.21 | 0.57 |
| Unknown excluded | 1,000 | 1,879 | 60,128 | 3.01 | 0.36 |
| Unknown excluded | 2,000 | 2,879 | 92,128 | 4.61 | 0.21 |

Recommendation: use the unknown-excluded cap-500 option for the first pilot training slice. It avoids the unresolved bucket entirely, keeps the real/fake ratio high enough to be stable, and still preserves a manageable frame budget. If the team later decides to learn from the unresolved pool, it should be treated as a separate label state rather than folded into the known manipulations.

## Open issues

The current EDA leaves three things unresolved:

1. The provenance of the 4,315 unknown rows needs a source-level audit. The current evidence says they are unresolved, but the team still needs a clear recovery path for them.
2. The new method-schema columns need to be wired into the training loaders and the manifest reader so that downstream code stops relying on the legacy single-column field.
3. The sampling decision should be finalized only after the team agrees whether unresolved rows are part of the training target or a separate validation-only bucket.
