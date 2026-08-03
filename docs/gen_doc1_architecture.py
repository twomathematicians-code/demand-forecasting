#!/usr/bin/env python3
"""Generate Document 1: Client Requirements & Technical Architecture."""

import os, sys, hashlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ━━ Color Palette (auto-generated) ━━
# Intent: neutral | Mode: minimal | Harmony: split_complementary
ACCENT       = colors.HexColor('#5329d1')
TEXT_PRIMARY  = colors.HexColor('#212324')
TEXT_MUTED    = colors.HexColor('#757e82')
BG_SURFACE   = colors.HexColor('#d8dee1')
BG_PAGE      = colors.HexColor('#f3f4f5')
TABLE_HEADER_COLOR = ACCENT
TABLE_HEADER_TEXT  = colors.white
TABLE_ROW_EVEN     = colors.white
TABLE_ROW_ODD      = BG_SURFACE

# ━━ Font Registration ━━
FONTS_DIR = 'C:/Windows/Fonts'
pdfmetrics.registerFont(TTFont('TimesNewRoman', os.path.join(FONTS_DIR, 'times.ttf')))
pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', os.path.join(FONTS_DIR, 'timesbd.ttf')))
pdfmetrics.registerFont(TTFont('TimesNewRoman-Italic', os.path.join(FONTS_DIR, 'timesi.ttf')))
pdfmetrics.registerFont(TTFont('TimesNewRoman-BI', os.path.join(FONTS_DIR, 'timesbi.ttf')))
registerFontFamily('TimesNewRoman', normal='TimesNewRoman', bold='TimesNewRoman-Bold',
                   italic='TimesNewRoman-Italic', boldItalic='TimesNewRoman-BI')

# ━━ Styles ━━
PAGE_W, PAGE_H = A4
MARGIN = 0.85 * inch
AVAILABLE_W = PAGE_W - 2 * MARGIN

styles = {}

styles['title'] = ParagraphStyle(
    name='Title', fontName='TimesNewRoman-Bold', fontSize=26, leading=34,
    textColor=ACCENT, alignment=TA_LEFT, spaceAfter=8, spaceBefore=0,
)

styles['h1'] = ParagraphStyle(
    name='H1', fontName='TimesNewRoman-Bold', fontSize=18, leading=24,
    textColor=ACCENT, alignment=TA_LEFT, spaceAfter=10, spaceBefore=22,
)

styles['h2'] = ParagraphStyle(
    name='H2', fontName='TimesNewRoman-Bold', fontSize=14, leading=20,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=6, spaceBefore=16,
)

styles['h3'] = ParagraphStyle(
    name='H3', fontName='TimesNewRoman-Bold', fontSize=12, leading=17,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=4, spaceBefore=12,
)

styles['body'] = ParagraphStyle(
    name='Body', fontName='TimesNewRoman', fontSize=10.5, leading=16,
    textColor=TEXT_PRIMARY, alignment=TA_JUSTIFY, spaceAfter=8, spaceBefore=0,
)

styles['body_indent'] = ParagraphStyle(
    name='BodyIndent', fontName='TimesNewRoman', fontSize=10.5, leading=16,
    textColor=TEXT_PRIMARY, alignment=TA_JUSTIFY, spaceAfter=8, spaceBefore=0,
    leftIndent=18, bulletIndent=6,
)

styles['bullet'] = ParagraphStyle(
    name='Bullet', fontName='TimesNewRoman', fontSize=10.5, leading=16,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=4, spaceBefore=0,
    leftIndent=24, bulletIndent=12, bulletFontName='TimesNewRoman',
)

styles['caption'] = ParagraphStyle(
    name='Caption', fontName='TimesNewRoman-Italic', fontSize=9.5, leading=14,
    textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=14, spaceBefore=4,
)

styles['table_header'] = ParagraphStyle(
    name='TableHeader', fontName='TimesNewRoman-Bold', fontSize=10,
    textColor=colors.white, alignment=TA_CENTER, leading=13,
)

styles['table_cell'] = ParagraphStyle(
    name='TableCell', fontName='TimesNewRoman', fontSize=9.5,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT, leading=13,
)

styles['table_cell_center'] = ParagraphStyle(
    name='TableCellCenter', fontName='TimesNewRoman', fontSize=9.5,
    textColor=TEXT_PRIMARY, alignment=TA_CENTER, leading=13,
)

styles['callout_value'] = ParagraphStyle(
    name='CalloutValue', fontName='TimesNewRoman-Bold', fontSize=22, leading=28,
    textColor=ACCENT, alignment=TA_CENTER,
)

styles['callout_label'] = ParagraphStyle(
    name='CalloutLabel', fontName='TimesNewRoman', fontSize=9, leading=13,
    textColor=TEXT_MUTED, alignment=TA_CENTER,
)

styles['toc1'] = ParagraphStyle(
    name='TOC1', fontName='TimesNewRoman-Bold', fontSize=13, leading=20,
    leftIndent=20, textColor=TEXT_PRIMARY,
)
styles['toc2'] = ParagraphStyle(
    name='TOC2', fontName='TimesNewRoman', fontSize=11, leading=17,
    leftIndent=40, textColor=TEXT_PRIMARY,
)

# ═══════════════════════════════════════════════════════════════
# TOC DocTemplate
# ═══════════════════════════════════════════════════════════════

class TocDocTemplate(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        SimpleDocTemplate.__init__(self, *args, **kwargs)
        self._toc_entries = []

    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            key = getattr(flowable, 'bookmark_key', '')
            self.notify('TOCEntry', (level, text, self.page, key))

# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def add_heading(text, style, level=0):
    key = 'h_%s' % hashlib.md5(text.encode()).hexdigest()[:8]
    p = Paragraph('<a name="%s"/>%s' % (key, text), style)
    p.bookmark_name = text
    p.bookmark_level = level
    p.bookmark_text = text
    p.bookmark_key = key
    return p

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=TEXT_MUTED, spaceBefore=8, spaceAfter=10)

def bullet(text):
    return Paragraph('\u2022  %s' % text, styles['bullet'])

def numbered(n, text):
    return Paragraph('<b>%d.</b>  %s' % (n, text), styles['body_indent'])

def callout_box(value, label):
    """Create a callout/metric box."""
    data = [[Paragraph(value, styles['callout_value'])],
            [Paragraph(label, styles['callout_label'])]]
    t = Table(data, colWidths=[130], hAlign='CENTER')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, TEXT_MUTED),
        ('TOPPADDING', (0, 0), (-1, 1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t

def make_table(headers, rows, col_widths=None):
    """Create a styled table with header and rows."""
    if col_widths is None:
        col_widths = [AVAILABLE_W / len(headers)] * len(headers)
    data = [[Paragraph('<b>%s</b>' % h, styles['table_header']) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), styles['table_cell']) for c in row])
    t = Table(data, colWidths=col_widths, hAlign='CENTER')
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, TEXT_MUTED),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ROW_ODD))
        else:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ROW_EVEN))
    t.setStyle(TableStyle(style_cmds))
    return t

def callout_row(values_labels):
    """Create a row of callout boxes."""
    n = len(values_labels)
    w = (AVAILABLE_W - (n - 1) * 10) / n
    data = []
    row_vals = []
    row_lbls = []
    for v, l in values_labels:
        row_vals.append(Paragraph(v, styles['callout_value']))
        row_lbls.append(Paragraph(l, styles['callout_label']))
    data.append(row_vals)
    data.append(row_lbls)
    t = Table(data, colWidths=[w] * n, hAlign='CENTER')
    cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
        ('BOX', (0, 0), (-1, 0), 0.5, TEXT_MUTED),
        ('BOX', (0, 1), (-1, 1), 0.5, TEXT_MUTED),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, TEXT_MUTED),
        ('TOPPADDING', (0, 0), (-1, 1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    t.setStyle(TableStyle(cmds))
    return t


# ═══════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ═══════════════════════════════════════════════════════════════

def build_body():
    output_path = os.path.join(os.path.dirname(__file__), 'doc1_body.pdf')
    doc = TocDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.7*inch, bottomMargin=0.7*inch,
        title='Intelligent Demand Forecasting Platform - Client Requirements & Technical Architecture',
        author='Mahesh Solanki',
    )

    story = []

    # ── TOC ──
    toc = TableOfContents()
    toc.levelStyles = [styles['toc1'], styles['toc2']]
    story.append(Paragraph('<b>Table of Contents</b>', styles['title']))
    story.append(Spacer(1, 12))
    story.append(toc)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # 1. EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════
    story.append(add_heading('1. Executive Summary', styles['h1'], level=0))
    story.append(hr())
    story.append(Paragraph(
        'This document presents the technical architecture and client requirements for an '
        '<b>Intelligent Demand Forecasting Platform</b> designed to serve civilian utilities, '
        'industrial supply chains, and enterprise capacity planning. The platform integrates '
        'climate-aware forecasting, industry-wise demand-supply clustering, real-time data '
        'streaming, and deep learning models (CNN+LSTM) within a comprehensive MLOps framework.',
        styles['body']
    ))
    story.append(Paragraph(
        'Drawing on market-leading practices from PJM Interconnection, United Utilities, '
        'Sydney Water, HP Inc., and automotive supply chains across 90+ countries, this '
        'architecture delivers production-grade forecasting with measured accuracy '
        'improvements of 30-35% over traditional statistical methods.',
        styles['body']
    ))

    story.append(Spacer(1, 6))
    story.append(callout_row([
        ('3', 'Requirement\nAreas'),
        ('4-6%', 'Target MAPE\nAccuracy'),
        ('20 Weeks', 'Implementation\nTimeline'),
        ('CNN+LSTM', 'Core Deep Learning\nArchitecture'),
    ]))
    story.append(Paragraph('<i>Figure 1: Platform at a glance</i>', styles['caption']))

    story.append(Spacer(1, 14))

    # ═══════════════════════════════════════════════════════
    # 2. REQUIREMENT AREA 1: CLIMATE-AWARE UTILITY FORECASTING
    # ═══════════════════════════════════════════════════════
    story.append(add_heading('2. Climate-Aware Civilian Utility Demand Forecasting', styles['h1'], level=0))
    story.append(hr())

    story.append(Paragraph(
        'Predict civilian demand for water, energy, and natural gas by integrating '
        'meteorological parameters as primary exogenous variables. This requirement '
        'addresses the critical dependency of utility consumption on weather patterns, '
        'seasonal cycles, and extreme climate events.',
        styles['body']
    ))

    story.append(add_heading('2.1 Key Climate & Utility Parameters', styles['h2'], level=1))
    story.append(make_table(
        ['Parameter Category', 'Variables', 'Source', 'Granularity'],
        [
            ['Temperature', 'HDD, CDD, Min/Max/Mean temp', 'Met Office / NOAA API', 'Hourly/Daily'],
            ['Precipitation', 'Rainfall, Snow, Drought indices', 'Weather Service', 'Daily'],
            ['Seasonality', 'Spring/Fall flags, Daylight hours', 'Calendar-derived', 'Daily'],
            ['Extreme Events', 'Heatwaves, Freeze-thaw, Storms', 'Weather Alerts', 'Event-based'],
            ['Climate Projection', 'UKCP09/UKCP18 uplift factors', 'Climate Agencies', 'Annual'],
            ['Calendar', 'Day of week, Holidays, Weekend flags', 'Internal', 'Daily'],
            ['Utility Metering', 'Consumption (kWh, m3, liters)', 'Smart Meters / SCADA', '15-min to Hourly'],
        ],
        [AVAILABLE_W * 0.20, AVAILABLE_W * 0.30, AVAILABLE_W * 0.25, AVAILABLE_W * 0.25]
    ))

    story.append(add_heading('2.2 Forecast Horizons', styles['h2'], level=1))
    story.append(make_table(
        ['Horizon', 'Duration', 'Use Case', 'Update Frequency'],
        [
            ['Short-term', '24-72 hours', 'Operational dispatch, pump scheduling', 'Hourly'],
            ['Medium-term', '7-30 days', 'Tactical planning, maintenance windows', 'Daily'],
            ['Long-term', '1-5 years', 'Strategic capacity, infrastructure investment', 'Monthly/Quarterly'],
        ],
        [AVAILABLE_W * 0.18, AVAILABLE_W * 0.18, AVAILABLE_W * 0.40, AVAILABLE_W * 0.24]
    ))

    story.append(add_heading('2.3 Industry Benchmarks', styles['h2'], level=1))
    story.append(Paragraph(
        'The table below summarizes production-grade implementations that inform our architecture:',
        styles['body']
    ))
    story.append(make_table(
        ['Organization', 'Domain', 'Approach', 'Key Result'],
        [
            ['PJM Interconnection', 'US Energy Grid', 'HDD/CDD + sector-level models', 'Operational hourly load forecasting across residential, commercial, industrial'],
            ['United Utilities (UK)', 'Water Resources', 'Met Office data + 1-in-500-year extreme scenarios', 'Demand forecasts extended to 2050 horizon'],
            ['Welland Hydro (Canada)', 'Energy Distribution', 'Multivariate regression with HDD/CDD', 'R-squared = 88.9% for weather-normalized energy'],
            ['Sydney Water (AU)', 'Water Distribution', 'Deep learning + weather integration', '10-day operational short-term forecast framework'],
            ['Tetouan/Astana Study', 'Energy (Research)', 'K-Means + Neural Network Regression', 'MAPE 5.19% vs. baseline 17.36%'],
        ],
        [AVAILABLE_W * 0.18, AVAILABLE_W * 0.14, AVAILABLE_W * 0.32, AVAILABLE_W * 0.36]
    ))

    story.append(add_heading('2.4 Recommended Model Ensemble', styles['h2'], level=1))
    story.append(bullet('<b>Prophet</b> with external weather regressors for trend and seasonality decomposition'))
    story.append(bullet('<b>LightGBM</b> with lagged weather features (7-day, 30-day, 365-day lags) for gradient-boosted predictions'))
    story.append(bullet('<b>SARIMAX</b> with HDD/CDD covariates for statistical baseline'))
    story.append(bullet('<b>CNN-LSTM Hybrid</b> for deep sequence modeling with multivariate weather inputs'))
    story.append(bullet('<b>Ensemble blending</b> with horizon-aware weights optimized against wMAPE'))

    # ═══════════════════════════════════════════════════════
    # 3. REQUIREMENT AREA 2: INDUSTRY CLUSTERING & BI
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(add_heading('3. Industry-Wise Clustering & BI Application with Streaming Data', styles['h1'], level=0))
    story.append(hr())

    story.append(Paragraph(
        'Enable demand-supply optimization through industry-wise clustering of consumption '
        'patterns, real-time data streaming, and business intelligence dashboards designed '
        'for capacity orchestration across client operations.',
        styles['body']
    ))

    story.append(add_heading('3.1 Clustering Methodology', styles['h2'], level=1))
    story.append(Paragraph(
        'We implement a two-tier clustering strategy combining Pareto segmentation for '
        'high-value items with unsupervised learning for pattern-based grouping:',
        styles['body']
    ))

    story.append(add_heading('Pareto Segmentation (Tier 1)', styles['h3'], level=2))
    story.append(bullet('Top ~10% of items generating ~80% of revenue modeled individually'))
    story.append(bullet('Long-tail items pooled into clusters for shared model training'))
    story.append(bullet('Threshold determined by cumulative revenue curve analysis'))

    story.append(add_heading('Demand Pattern Clustering (Tier 2)', styles['h3'], level=2))
    story.append(make_table(
        ['Algorithm', 'Strengths', 'Best For', 'Benchmark Score'],
        [
            ['K-Means', 'Fast, scalable, well-understood', 'Spherical clusters, initial segmentation', 'Silhouette: 0.724'],
            ['DBSCAN', 'Handles outliers, arbitrary shapes', 'Noisy data, irregular demand patterns', 'Score: 0.89 vs K-Means 0.724'],
            ['Hierarchical', 'Dendrogram visualization', 'Taxonomy creation, executive reporting', 'Interpretability: High'],
        ],
        [AVAILABLE_W * 0.15, AVAILABLE_W * 0.30, AVAILABLE_W * 0.30, AVAILABLE_W * 0.25]
    ))
    story.append(Paragraph(
        '<b>Recommendation:</b> DBSCAN as primary clustering algorithm due to its robustness '
        'to noise and irregular cluster shapes, outperforming K-Means by 23% in retail '
        'benchmarks (score 0.89 vs. 0.724). K-Means retained for initial exploratory analysis.',
        styles['body']
    ))

    story.append(add_heading('3.2 Streaming Data Architecture', styles['h2'], level=1))
    story.append(make_table(
        ['Component', 'Technology', 'Purpose'],
        [
            ['Message Broker', 'Apache Kafka / Redpanda', 'Real-time ingestion from IoT meters, POS, ERP'],
            ['Stream Processing', 'Kafka Streams / Apache Flink', 'Windowed aggregations, real-time feature computation'],
            ['Change Data Capture', 'Debezium', 'CDC from PostgreSQL/ERP source systems'],
            ['Feature Computation', 'Feast (Feature Store)', 'Online feature serving for real-time inference'],
            ['Anomaly Detection', 'Custom Spark Streaming jobs', 'Real-time anomaly scoring on demand patterns'],
        ],
        [AVAILABLE_W * 0.22, AVAILABLE_W * 0.35, AVAILABLE_W * 0.43]
    ))

    story.append(add_heading('3.3 BI Application Design', styles['h2'], level=1))
    story.append(bullet('<b>Interactive Dashboards:</b> MAPE/WMAPE tracking, forecast vs. actual comparison, bias decomposition by product category, region, and season'))
    story.append(bullet('<b>Revenue-Weighted Views:</b> Connect forecasting accuracy to business impact — over-forecast cost (excess inventory) vs. under-forecast cost (stockout/lost sales)'))
    story.append(bullet('<b>Role-Based Access:</b> Executive summary (KPIs), Planner workspace (drill-down forecast adjustment), Operator view (real-time alerting)'))
    story.append(bullet('<b>Alert System:</b> Automated notifications for forecast drift exceeding thresholds, anomaly detection triggers, and model performance degradation'))
    story.append(bullet('<b>What-If Scenario Engine:</b> Simulate weather events, promotion campaigns, supply disruptions, and capacity changes'))

    story.append(add_heading('3.4 Capacity Orchestration', styles['h2'], level=1))
    story.append(bullet('<b>Safety Stock Optimization:</b> Dynamic buffer calculation based on forecast uncertainty (prediction intervals)'))
    story.append(bullet('<b>Dynamic Reorder Points:</b> Adjust replenishment thresholds using real-time demand signals'))
    story.append(bullet('<b>Multi-Echelon Optimization:</b> Coordinate inventory levels across distribution centers, warehouses, and retail locations'))
    story.append(bullet('<b>Capacity Reservation:</b> Predictive booking of production slots, transport capacity, and storage based on forecast confidence'))

    # ═══════════════════════════════════════════════════════
    # 4. REQUIREMENT AREA 3: CNN+LSTM & MLOps
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(add_heading('4. CNN+LSTM Deep Learning & MLOps Pipeline', styles['h1'], level=0))
    story.append(hr())

    story.append(Paragraph(
        'Implement a CNN-LSTM hybrid architecture for demand classification and forecasting, '
        'integrated within a production-grade MLOps framework. The CNN layers extract local '
        'spatial and short-term temporal features, while bidirectional LSTM layers capture '
        'long-range dependencies in demand sequences.',
        styles['body']
    ))

    story.append(add_heading('4.1 CNN-LSTM Architecture', styles['h2'], level=1))
    story.append(Paragraph(
        'The proposed architecture follows the proven pattern from 2024 research showing '
        'CNN-LSTM hybrids outperform standalone models by 12-24% on MAPE:',
        styles['body']
    ))
    story.append(make_table(
        ['Layer', 'Configuration', 'Purpose'],
        [
            ['Input', '(batch, seq_len, n_features)', 'Multivariate time series window (30-90 days)'],
            ['Conv1D', '64 filters, kernel=3, ReLU, BatchNorm', 'Local pattern extraction (short-term trends)'],
            ['Conv1D', '128 filters, kernel=3, ReLU, BatchNorm', 'Higher-level feature extraction'],
            ['MaxPool1D', 'pool_size=2', 'Dimensionality reduction, translation invariance'],
            ['Dropout', 'Rate=0.3', 'Regularization, prevent overfitting'],
            ['BiLSTM', '128 units, return_sequences=True', 'Bidirectional temporal dependency modeling'],
            ['BiLSTM', '64 units, return_sequences=False', 'Final temporal encoding'],
            ['Dropout', 'Rate=0.3', 'Regularization'],
            ['Dense', '32 units, ReLU', 'Feature compression'],
            ['Dense (Output)', 'n_outputs', 'Regression: linear | Classification: softmax'],
        ],
        [AVAILABLE_W * 0.18, AVAILABLE_W * 0.40, AVAILABLE_W * 0.42]
    ))

    story.append(add_heading('4.2 Performance Benchmarks', styles['h2'], level=1))
    story.append(Paragraph(
        'Based on published 2024 literature comparing models on supply chain demand forecasting tasks:',
        styles['body']
    ))
    story.append(make_table(
        ['Model', 'MAE', 'RMSE', 'MAPE (%)', 'R-squared'],
        [
            ['ARIMA (Statistical Baseline)', '143.67', '180.24', '15.29', '0.62'],
            ['Standalone LSTM', '125.76', '160.21', '13.11', '0.71'],
            ['XGBoost', '120.98', '158.67', '12.89', '0.72'],
            ['CNN-LSTM Hybrid', '110.32', '148.76', '11.48', '0.76'],
            ['CNN-BiLSTM (2024 State-of-Art)', '—', '—', '—', '0.966 (Accuracy)'],
        ],
        [AVAILABLE_W * 0.28, AVAILABLE_W * 0.18, AVAILABLE_W * 0.18, AVAILABLE_W * 0.18, AVAILABLE_W * 0.18]
    ))
    story.append(Paragraph(
        '<b>Key Finding:</b> CNN-LSTM reduces MAPE by 25% vs. ARIMA and 11% vs. standalone LSTM. '
        'The 2024 CNN-BiLSTM variant achieves 96.57% accuracy on supply chain optimization tasks.',
        styles['body']
    ))

    story.append(add_heading('4.3 Classification Use Cases', styles['h2'], level=1))
    story.append(make_table(
        ['Classification Task', 'Classes', 'Business Application'],
        [
            ['Demand Level', 'Low / Medium / High / Critical', 'Resource allocation, staffing levels'],
            ['Anomaly Detection', 'Normal / Anomalous', 'Real-time alerting, fraud/leak detection'],
            ['Demand Volatility Tier', 'Stable / Seasonal / Volatile / Intermittent', 'Model selection, safety stock policy'],
            ['Event Impact', 'Normal / Holiday / Weather / Promotion', 'Decomposition, what-if analysis'],
        ],
        [AVAILABLE_W * 0.25, AVAILABLE_W * 0.32, AVAILABLE_W * 0.43]
    ))

    story.append(add_heading('4.4 MLOps Pipeline', styles['h2'], level=1))
    story.append(Paragraph(
        'A complete MLOps framework ensures reproducibility, monitoring, and continuous improvement:',
        styles['body']
    ))
    story.append(make_table(
        ['Capability', 'Tool/Technology', 'Function'],
        [
            ['Experiment Tracking', 'MLflow', 'Artifact storage, model versioning, lineage tracking'],
            ['Feature Store', 'Feast', 'Real-time feature serving, point-in-time correctness'],
            ['Model Registry', 'MLflow Model Registry', 'Versioned models with metadata, stage transitions (Staging→Production→Archived)'],
            ['CI/CD', 'GitHub Actions / GitLab CI', 'Automated testing, deployment, rollback'],
            ['Orchestration', 'Apache Airflow / Prefect', 'Scheduled training pipelines, DAG management'],
            ['Data Drift Monitoring', 'Evidently AI', 'PSI on input features, auto-trigger investigation'],
            ['Concept Drift', 'Evidently AI / Custom', 'Rolling MAPE tracking, residual analysis'],
            ['A/B Testing', 'Custom Champion/Challenger', 'Statistical validation of new model versions'],
            ['Alerting', 'Prometheus + Grafana', 'Performance dashboards, Slack/Email alerts'],
            ['Audit Trail', 'MLflow + Custom Logging', 'All predictions logged with model version and inputs'],
        ],
        [AVAILABLE_W * 0.22, AVAILABLE_W * 0.32, AVAILABLE_W * 0.46]
    ))

    story.append(add_heading('4.5 Retraining Strategy', styles['h2'], level=1))
    story.append(bullet('<b>Scheduled:</b> Monthly retraining with new data as default cadence'))
    story.append(bullet('<b>Performance-triggered:</b> When rolling MAPE exceeds baseline by >20%'))
    story.append(bullet('<b>Drift-triggered:</b> PSI > 0.25 on any key feature, or concept drift detected in residuals'))
    story.append(bullet('<b>Event-triggered:</b> Major market changes, new product launches, regulatory shifts'))

    # ═══════════════════════════════════════════════════════
    # 5. SYSTEM ARCHITECTURE
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(add_heading('5. High-Level System Architecture', styles['h1'], level=0))
    story.append(hr())

    story.append(Paragraph(
        'The platform follows a layered architecture with clear separation of concerns '
        'across data ingestion, feature engineering, modeling, serving, and MLOps layers:',
        styles['body']
    ))

    # Architecture as a structured table
    arch_data = [
        [Paragraph('<b>DATA INGESTION LAYER</b>', styles['table_header'])],
        [Paragraph('Weather APIs (NOAA, Met Office) | Utility Smart Meters/SCADA | Industry ERP/SCM Systems | '
                   'Streaming Platform (Kafka/MQTT for IoT and real-time feeds)', styles['table_cell'])],
        [Paragraph('<b>DATA LAKE (S3 / MinIO)</b>', styles['table_header'])],
        [Paragraph('Raw data storage in columnar format (Parquet). Data versioning with DVC. '
                   'Schema validation with Great Expectations.', styles['table_cell'])],
        [Paragraph('<b>FEATURE ENGINEERING LAYER</b>', styles['table_header'])],
        [Paragraph('Lag features (t-1, t-7, t-30, t-365) | Rolling statistics (7d/30d mean/std/min/max) | '
                   'Weather encodings (HDD, CDD, precip) | Calendar features + cyclical encodings | '
                   'Cluster labels from DBSCAN/K-Means | Holiday flags and event markers', styles['table_cell'])],
        [Paragraph('<b>MODELING LAYER (Ensemble)</b>', styles['table_header'])],
        [Paragraph('Prophet (Trend + Seasonality) | LightGBM (GBDT with lagged features) | '
                   'SARIMAX (Statistical with exogenous regressors) | CNN-BiLSTM (Deep sequence modeling) | '
                   'Horizon-Aware Weighted Ensemble Blending', styles['table_cell'])],
        [Paragraph('<b>SERVING LAYER</b>', styles['table_header'])],
        [Paragraph('FastAPI REST API (real-time inference) | Streamlit Dashboard (BI/analytics) | '
                   'Power BI / Tableau Connector | Alerting Service (Slack/Email/SMS) | '
                   'ERP/IBP Integration Connectors', styles['table_cell'])],
        [Paragraph('<b>MLOps LAYER</b>', styles['table_header'])],
        [Paragraph('MLflow (Experiment Tracking + Model Registry) | Feast (Feature Store) | '
                   'Evidently AI (Drift Detection) | Apache Airflow (Pipeline Orchestration) | '
                   'GitHub Actions (CI/CD) | Prometheus + Grafana (Monitoring)', styles['table_cell'])],
    ]
    arch_table = Table(arch_data, colWidths=[AVAILABLE_W], hAlign='CENTER')
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('BACKGROUND', (0, 2), (-1, 2), ACCENT),
        ('BACKGROUND', (0, 4), (-1, 4), ACCENT),
        ('BACKGROUND', (0, 6), (-1, 6), ACCENT),
        ('BACKGROUND', (0, 8), (-1, 8), ACCENT),
        ('BACKGROUND', (0, 10), (-1, 10), ACCENT),
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
        ('BACKGROUND', (0, 3), (-1, 3), colors.white),
        ('BACKGROUND', (0, 5), (-1, 5), colors.white),
        ('BACKGROUND', (0, 7), (-1, 7), colors.white),
        ('BACKGROUND', (0, 9), (-1, 9), colors.white),
        ('BACKGROUND', (0, 11), (-1, 11), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.8, ACCENT),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, TEXT_MUTED),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(arch_table)
    story.append(Paragraph('<i>Figure 2: Layered system architecture overview</i>', styles['caption']))

    # ═══════════════════════════════════════════════════════
    # 6. TECHNOLOGY STACK
    # ═══════════════════════════════════════════════════════
    story.append(add_heading('6. Technology Stack Summary', styles['h1'], level=0))
    story.append(hr())
    story.append(make_table(
        ['Capability', 'Primary Technology', 'Alternative'],
        [
            ['Deep Learning', 'PyTorch / TensorFlow', 'JAX'],
            ['ML Framework', 'LightGBM + Prophet + statsmodels', 'XGBoost + sktime'],
            ['API Framework', 'FastAPI (Python 3.11+)', 'Flask, Django REST'],
            ['Experiment Tracking', 'MLflow', 'Weights & Biases'],
            ['Feature Store', 'Feast', 'Tecton'],
            ['Data Versioning', 'DVC', 'Delta Lake'],
            ['Orchestration', 'Apache Airflow', 'Prefect, Dagster'],
            ['Streaming', 'Apache Kafka / Redpanda', 'AWS Kinesis'],
            ['Monitoring', 'Evidently AI + Grafana', 'WhyLogs, NannyML'],
            ['Containerization', 'Docker + Kubernetes', 'Podman'],
            ['BI / Dashboard', 'Streamlit + Power BI', 'Tableau, Looker'],
            ['Data Quality', 'Great Expectations', 'Soda, Deequ'],
            ['CI/CD', 'GitHub Actions', 'GitLab CI, Jenkins'],
        ],
        [AVAILABLE_W * 0.25, AVAILABLE_W * 0.42, AVAILABLE_W * 0.33]
    ))

    # ═══════════════════════════════════════════════════════
    # 7. IMPLEMENTATION ROADMAP
    # ═══════════════════════════════════════════════════════
    story.append(add_heading('7. Implementation Roadmap', styles['h1'], level=0))
    story.append(hr())
    story.append(make_table(
        ['Phase', 'Duration', 'Key Deliverables'],
        [
            ['Phase 1: Foundation', 'Weeks 1-4', 'Data pipeline construction, weather API integration, basic Prophet & LightGBM models, baseline evaluation'],
            ['Phase 2: Deep Learning', 'Weeks 5-8', 'CNN-LSTM implementation, hyperparameter tuning with Optuna, model evaluation against baselines, MLflow experiment tracking'],
            ['Phase 3: Clustering & BI', 'Weeks 9-12', 'DBSCAN/K-Means industry clustering, Kafka streaming pipeline, Streamlit BI dashboards, what-if scenario engine'],
            ['Phase 4: MLOps', 'Weeks 13-16', 'Feast feature store, Evidently drift monitoring, Airflow orchestration, CI/CD pipelines, automated retraining triggers'],
            ['Phase 5: Production', 'Weeks 17-20', 'Load testing, security audit, A/B champion/challenger deployment, production cutover, user training & documentation'],
        ],
        [AVAILABLE_W * 0.20, AVAILABLE_W * 0.15, AVAILABLE_W * 0.65]
    ))

    # ═══════════════════════════════════════════════════════
    # 8. APPENDIX: CNN-LSTM REFERENCE ARCHITECTURE
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(add_heading('8. Appendix: CNN-BiLSTM Architecture Reference', styles['h1'], level=0))
    story.append(hr())
    story.append(Paragraph(
        'The following is the reference PyTorch implementation for the CNN-BiLSTM hybrid model:',
        styles['body']
    ))

    code_text = (
        'Input: (batch_size, sequence_length, n_features)\n'
        '    |\n'
        'Conv1D(filters=64, kernel_size=3) -> ReLU -> BatchNorm\n'
        '    |\n'
        'Conv1D(filters=128, kernel_size=3) -> ReLU -> BatchNorm\n'
        '    |\n'
        'MaxPooling1D(pool_size=2)\n'
        '    |\n'
        'Dropout(0.3)\n'
        '    |\n'
        'BiLSTM(units=128, return_sequences=True)\n'
        '    |\n'
        'BiLSTM(units=64, return_sequences=False)\n'
        '    |\n'
        'Dropout(0.3)\n'
        '    |\n'
        'Dense(32, activation=ReLU)\n'
        '    |\n'
        'Dense(n_outputs)  <- Regression: linear | Classification: softmax\n'
    )
    code_style = ParagraphStyle(
        'Code', fontName='TimesNewRoman', fontSize=9, leading=14,
        textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=8,
        leftIndent=20, backColor=BG_SURFACE,
    )
    story.append(Paragraph(code_text.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Spacer(1, 14))
    story.append(Paragraph(
        '<b>Training Configuration:</b> Adam optimizer with learning rate 0.001, '
        'ReduceLROnPlateau scheduler (factor=0.5, patience=10), EarlyStopping (patience=20), '
        'batch size 64, sequence length 60 days for short-term or 365 days for long-term forecasting, '
        'validation split 20% with TimeSeriesSplit cross-validation.',
        styles['body']
    ))

    story.append(Spacer(1, 20))
    story.append(hr())
    story.append(Paragraph(
        '<i>Document Version 1.0 | August 2026 | Prepared by Mahesh Solanki | '
        'Confidential — For Client Review Only</i>',
        ParagraphStyle('Footer', fontName='TimesNewRoman-Italic', fontSize=8, leading=12,
                       textColor=TEXT_MUTED, alignment=TA_CENTER)
    ))

    # ── Build ──
    doc.multiBuild(story)
    print(f'[DONE] Body PDF: {output_path}')
    return output_path

if __name__ == '__main__':
    build_body()
