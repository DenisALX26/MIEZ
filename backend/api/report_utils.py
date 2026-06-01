from pathlib import Path

from django.conf import settings
from django.utils import timezone


def _build_html_with_claude(report, directives='', context_data=''):
    try:
        from anthropic import Anthropic
        client = Anthropic()
        today = timezone.now().strftime('%B %d, %Y')
        directives_line = f'\nSpecial focus / additional instructions: {directives}' if directives else ''
        data_section = (
            f'\n\nReal data from the app — use these exact figures in the report:\n{context_data}'
            if context_data else
            '\n\nNo live data was provided. Generate realistic placeholder figures.'
        )

        prompt = f"""Generate a professional business report as a complete, self-contained HTML document.

Report: {report.name}
Category: {report.category}
Period: {report.period}
Generated: {today}{directives_line}{data_section}

Requirements:
- Return a complete HTML document (<!DOCTYPE html> through </html>), nothing else
- All CSS must be inside a <style> tag in <head> — no external stylesheets
- White background, clean typography, print-friendly layout
- Header section: company name "MIEZ Corp", report title, generated date, category badge
- KPI summary row: 3–4 metric cards derived from the provided data
- One or more detailed data tables populated with the provided data
- A short executive summary paragraph (2–3 sentences) based on the actual data
- All monetary values must be in RON (Romanian Leu) — never use USD, EUR, or $ symbols
- Accent colour #D1353B for headings and badges; table headers #f3f4f6; borders #e5e7eb
- Font: system-ui, -apple-system, sans-serif
- No JavaScript, no external resources, no fixed heights that break printing

Return ONLY the HTML document. No markdown, no code fences, no explanation."""

        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=4096,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return message.content[0].text
    except Exception:
        return _fallback_html(report)


def _fallback_html(report):
    today = timezone.now().strftime('%B %d, %Y')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{report.name}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 48px; color: #111; }}
  h1 {{ color: #D1353B; margin-bottom: 4px; font-size: 24px; }}
  .meta {{ color: #666; font-size: 13px; margin-bottom: 32px; }}
</style>
</head>
<body>
  <h1>{report.name}</h1>
  <p class="meta">MIEZ Corp · {report.category} · {report.period} · {today}</p>
  <p>Report content unavailable. Please try regenerating.</p>
</body>
</html>"""


def generate_report_file(report, user=None, directives='', context_data=''):
    reports_dir = Path(settings.BASE_DIR) / 'reports'
    reports_dir.mkdir(exist_ok=True)

    html_content = _build_html_with_claude(report, directives=directives, context_data=context_data)

    file_path = reports_dir / f'{report.slug}.html'
    file_path.write_text(html_content, encoding='utf-8')

    size_bytes = file_path.stat().st_size
    size_kb = max(1, size_bytes // 1024)
    report.file_path = str(file_path)
    report.file_size_kb = size_kb
    report.generated_at = timezone.now()
    if user is not None:
        report.generated_by = user
    report.save(update_fields=['file_path', 'file_size_kb', 'generated_at', 'generated_by'])
