"""
Jinja2 HTML template and CSS for the PDF audit report.

The styling mirrors the "old-money" Courier Prime aesthetic from ``app.py``:
flat 1px borders, no shadows, hairline greys, monospace numerals. CJK text
falls back to system fonts (Hiragino Sans GB on macOS, Noto Sans CJK on Linux).
"""

from __future__ import annotations

from jinja2 import Template

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

REPORT_CSS = """
@page {
    size: A4;
    margin: 1.5cm 1.5cm 1.5cm 1.5cm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: "Courier Prime", "Courier New", monospace;
        font-size: 0.7rem;
        color: rgba(40, 40, 40, 0.5);
        padding-top: 6pt;
    }
}

html, body {
    font-family: "Courier Prime", "Courier New", "Hiragino Sans GB",
                 "Noto Sans CJK SC", "STHeiti", "PingFang SC", monospace;
    color: #1a1a1a;
    font-size: 9pt;
    line-height: 1.55;
    margin: 0;
    padding: 0;
}

/* ── Cover ───────────────────────────────────────────────────────────── */
.cover {
    page-break-after: always;
    padding-top: 3cm;
    text-align: left;
}
.cover .ruler {
    width: 100%;
    height: 1px;
    background: rgba(40, 40, 40, 0.4);
    margin: 0.6cm 0 1.2cm 0;
}
.cover {
    font-size: 0.7rem;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    opacity: 0.55;
    margin-bottom: 0.3cm;
}
.cover h1 {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0 0 0.2cm 0;
    line-height: 1.25;
}
.cover .subtitle {
    font-size: 1.05rem;
    opacity: 0.7;
    margin-bottom: 1.5cm;
}
.cover .meta-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 0.5cm;
    font-size: 0.85rem;
}
.cover .meta-table td {
    border: 1px solid rgba(128, 128, 128, 0.2);
    padding: 0.45rem 0.6rem;
    vertical-align: top;
}
.cover .meta-table td.label {
    width: 32%;
    opacity: 0.55;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    font-size: 0.7rem;
}
.cover .footer-note {
    margin-top: 4cm;
    font-size: 0.7rem;
    opacity: 0.5;
    line-height: 1.5;
}

/* ── Headings ────────────────────────────────────────────────────────── */
h2.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0 0 0.4cm 0;
    padding-bottom: 0.2cm;
    border-bottom: 1px solid rgba(40, 40, 40, 0.4);
}
h3.subsection {
    font-size: 0.95rem;
    font-weight: 700;
    margin: 0.5cm 0 0.25cm 0;
    opacity: 0.85;
}
.section {
    page-break-inside: auto;
}
.section-break {
    break-before: page;
}
p { margin: 0.3cm 0; }
.intro { margin-bottom: 0.4cm; opacity: 0.85; }
.bullet { margin: 0.15cm 0 0.15cm 0.4cm; opacity: 0.85; }

/* ── Metric cards (4-up grid) ────────────────────────────────────────── */
.metric-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4cm;
    margin: 0.3cm 0 0.5cm 0;
}
.metric-card {
    flex: 1 1 22%;
    min-width: 22%;
    border: 1px solid rgba(128, 128, 128, 0.25);
    border-radius: 0;
    padding: 0.5rem 0.6rem;
    background: transparent;
}
.metric-card .label {
    font-size: 0.7rem;
    opacity: 0.6;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.2rem;
    line-height: 1.2;
}
.metric-card .value {
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.3;
}
.metric-card .help {
    font-size: 0.65rem;
    opacity: 0.5;
    margin-top: 0.2rem;
    line-height: 1.3;
}

/* ── Charts ──────────────────────────────────────────────────────────── */
.chart-block {
    margin: 0.3cm 0 0.5cm 0;
    text-align: center;
    page-break-inside: avoid;
}
.chart-block img {
    width: 100%;
    max-width: 120%;
    height: 100%;
    max-height: 120%;
}
.chart-caption {
    font-size: 0.7rem;
    opacity: 0.5;
    margin-top: 0.15cm;
}

/* ── Tables ──────────────────────────────────────────────────────────── */
table.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.3cm 0 0.5cm 0;
    font-size: 0.75rem;
    page-break-inside: auto;
}
table.data-table th,
table.data-table td {
    border: 1px solid rgba(128, 128, 128, 0.2);
    padding: 0.35rem 0.45rem;
    text-align: right;
    vertical-align: top;
}
table.data-table th {
    background: rgba(128, 128, 128, 0.06);
    font-weight: 700;
    text-align: center;
    font-size: 0.7rem;
}
table.data-table td.label-col,
table.data-table th.label-col {
    text-align: left;
}
table.data-table tr {
    page-break-inside: avoid;
}

/* ── Checklist principles ────────────────────────────────────────────── */
.principle {
    border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    padding: 0.5cm 0;
    page-break-inside: avoid;
}
.principle .header {
    font-size: 0.95rem;
    font-weight: 700;
    margin-bottom: 0.2cm;
}
.principle .facts {
    font-size: 0.8rem;
    margin: 0.15cm 0;
}
.principle .facts .label {
    opacity: 0.6;
    margin-right: 0.2cm;
}
.principle .facts strong { font-weight: 700; }
.principle .desc {
    font-size: 0.78rem;
    opacity: 0.8;
    margin-top: 0.2cm;
    line-height: 1.5;
}

/* ── Badges ──────────────────────────────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 0.05rem 0.4rem;
    border: 1px solid rgba(128, 128, 128, 0.4);
    border-radius: 0;
    font-weight: 700;
    font-size: 0.78rem;
    margin-right: 0.4rem;
}
.badge-pass    { color: #4ca66b; border-color: rgba(76, 166, 107, 0.5); }
.badge-fail    { color: #c0463e; border-color: rgba(192, 70, 62, 0.5); text-decoration: underline; }
.badge-warning { color: #b8860b; border-color: rgba(184, 134, 11, 0.5); border-bottom: 1px dashed rgba(184,134,11,0.6); }
.badge-insufficient { color: #8a8a8a; opacity: 0.6; border-color: rgba(138, 138, 138, 0.4); }

/* ── Alerts (callouts) ───────────────────────────────────────────────── */
.alert {
    border: 1px solid rgba(128, 128, 128, 0.15);
    border-left: 4px solid rgba(128, 128, 128, 0.55);
    padding: 0.5rem 0.7rem;
    margin: 0.3cm 0;
    background: rgba(128, 128, 128, 0.04);
    font-size: 0.8rem;
}
.alert-warning { border-left-color: #b8860b; background: rgba(184, 134, 11, 0.05); }
.alert-success { border-left-color: #4ca66b; background: rgba(76, 166, 107, 0.05); }
.alert-info    { border-left-color: #3399ff; background: rgba(51, 153, 255, 0.04); }

/* ── Summary block ───────────────────────────────────────────────────── */
.summary-grid {
    display: flex;
    gap: 0.4cm;
    margin: 0.4cm 0;
}
.summary-cell {
    flex: 1 1 24%;
    border: 1px solid rgba(128, 128, 128, 0.25);
    padding: 0.6rem 0.7rem;
    text-align: center;
}
.summary-cell .count {
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.1;
}
.summary-cell .name {
    font-size: 0.7rem;
    opacity: 0.6;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.2rem;
}
.count-pass    { color: #4ca66b; }
.count-fail    { color: #c0463e; }
.count-warning { color: #b8860b; }
.count-insufficient { color: #8a8a8a; }

/* ── Appendix params table ───────────────────────────────────────────── */
table.params-table th { text-align: left; }
table.params-table td { text-align: left; }
table.params-table td.value { font-weight: 700; }

/* ── Disclaimer ──────────────────────────────────────────────────────── */
.disclaimer {
    margin-top: 0.5cm;
    font-size: 0.72rem;
    opacity: 0.65;
    line-height: 1.55;
    border-top: 1px solid rgba(128, 128, 128, 0.25);
    padding-top: 0.4cm;
}

/* ── Misc ────────────────────────────────────────────────────────────── */
.small { font-size: 0.72rem; opacity: 0.65; }
.muted { opacity: 0.55; }
hr.thin {
    border: none;
    border-top: 1px solid rgba(128, 128, 128, 0.2);
    margin: 0.4cm 0;
}
.numeric { font-variant-numeric: tabular-nums; }
"""

# ---------------------------------------------------------------------------
# Jinja2 template
# ---------------------------------------------------------------------------

REPORT_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
<meta charset="utf-8">
<title>{{ report_title }} - {{ company_name }}</title>
<style>{{ css }}</style>
</head>
<body>

<!-- ════════════════════════ COVER ════════════════════════ -->
<section class="cover">
    <h1>{{ report_title }}</h1>
    <p class="subtitle">{{ company_name }} · {{ ticker }}</p>
    <div class="ruler"></div>
    <table class="meta-table">
        <tr><td class="label">{{ labels.company }}</td><td>{{ company_name }} ({{ ticker }})</td></tr>
        <tr><td class="label">{{ labels.years }}</td><td>{{ years_range }} ({{ n_years }})</td></tr>
        <tr><td class="label">{{ labels.currency_unit }}</td><td>{{ currency }} / {{ amount_unit_label }}</td></tr>
        <tr><td class="label">{{ labels.market_currency }}</td><td>{{ market_currency }}</td></tr>
        <tr><td class="label">{{ labels.generated_at }}</td><td>{{ generated_at }}</td></tr>
        <tr><td class="label">{{ labels.language }}</td><td>{{ language_label }}</td></tr>
    </table>
    <p class="footer-note">{{ footer_note }}</p>
</section>

<!-- ════════════════════════ SECTIONS ════════════════════════ -->
{% for section in body_sections %}
<section class="section{% if loop.index > 1 %} section-break{% endif %}">
    <h2 class="section-title">{{ section.title }}</h2>
    {% if section.intro %}<p class="intro">{{ section.intro }}</p>{% endif %}
    {% for bullet in section.bullets %}<p class="bullet">{{ bullet }}</p>{% endfor %}
    {% if section.alert %}<div class="alert alert-{{ section.alert.kind }}">{{ section.alert.text }}</div>{% endif %}
    {% for chart in section.charts %}
        <div class="chart-block">
            <img src="{{ chart.src }}" alt="{{ chart.alt }}">
            {% if chart.caption %}<div class="chart-caption">{{ chart.caption }}</div>{% endif %}
        </div>
    {% endfor %}
    {% if section.metrics %}
    <h3 class="subsection">{{ section.metrics_header }}</h3>
    <div class="metric-grid">
        {% for m in section.metrics %}
        <div class="metric-card">
            <div class="label">{{ m.label }}</div>
            <div class="value numeric">{{ m.value }}</div>
            {% if m.help %}<div class="help">{{ m.help }}</div>{% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}
    {% if section.tables %}
        {% for tbl in section.tables %}
        {% if tbl.caption %}<h3 class="subsection">{{ tbl.caption }}</h3>{% endif %}
        <table class="data-table">
            <thead><tr>
                {% for h in tbl.headers %}<th{% if loop.first %} class="label-col"{% endif %}>{{ h }}</th>{% endfor %}
            </tr></thead>
            <tbody>
                {% for row in tbl.rows %}
                <tr>
                    {% for cell in row %}<td{% if loop.first %} class="label-col"{% endif %}>{{ cell }}</td>{% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endfor %}
    {% endif %}
    {% for principle in section.principles %}
    <div class="principle">
        <p class="header">
            <span class="badge badge-{{ principle.status }}">{{ principle.badge }}</span>
            {{ principle.principle_label }}: {{ principle.title }}
        </p>
        <p class="facts">
            <span class="label">{{ principle.actual_label }}</span><strong>{{ principle.value }}</strong>
            &nbsp;&nbsp;
            <span class="label">{{ principle.benchmark_label }}</span><strong>{{ principle.benchmark }}</strong>
        </p>
        <p class="desc">{{ principle.description }}</p>
    </div>
    {% endfor %}
    {% if section.guidance_header %}
    <h3 class="subsection">{{ section.guidance_header }}</h3>
    {% for g in section.guidance_bullets %}<p class="bullet">{{ g }}</p>{% endfor %}
    {% endif %}
    {% if section.summary %}<div class="alert alert-info">{{ section.summary }}</div>{% endif %}
    {% if section.disclaimers %}
        {% for d in section.disclaimers %}<p class="small">{{ d }}</p>{% endfor %}
    {% endif %}
</section>
{% endfor %}

<!-- ════════════════════════ APPENDIX ════════════════════════ -->
<section class="section section-break">
    <h2 class="section-title">{{ appendix_title }}</h2>
    <p class="intro">{{ appendix_intro }}</p>
    <table class="data-table params-table">
        <thead><tr><th class="label-col">{{ labels.param }}</th><th>{{ labels.value }}</th></tr></thead>
        <tbody>
            {% for p in params %}
            <tr><td class="label-col">{{ p.name }}</td><td class="value numeric">{{ p.value }}</td></tr>
            {% endfor %}
        </tbody>
    </table>
    <div class="disclaimer">
        <p>{{ disclaimer_1 }}</p>
        <p>{{ disclaimer_2 }}</p>
    </div>
</section>

</body>
</html>
"""
)


def render_html(context: dict) -> str:
    """Render the full HTML document from a context dict."""
    return REPORT_TEMPLATE.render(css=REPORT_CSS, **context)
