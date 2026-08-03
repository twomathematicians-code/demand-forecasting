#!/usr/bin/env python3
"""Generate Document 2: SOP for Demand Forecasting ML Development."""

import os, sys, hashlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ━━ Color Palette (auto-generated) ━━
# Intent: neutral | Mode: minimal | Harmony: split_complementary
ACCENT       = colors.HexColor('#1f7693')
TEXT_PRIMARY  = colors.HexColor('#1d1f20')
TEXT_MUTED    = colors.HexColor('#80888c')
BG_SURFACE   = colors.HexColor('#e0e6e9')
BG_PAGE      = colors.HexColor('#f0f2f3')
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

# ━━ Dimensions ━━
PAGE_W, PAGE_H = A4
MARGIN = 0.85 * inch
AVAILABLE_W = PAGE_W - 2 * MARGIN

# ━━ Styles ━━
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
    textColor=TEXT_PRIMARY, alignment=TA_JUSTIFY, spaceAfter=6, spaceBefore=0,
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

styles['toc1'] = ParagraphStyle(
    name='TOC1', fontName='TimesNewRoman-Bold', fontSize=13, leading=20,
    leftIndent=20, textColor=TEXT_PRIMARY,
)
styles['toc2'] = ParagraphStyle(
    name='TOC2', fontName='TimesNewRoman', fontSize=11, leading=17,
    leftIndent=40, textColor=TEXT_PRIMARY,
)

styles['sop_header'] = ParagraphStyle(
    name='SOPHeader', fontName='TimesNewRoman-Bold', fontSize=11, leading=15,
    textColor=TEXT_MUTED, alignment=TA_LEFT, spaceAfter=2, spaceBefore=14,
)

styles['footer'] = ParagraphStyle(
    name='Footer', fontName='TimesNewRoman-Italic', fontSize=8, leading=12,
    textColor=TEXT_MUTED, alignment=TA_CENTER,
)

# ═══════════════════════════════════════════════════════════════
# TOC DocTemplate
# ═══════════════════════════════════════════════════════════════

class TocDocTemplate(SimpleDocTemplate):
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

def make_table(headers, rows, col_widths=None):
    """Create a styled table."""
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
        bg = TABLE_ROW_ODD if i % 2 == 0 else TABLE_ROW_EVEN
        style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(style_cmds))
    return t

def sop_section(sop_id, title, body_paras, subsections=None):
    """Create a standard SOP section with procedure ID, title, and numbered steps."""
    elements = []
    elements.append(add_heading('%s: %s' % (sop_id, title), styles['h1'], level=0))
    elements.append(hr())

    # Objective
    elements.append(Paragraph('<b>Objective:</b> %s' % body_paras[0], styles['body']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph('<b>Procedure:</b>', styles['body']))

    # Numbered steps
    for i, step in enumerate(body_paras[1:], 1):
        elements.append(numbered(i, step))

    if subsections:
        for sub_title, sub_rows in subsections:
            elements.append(Spacer(1, 8))
            elements.append(add_heading(sub_title, styles['h3'], level=2))
            elements.append(make_table(
                sub_rows[0],
                sub_rows[1:],
                [AVAILABLE_W / len(sub_rows[0])] * len(sub_rows[0])
            ))

    elements.append(Paragraph('<b>Output:</b> %s' % body_paras[-1], styles['body']))
    elements.append(Spacer(1, 10))
    return elements


# ═══════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ═══════════════════════════════════════════════════════════════

def build_body():
    output_path = os.path.join(os.path.dirname(__file__), 'SOP_Demand_Forecasting_ML_Development.pdf')
    doc = TocDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.7*inch, bottomMargin=0.7*inch,
        title='Standard Operating Procedure - Demand Forecasting ML Development',
        author='Mahesh Solanki',
    )

    story = []

    # ── DOCUMENT HEADER ──
    story.append(Paragraph('<b>STANDARD OPERATING PROCEDURE</b>', styles['sop_header']))
    story.append(Paragraph('Demand Forecasting ML Development Lifecycle', styles['title']))
    story.append(Paragraph(
        'Document Version: 3.0.0 | Effective Date: August 2026 | Owner: Data Science Team | Classification: Internal',
        styles['caption']
    ))
    story.append(hr())

    # ── TOC ──
    toc = TableOfContents()
    toc.levelStyles = [styles['toc1'], styles['toc2']]
    story.append(Paragraph('<b>Table of Contents</b>', ParagraphStyle(
        'TOCTitle', fontName='TimesNewRoman-Bold', fontSize=16, leading=22,
        textColor=ACCENT, alignment=TA_LEFT, spaceAfter=10
    )))
    story.append(toc)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # INTRODUCTION
    # ═══════════════════════════════════════════════════════
    story.append(add_heading('Introduction', styles['h1'], level=0))
    story.append(hr())
    story.append(Paragraph(
        'This Standard Operating Procedure (SOP) defines the end-to-end lifecycle for developing, '
        'deploying, and maintaining machine learning models for demand forecasting. It applies to '
        'all forecasting use cases including product demand, order volumes, energy consumption, '
        'and water/utility demand prediction. The SOP is aligned with the CRISP-DM methodology, '
        'extended with MLOps practices for production-grade ML systems.',
        styles['body']
    ))
    story.append(Paragraph(
        'All data scientists, ML engineers, data engineers, and DevOps personnel involved in '
        'demand forecasting projects must follow this SOP. Deviations require documented approval '
        'from the Data Science Team Lead.',
        styles['body']
    ))

    # SOP Overview table
    story.append(Spacer(1, 8))
    story.append(make_table(
        ['SOP ID', 'Phase', 'Owner', 'Duration (Typical)'],
        [
            ['SOP-01', 'Business Requirements & Use Case Definition', 'Product Manager + Data Science Lead', '1-2 weeks'],
            ['SOP-02', 'Data Collection & Engineering', 'Data Engineer', '2-4 weeks'],
            ['SOP-03', 'Feature Engineering', 'Data Scientist', '1-3 weeks'],
            ['SOP-04', 'Model Development', 'Data Scientist + ML Engineer', '2-6 weeks'],
            ['SOP-05', 'Model Evaluation & Validation', 'Data Scientist', '1-2 weeks'],
            ['SOP-06', 'Deployment & Integration', 'ML Engineer + DevOps', '1-3 weeks'],
            ['SOP-07', 'Monitoring & Continuous Improvement', 'ML Engineer + Data Scientist', 'Ongoing'],
            ['SOP-08', 'Governance & Compliance', 'Data Science Lead', 'Ongoing'],
            ['SOP-09', 'Tools & Technology Standards', 'Engineering Lead', 'Annual review'],
        ],
        [AVAILABLE_W * 0.12, AVAILABLE_W * 0.40, AVAILABLE_W * 0.28, AVAILABLE_W * 0.20]
    ))
    story.append(Paragraph('<i>Table 1: SOP document structure overview</i>', styles['caption']))

    # ═══════════════════════════════════════════════════════
    # SOP-01
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-01', 'Business Requirements & Use Case Definition', [
        'Align ML development with business objectives before any code is written.',
        'Identify the business problem: inventory optimization, capacity planning, procurement, or workforce scheduling. Document the specific pain point in measurable terms (e.g., "current stockout rate is 8.2%, target is <3%").',
        'Define forecast granularity. Determine the level at which predictions are needed: SKU-level, product-category, regional, or national. Note that finer granularity requires more data and model complexity.',
        'Determine forecast horizon. Classify as Short-term (1-7 days for operations), Medium-term (7-30 days for tactical planning), or Long-term (30-365 days for strategic decisions). Different horizons may require different models.',
        'Establish success KPIs. Set primary metric (wMAPE recommended for demand forecasting), acceptable threshold (typically < 15% wMAPE), bias tolerance (within +/-5%), and business KPIs (inventory reduction %, service level %).',
        'Identify stakeholders and their needs: Planners need daily forecasts with drill-down capability; Supply Chain Managers need weekly aggregated views with confidence intervals; Finance needs monthly revenue-impact projections; Executives need KPI dashboards.',
        'Document data sources and availability. Create a Data Source Inventory listing each system, data type, historical range available, update frequency, and access method (API, database, file export).',
        'Define acceptable latency for predictions. Real-time scoring (< 500ms per prediction) for operational use cases; batch scoring (< 30 minutes for full dataset) for planning use cases.',
        'Create a Business Requirements Document (BRD) containing all above artifacts. Obtain sign-off from all stakeholders before proceeding to SOP-02.',
        'Signed BRD with stakeholder approvals, KPI baseline measurements, Data Source Inventory, and Stakeholder Map (RACI matrix).',
    ]))

    # ═══════════════════════════════════════════════════════
    # SOP-02
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-02', 'Data Collection & Engineering', [
        'Build a reliable, versioned data pipeline that feeds all downstream forecasting models.',
        'Inventory data sources from the BRD. Categorize as: (a) Historical demand/sales — minimum 2-3 years for seasonal pattern capture; (b) Product metadata — category, lifecycle stage, unit price, unit cost, lead time; (c) External data — weather (temperature, precipitation, HDD/CDD), holidays, economic indicators, competitor pricing indices; (d) Real-time streaming sources — IoT meters, POS systems, ERP transaction logs, SCADA readings.',
        'Assess data quality for each source. Completeness: require >95% for model training features; flag sources below threshold. Outlier detection: apply IQR method (1.5x IQR beyond Q1/Q3) and z-score method (|z| > 3). Missing value analysis: classify as MCAR (Missing Completely At Random), MAR (Missing At Random), or MNAR (Missing Not At Random). Document pattern and planned imputation strategy.',
        'Construct the ETL/ELT pipeline using Apache Airflow or Prefect. Each pipeline must include: extraction task, validation task (Great Expectations suite), transformation task, loading task, and notification task (Slack/email on failure).',
        'Implement data versioning. Use DVC for dataset versioning with remote storage (S3/MinIO). Every dataset used for model training must have a unique version tag. Alternatively, use Delta Lake for ACID-compliant versioned data lakes.',
        'Perform the train/validation/test split. Use time-based splitting (NEVER random for time series). Standard ratio: 60% train, 20% validation, 20% test. For backtesting, use rolling-origin with expanding or rolling windows of configurable size.',
        'Generate automated Data Quality Report covering: completeness percentages per feature, outlier counts and bounds, missing value patterns, timestamp consistency check, and distribution comparison (train vs. validation vs. test).',
        'Data Quality Report (PDF/HTML), versioned datasets in DVC/Delta Lake with metadata, Airflow/Prefect pipeline DAG definition, and Great Expectations validation suite.',
    ]))

    # ═══════════════════════════════════════════════════════
    # SOP-03
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-03', 'Feature Engineering', [
        'Transform raw data into predictive features that capture temporal patterns, external influences, and domain-specific signals.',
        'Create temporal features: (a) Lag features: t-1, t-2, t-3, t-7, t-14, t-30, t-90, t-365; (b) Rolling statistics over configurable windows: 7-day mean/std/min/max, 30-day mean/std, 90-day trend slope; (c) Calendar features: day of week (0-6), month (1-12), quarter, is_weekend, is_month_start, is_month_end; (d) Cyclical encodings using sin/cos transformations: day_of_week_sin, day_of_week_cos, month_sin, month_cos.',
        'Create weather/climate features: Heating Degree Days (HDD = max(0, 18°C - avg_temp)), Cooling Degree Days (CDD = max(0, avg_temp - 18°C)), daily precipitation, cumulative 7-day and 30-day precipitation, temperature range (max - min), and extreme event flags (heatwave: temp > 95th percentile for 3+ consecutive days; cold snap: temp < 5th percentile for 3+ days).',
        'Create domain features: price and promotion indicators (discount %, promotion type, days since last promotion), product lifecycle stage (ramp-up, maturity, decline — derived from launch date), inventory level flags (stockout indicator, days of supply remaining), and competitor activity indices where available.',
        'Create cluster features for demand pattern segmentation: ADI (Average Demand Interval) for intermittency classification, CV-squared (coefficient of variation squared) for dispersion, seasonality strength index (ratio of seasonal variance to total variance), and revenue tier (A/B/C based on cumulative revenue contribution).',
        'Validate feature quality: (a) Compute SHAP values and permutation feature importance; (b) Build correlation matrix and flag any feature pair with |r| > 0.95 for removal; (c) Calculate Population Stability Index (PSI) between train and test sets — flag features with PSI > 0.25 for investigation.',
        'Feature metadata document listing all features with descriptions, Feature Importance Report (SHAP summary plot + top-20 table), Feature Correlation Matrix heatmap, and updated Feature Store (Feast) with all computed features registered.',
    ]))

    # ═══════════════════════════════════════════════════════
    # SOP-04
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-04', 'Model Development', [
        'Train, tune, and select the best-performing model(s) using a systematic, reproducible approach.',
        'Establish baselines first (MANDATORY — never skip). Implement and evaluate: (a) Naive forecast: use last observed value; (b) Seasonal naive: use value from same period last season; (c) Simple exponential smoothing; (d) Historical average by day-of-week. Document baseline metrics as the minimum bar for any ML model.',
        'Train statistical models: SARIMA/SARIMAX with exogenous regressors using auto_arima for order selection; ETS (Error-Trend-Seasonality) with additive or multiplicative components; Croston\'s method for intermittent demand items (ADI > 1.32).',
        'Train machine learning models: LightGBM and XGBoost gradient boosting with the full feature set. CRITICAL: ML models do not capture trend inherently — you must include trend features (cumulative time index, rolling trend slope). Use time-based cross-validation with expanding windows.',
        'Train deep learning models (CNN-LSTM): Implement the reference architecture (Conv1D 64/128 filters -> MaxPool -> BiLSTM 128/64 units -> Dense). Use Adam optimizer (lr=0.001), ReduceLROnPlateau (factor=0.5, patience=10), EarlyStopping (patience=20). Regularization: Dropout(0.3) between CNN and LSTM layers, L2 regularization on Dense layers.',
        'Build ensemble: Combine models using (a) simple average of all model predictions; (b) weighted average with weights inversely proportional to validation MAPE; (c) stacking with a meta-learner (Linear Regression or LightGBM) trained on out-of-fold predictions; (d) horizon-aware weights where different models get different weights depending on forecast step.',
        'Tune hyperparameters using Optuna (Bayesian optimization) or Hyperopt. Define search spaces for each model. Use TimeSeriesSplit for cross-validation. Track ALL experiments in MLflow with: parameters, metrics, artifacts (model files, feature importance plots), tags (model type, data version), and git commit hash.',
        'All trained models registered in MLflow Model Registry, Experiment Comparison Report showing metrics vs. baseline, hyperparameter importance analysis, and Model Card for the selected model(s).',
    ]))

    # ═══════════════════════════════════════════════════════
    # SOP-05
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-05', 'Model Evaluation & Validation', [
        'Rigorously evaluate model performance using statistical metrics and business impact analysis before deployment approval.',
        'Compute point forecast metrics on the held-out test set: MAE (unit-level error magnitude), RMSE (penalizes large errors), MAPE (percentage interpretability), sMAPE (symmetric, bounded 0-200%), wMAPE (revenue/cost-weighted — PRIMARY METRIC), MASE (scale-independent, compare to naive baseline).',
        'Perform bias analysis: (a) Mean Percentage Error (MPE) — should be near zero; deviations indicate systematic over/under-forecasting; (b) Over-forecast vs. under-forecast ratio — significant asymmetry indicates model bias; (c) Bias decomposition by product category, season, volume tier, and region — identify segments where model underperforms.',
        'Quantify business impact: (a) Simulate inventory holding cost using forecast vs. actual (holding cost per unit x excess inventory from over-forecast); (b) Assess stockout risk (lost sales from under-forecast x contribution margin per unit); (c) Calculate service level attainment (% of demand periods where inventory covered forecast demand).',
        'Run statistical validation tests: (a) Diebold-Mariano test for pairwise model comparison (is Model A significantly better than Model B?); (b) Residual diagnostics: normality test (Jarque-Bera), autocorrelation test (Ljung-Box on residuals), heteroscedasticity test (Breusch-Pagan); (c) Prediction interval coverage: check that actual values fall within the predicted interval at the nominal confidence level (e.g., 95% of actuals within 95% PI).',
        'Conduct stakeholder review: Present results to business stakeholders in a structured review meeting. Compare against current manual/existing forecasts. Document model limitations (edge cases where performance degrades) and known failure modes. Obtain formal sign-off before proceeding to deployment.',
        'Model Evaluation Report (PDF) with all metrics, bias analysis, and business impact simulation; Diebold-Mariano test results; Stakeholder sign-off form (wet signature or digital approval in MLflow); and updated Model Card with evaluation results.',
    ]))

    # ═══════════════════════════════════════════════════════
    # SOP-06
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-06', 'Deployment & Integration', [
        'Deploy models to production with reliability, reproducibility, and zero-downtime rollback capability.',
        'Package the model: (a) Classical ML models (LightGBM, Prophet) — serialize with joblib (preferred) or pickle, include feature names and preprocessing pipeline; (b) Deep learning models (CNN-LSTM) — export to TorchScript or ONNX format for language-agnostic serving; (c) Containerize the model and API code using Docker with a pinned base image and all dependencies version-locked.',
        'Develop the serving API using FastAPI: implement POST endpoints for single and batch prediction; validate inputs with Pydantic models (type checking, range validation); add rate limiting (e.g., 100 requests/second per client); implement API key authentication; include health check endpoint (/health) for load balancer probing.',
        'Integrate with downstream systems: (a) ERP connectors (SAP BAPI/RFC, Oracle REST API) for direct forecast injection into planning modules; (b) BI tool connectors (Power BI REST API, Tableau Web Data Connector) for dashboard data refresh; (c) Streaming platforms (Kafka producer for real-time forecast publishing to event-driven architectures).',
        'Execute deployment strategy: (a) Canary deployment: route 5% traffic to new model -> monitor for 24 hours -> increase to 25% -> monitor 24 hours -> 100%; (b) Blue-green deployment: maintain two identical production environments, switch traffic instantly, keep previous version warm for 1 hour for instant rollback; (c) Maintain rollback runbook with step-by-step instructions for reverting to previous model version.',
        'Perform post-deployment verification: (a) Smoke tests on all API endpoints with known inputs and expected outputs; (b) Latency validation: single prediction < 500ms (P99), batch of 1000 < 30 seconds; (c) Verify logging pipeline: all predictions logged with model version, input features, prediction, and timestamp; (d) Verify monitoring dashboards show live data.',
        'Deployed API (Docker image in container registry), Integration Test Report (automated test suite passing), Production Runbook (deployment steps, rollback procedure, contact list), and monitoring dashboard URLs with alerts configured.',
    ]))

    # ═══════════════════════════════════════════════════════
    # SOP-07
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-07', 'Monitoring & Continuous Improvement', [
        'Maintain model health in production and drive ongoing performance improvement through systematic monitoring.',
        'Implement daily performance monitoring: (a) Forecast vs. actual tracking — compute MAPE, wMAPE, and bias for each forecast horizon (t+1, t+7, t+30) daily; (b) Prediction latency and throughput — track P50, P95, P99 latency and requests/second; (c) Error rate and availability — track HTTP 5xx rate and uptime % (target: 99.9%).',
        'Implement weekly drift detection: (a) Data drift — compute PSI on all input features weekly; flag any feature with PSI > 0.25 for investigation by the data science team; (b) Concept drift — track rolling 30-day MAPE; if MAPE increases by >20% from the validation baseline, trigger investigation; (c) Target drift — compare actual demand distribution (mean, variance, quantiles) against training distribution using Kolmogorov-Smirnov test.',
        'Configure retraining triggers: (a) Scheduled trigger: monthly retraining with the latest data (default cadence); (b) Performance trigger: rolling MAPE exceeds threshold (baseline + 20%); (c) Drift trigger: PSI > 0.25 on any top-10 feature OR concept drift detected via residual trend analysis; (d) Event trigger: major market change, new product launch, competitor entry, regulatory change.',
        'Manage model lifecycle: (a) Archive models older than 2 retraining cycles from the active registry (move to archive with metadata preserved); (b) Maintain champion/challenger pipeline — always have at least one challenger model in shadow mode receiving production traffic; (c) Conduct quarterly model review meeting with stakeholders — present performance trends, drift analysis, and improvement proposals.',
        'Operate the feedback loop: (a) Log all planner overrides (manual forecast adjustments) with reason codes; (b) Perform monthly root cause analysis on the top-10 largest forecast errors; (c) Maintain a prioritized improvement backlog with feature requests, bug fixes, and enhancement proposals.',
        'Monthly Model Health Report (automated PDF generation from monitoring dashboards), Retraining Log (dates, triggers, data versions, metrics before/after), Quarterly Stakeholder Review presentation, and Prioritized Improvement Backlog in project management tool.',
    ]))

    # ═══════════════════════════════════════════════════════
    # SOP-08
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-08', 'Governance & Compliance', [
        'Ensure responsible, auditable, and compliant ML operations throughout the model lifecycle.',
        'Maintain model documentation (per model): (a) Model Card — purpose, intended use, training data summary, features used, performance metrics, limitations, ethical considerations, and out-of-scope use cases; (b) Training Run Log — date, data snapshot version, hyperparameters, metrics, and approver; (c) Deployment Log — deployment date, version deployed, approver, rollback plan reference.',
        'Implement access control: (a) Role-Based Access Control (RBAC) for MLflow Model Registry — Data Scientists: read/write staging; ML Engineers: promote to production; Managers: approve transitions; (b) Production deployment requires two-person approval (4-eyes principle); (c) All prediction API access logged with client ID, timestamp, and request metadata.',
        'Check for bias and fairness: (a) Analyze forecast error by region, product category, and customer segment quarterly; (b) If systematic bias > 10% MAPE difference between any two segments, initiate bias investigation; (c) Document any known biases and mitigations in the Model Card.',
        'Ensure business continuity: (a) Maintain fallback model — a simpler, proven statistical model (e.g., seasonal exponential smoothing) that can be activated if the primary model fails; (b) Manual override capability — planners must be able to adjust forecasts in the BI dashboard with audit trail; (c) Disaster recovery plan — documented procedures for restoring ML infrastructure from backups, including model artifacts, feature store, and training data.',
        'Conduct annual compliance audit: Review all active models against this SOP, update Model Cards, verify access controls, test disaster recovery procedures, and document findings in an Audit Report.',
        'Model Cards for all production models, Audit Trail (MLflow + custom logging), Annual Compliance Audit Report, and Business Continuity Plan (tested annually).',
    ]))

    # ═══════════════════════════════════════════════════════
    # SOP-09
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-09', 'Tools & Technology Standards', [
        'Define the standard technology stack for demand forecasting ML development to ensure consistency, maintainability, and team efficiency.',
        'Adopt the following standard tools. Deviations require written justification and Engineering Lead approval.',
    ], [
        ('Tool Standards', [
            ['Capability', 'Standard Tool', 'Alternative (with approval)'],
            ['Experiment Tracking', 'MLflow', 'Weights & Biases'],
            ['Feature Store', 'Feast', 'Tecton'],
            ['Data Versioning', 'DVC', 'Delta Lake'],
            ['Pipeline Orchestration', 'Apache Airflow', 'Prefect, Dagster'],
            ['Model Serving', 'FastAPI + Docker', 'BentoML, Seldon Core'],
            ['Drift Monitoring', 'Evidently AI + Grafana', 'WhyLogs, NannyML'],
            ['CI/CD', 'GitHub Actions', 'GitLab CI, Jenkins'],
            ['Data Quality', 'Great Expectations', 'Soda, Deequ'],
            ['Deep Learning Framework', 'PyTorch', 'TensorFlow / Keras'],
            ['BI/Dashboard', 'Streamlit + Power BI', 'Tableau, Looker'],
            ['Container Orchestration', 'Kubernetes', 'Docker Swarm (small deployments)'],
            ['Secrets Management', 'HashiCorp Vault', 'AWS Secrets Manager, Azure Key Vault'],
            ['Code Quality', 'Ruff + Black', 'pylint + flake8'],
            ['Streaming Platform', 'Apache Kafka', 'Redpanda, RabbitMQ'],
            ['Caching / Session Store', 'Redis', 'Memcached'],
            ['Monitoring Dashboards', 'Grafana', 'Datadog, New Relic'],
            ['Real-time Communication', 'WebSocket (FastAPI)', 'SSE (Server-Sent Events)'],
            ['Local Orchestration', 'Docker Compose', 'Podman Compose'],
        ]),
    ]))

    # ═══════════════════════════════════════════════════════
    # SOP-10
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-10', 'Streaming Data Ingestion & Real-Time Processing', [
        'Define procedures for ingesting, validating, and processing real-time demand data streams.',
        'Configure Kafka topics per data source (sales.events, inventory.updates, external.weather, external.promotions) with appropriate partition counts based on throughput.',
        'Implement schema validation using Avro/JSON Schema in the Kafka producer. Reject malformed messages to a dead-letter queue (DLQ) topic.',
        'Deploy the aiokafka consumer as a FastAPI lifespan background task with batch upserts (100 records or 5-second flush) to the actuals table.',
        'Configure idempotent producers (enable_idempotence=True) and manual commits (enable_auto_commit=False) for exactly-once semantics.',
        'Monitor consumer lag using Kafka\'s built-in metrics. Alert when lag exceeds 1000 messages or 60 seconds.',
        'Test the full stream end-to-end: produce test events, verify they appear in the actuals table within 10 seconds.',
        'Streaming topology document, topic registry, consumer lag monitoring dashboard.',
    ]))

    # ═══════════════════════════════════════════════════════
    # SOP-11
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(sop_section('SOP-11', 'Production Monitoring & Observability', [
        'Maintain full observability of ML models and infrastructure in production.',
        'Deploy Grafana dashboards (demand-overview, forecast-accuracy, model-health) via docker-compose provisioning. Verify all panels render with live data.',
        'Configure Evidently AI drift checks via APScheduler (daily at 06:00). Store results in drift_metrics table and auto-create alerts for detected drift.',
        'Set up WebSocket heartbeat (30-second interval) for real-time dashboard connections. Monitor active connection count.',
        'Enable Redis caching for dashboard API endpoints with configurable TTL. Monitor cache hit rate — target >80%.',
        'Configure multi-tenant isolation: verify tenant_id is propagated through all queries. Test cross-tenant data isolation by querying as different tenants.',
        'Review monitoring dashboards weekly: check for accuracy degradation, drift patterns, and resource utilization trends.',
        'Operational runbook, monitoring dashboard URLs, alert escalation matrix.',
    ]))

    # ═══════════════════════════════════════════════════════
    # APPENDIX A: FORECAST ACCURACY METRICS
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(add_heading('Appendix A: Forecast Accuracy Metrics Quick Reference', styles['h1'], level=0))
    story.append(hr())

    story.append(make_table(
        ['Metric', 'Formula', 'Range', 'Best For'],
        [
            ['MAE', 'mean(|actual - forecast|)', '[0, inf)', 'General comparison, same units as data'],
            ['RMSE', 'sqrt(mean((actual - forecast) squared))', '[0, inf)', 'Penalizing large errors heavily'],
            ['MAPE', 'mean(|actual - forecast| / |actual|) x 100', '[0, inf)%', 'Percentage interpretability'],
            ['sMAPE', 'mean(2|actual - forecast| / (|actual| + |forecast|)) x 100', '[0, 200]%', 'Symmetric, bounded'],
            ['wMAPE', 'sum(|actual - forecast|) / sum(|actual|)', '[0, inf)', 'Revenue/cost-weighted accuracy (PRIMARY)'],
            ['MASE', 'MAE_model / MAE_naive', '[0, inf)', 'Scale-independent, compare to naive'],
            ['Pinball Loss', 'mean(max(q(y-y_hat), (q-1)(y-y_hat)))', '[0, inf)', 'Quantile/probabilistic forecasts'],
            ['MPE', 'mean((actual - forecast) / actual) x 100', '(-inf, inf)', 'Bias direction detection'],
        ],
        [AVAILABLE_W * 0.10, AVAILABLE_W * 0.38, AVAILABLE_W * 0.14, AVAILABLE_W * 0.38]
    ))
    story.append(Paragraph('<i>Table A.1: Standard forecast accuracy metrics</i>', styles['caption']))

    story.append(Spacer(1, 10))
    story.append(Paragraph('<b>Metric Selection Guidelines:</b>', styles['body']))
    story.append(bullet('Use <b>wMAPE</b> as the primary metric when forecasts drive financial decisions (inventory, procurement) — it weights errors by volume/revenue impact.'))
    story.append(bullet('Use <b>MASE</b> when comparing models across different products with different demand scales.'))
    story.append(bullet('Use <b>Pinball Loss</b> when evaluating probabilistic forecasts (prediction intervals, quantile regression).'))
    story.append(bullet('Always report <b>MPE</b> alongside accuracy metrics to detect systematic bias.'))
    story.append(bullet('Never use <b>MAPE</b> when actual values can be zero or near-zero (intermittent demand) — use sMAPE or MASE instead.'))

    # ═══════════════════════════════════════════════════════
    # APPENDIX B: CNN-LSTM REFERENCE
    # ═══════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(add_heading('Appendix B: CNN-BiLSTM Architecture Reference', styles['h1'], level=0))
    story.append(hr())

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
    story.append(Paragraph('<b>Training Configuration Reference:</b>', styles['body']))
    story.append(make_table(
        ['Hyperparameter', 'Default Value', 'Search Range', 'Notes'],
        [
            ['Learning Rate', '0.001', '[1e-4, 1e-2] log-uniform', 'Adam optimizer'],
            ['Batch Size', '64', '[16, 32, 64, 128, 256]', 'Scale based on GPU memory'],
            ['Sequence Length', '60 days', '[30, 60, 90, 180, 365]', 'Match forecast horizon'],
            ['Conv Filters (Layer 1)', '64', '[32, 64, 128]', 'First conv layer'],
            ['Conv Filters (Layer 2)', '128', '[64, 128, 256]', 'Second conv layer'],
            ['LSTM Units (Layer 1)', '128', '[64, 128, 256]', 'First BiLSTM layer'],
            ['LSTM Units (Layer 2)', '64', '[32, 64, 128]', 'Second BiLSTM layer'],
            ['Dropout Rate', '0.3', '[0.1, 0.2, 0.3, 0.4, 0.5]', 'After CNN and LSTM blocks'],
            ['L2 Regularization', '1e-4', '[1e-5, 1e-3] log-uniform', 'On Dense layers'],
            ['ReduceLROnPlateau Factor', '0.5', 'Fixed', 'Patience: 10 epochs'],
            ['EarlyStopping Patience', '20', 'Fixed', 'Restore best weights: True'],
        ],
        [AVAILABLE_W * 0.22, AVAILABLE_W * 0.18, AVAILABLE_W * 0.25, AVAILABLE_W * 0.35]
    ))

    # ── FOOTER ──
    story.append(Spacer(1, 20))
    story.append(hr())
    story.append(Paragraph(
        '<i>End of Document | SOP Version 3.0.0 | August 2026 | '
        'Next Review Date: February 2027 | Document Owner: Data Science Team Lead</i>',
        styles['footer']
    ))

    # ── Build ──
    doc.multiBuild(story)
    print(f'[DONE] Body PDF: {output_path}')
    return output_path

if __name__ == '__main__':
    build_body()
