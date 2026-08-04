#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from markdown import markdown
from weasyprint import HTML

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


def build_pdf(markdown_path: Path, output_pdf: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    markdown_path = markdown_path.resolve()
    output_pdf = output_pdf.resolve()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    text = markdown_path.read_text(encoding="utf-8")
    html = markdown(text, extensions=["tables", "fenced_code", "attr_list"])
    html = f"""<!doctype html>
<html lang='en'>
  <head>
    <meta charset='utf-8' />
    <style>
      body {{ font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.35; color: #111; margin: 36px; }}
      h1, h2, h3 {{ color: #0f3d5e; }}
      h1 {{ font-size: 22pt; margin-top: 0; }}
      h2 {{ font-size: 16pt; margin-top: 24px; }}
      h3 {{ font-size: 13pt; margin-top: 18px; }}
      table {{ border-collapse: collapse; width: 100%; margin: 10px 0 16px; font-size: 10pt; }}
      th, td {{ border: 1px solid #c6c6c6; padding: 6px 8px; text-align: left; vertical-align: top; }}
      th {{ background-color: #f2f7fb; }}
      img {{ max-width: 100%; height: auto; display: block; margin: 12px 0 6px; }}
      .source {{ font-size: 9pt; color: #666; margin-top: 4px; }}
      ul {{ padding-left: 18px; }}
      blockquote {{ border-left: 4px solid #d7e7f3; margin: 10px 0; padding-left: 12px; color: #444; }}
    </style>
  </head>
  <body>{html}</body>
</html>"""

    html_path = output_pdf.with_suffix('.html')
    html_path.write_text(html, encoding='utf-8')
    HTML(string=html, base_url=str(markdown_path.parent)).write_pdf(output_pdf)

    if PdfReader is not None:
        reader = PdfReader(str(output_pdf))
        pages = len(reader.pages)
    else:
        pages = None

    return output_pdf, pages


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a PDF report from a markdown file.')
    parser.add_argument('markdown', nargs='?', default='reports/eda_report.md')
    args = parser.parse_args()

    markdown_path = Path(args.markdown)
    if not markdown_path.is_absolute():
        markdown_path = Path.cwd() / markdown_path
    if not markdown_path.exists():
        raise FileNotFoundError(f'Markdown file not found: {markdown_path}')

    output_dir = markdown_path.parent / 'build'
    output_pdf = output_dir / f'{markdown_path.stem}.pdf'
    output_pdf, pages = build_pdf(markdown_path, output_pdf)
    print(f'Wrote {output_pdf}')
    if pages is not None:
        print(f'Page count: {pages}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
