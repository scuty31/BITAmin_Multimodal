# AGENTS.md

Project rules for coding agents. Read this before any task in this repo.

## Project

Multimodal deepfake detection on **FakeAVCeleb v1.2**. Three branches feed a
fusion head: video (GenD / CLIP ViT-L LN-tuning), audio (AASIST), and
audio-visual sync (DiMoDif / AVH-Align). This repo currently covers the data
layer and the video branch.

Split by modality: teammates own audio, video, and fusion separately. The
manifest is the integration point — changing its schema breaks other people's
data loaders, so treat schema changes as breaking changes and say so explicitly.

## Language

**All generated content is in English.** Code, comments, docstrings, commit
messages, notebook markdown cells, figure titles, axis labels, legends, table
headers, and report prose. No exceptions — mixed-language figures are the main
source of font-rendering failures on this server.

## Layout

```
configs/         params.yaml, preprocess.yaml — all tunables live here
src/             importable package
  report/        style.py (shared matplotlib config)
scripts/         CLI entry points
notebooks/       exploratory analysis, committed with outputs cleared
reports/
  figures/       .png + .svg written by src.report.style.save()
  build/         generated .html / .pdf — gitignored
data/            DVC-tracked, never committed to git
```

## Environment

- Python 3.12, conda env. Prefer `uv pip install` over `pip install`.
- No sudo. If a task needs a system package, stop and report it rather than
  attempting `apt`.
- Outbound HTTPS may be firewalled. If a download fails, report it — do not
  silently fall back to a stub or synthetic data.
- Long jobs run under tmux. Anything expected to exceed ~10 minutes must print
  progress and support resumption via a cache or `--skip-processed` flag.

## Data rules

These exist because violations are expensive to discover late.

1. **Split by identity, never by video.** The same person appearing in both
   train and test inflates AUROC. Use `GroupKFold` / grouped splits on the
   `identity` column.
2. **Real videos come only from `RealVideo-RealAudio`.** `RealVideo-FakeAudio`
   has a byte-identical video track; using both duplicates frames.
3. **Class imbalance is ~1:41** (500 real / 20,544 fake in the video branch).
   Always apply balanced sampling or class weights, and never report bare
   accuracy — use AUROC, AP, EER, and TPR@FPR.
4. **Flag failures, do not drop them.** No face detected, silent audio,
   multiple faces: add a boolean column. Silent row removal makes counts
   unauditable.
5. **Never write to `data/`** from a notebook. Derived artifacts go to
   `reports/` or a DVC-tracked stage output.

## Known analysis findings

Carry these forward; do not re-derive or contradict them without evidence.

- Container metadata alone predicts the label at **AUROC 0.7025** (5-fold
  GroupKFold, ±0.0085). The signal is **clip duration**, not compression:
  `duration` / `nb_frames` / `size_bytes` carry it, while `bit_rate` and `bpp`
  have *negative* permutation importance. Re-encoding does not fix this;
  fixed-length clip sampling does.
- `method == "unknown"` covers 4,315 fake videos (21%) because `meta_data.csv`
  was not found and path-based fallback parsing ran. Treat `unknown` as
  "unresolved", not as a manipulation technique.
- Source frames are 224x224 for 99.1% of videos; estimated face height is
  ~90px. Saving crops larger than native resolution only upscales.

## Plotting

- `matplotlib` only. No seaborn, no plotly.
- Always start with `from src.report.style import setup, save; setup()`.
- Save via `save(fig, "descriptive_name")` so the report build finds figures.
- One idea per figure. Label axes with units. Annotate the number that matters
  rather than making the reader estimate it from the axis.
- State sample size in the title or caption whenever n varies across panels.

## Notebooks

- Must run top to bottom on a fresh kernel. Test this before declaring done.
- Cache expensive steps to `reports/` and check for the cache on entry, keyed
  on a stable identifier (relative path, not absolute).
- Every section opens with a markdown cell naming the **question** it answers
  and closes with one naming the **decision** it drives. Analysis that decides
  nothing does not belong here.
- Clear outputs before committing (`nbstripout` or `--ClearOutputPreprocessor`).

## Reports

PDF generation goes `ipynb`/`md` → HTML → PDF. **Do not use LaTeX or
`nbconvert --to pdf`** — it pulls in a TeX distribution that is not installed
and cannot be installed without sudo.

PDF converter fallback order: `weasyprint` (pip-installable, no sudo) →
`wkhtmltopdf` → headless `chromium`. Detect what is present at runtime rather
than assuming.

## Verification

A task is not done until it has been run. Before reporting completion:

- Execute the notebook or script end to end and read the actual output.
- Open generated figures and confirm they render — check that text is not
  clipped, axes are not empty, and legends are present.
- Confirm the PDF exists, is non-trivial in size, and report its page count.
- If a number in the output contradicts the "Known analysis findings" above,
  say so explicitly instead of quietly adjusting the analysis to match.

Report what you actually observed. Never describe intended behavior as if it
were verified behavior.
