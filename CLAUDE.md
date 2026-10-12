# CLAUDE.md — Project Guidelines & Implementation Preferences

**Project:** Ukrainian Air Raid Alerts Time Series Analysis  
**Last Updated:** 2026-10-11  
**Status:** Research Complete — Ready for Implementation Phase  
**Scope:** MVP (Minimum Viable Product)

---

## PROJECT OVERVIEW

Build a reproducible Python pipeline to analyze and forecast temporal patterns in Ukrainian air raid alerts using open-source time series data and machine learning techniques.

**Type:** Real-world defense analysis using publicly available OSINT data  
**Target Users:** Researchers, data analysts, defensive intelligence professionals  
**Timeline:** 8-12 weeks (MVP)  
**Team:** 1 senior data scientist (or equivalent)  
**Budget:** $25K-$50K (MVP)

---

## CORE CONSTRAINTS & NON-NEGOTIABLES

### 1. Data Leakage Prevention (CRITICAL)
- ✅ **MUST:** All training data strictly before forecast point
- ✅ **MUST:** No future data leakage in features
- ✅ **MUST:** Test set separated from training set
- ✅ **MUST:** External sources (news, Telegram, etc.) timestamped before forecast point
- **Rationale:** Military data is time-sensitive; any leakage invalidates operational value

### 2. Open-Source Data Only
- ✅ All data sources must be publicly accessible
- ✅ No proprietary or classified data
- ✅ License compliance required (document any restrictions)

### 3. No Data Fabrication
- ❌ Do NOT use synthetic/inferred data for ground truth
- ⚠️ If using inferred data (e.g., Kaggle's 30% inferred end times), document explicitly as feature
- **Rationale:** Military analysis requires verifiable ground truth

### 4. Reproducibility First
- ✅ `python run_pipeline.py` must work from scratch
- ✅ All external data sources versioned or timestamped
- ✅ Environment fully specified in requirements.txt
- ✅ No hardcoded credentials or API keys

---

## MVP SCOPE (PRIMARY FOCUS)

### Data Sources (3 Primary)
1. **Vadimkin/ukrainian-air-raid-sirens-dataset** (GitHub)
   - URL: https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset
   - Format: CSV, 299K+ records
   - Coverage: 2022-02-24 to 2026-09-07 (+ volunteer data ongoing)
   - License: MIT (commercial-friendly)

2. **Kaggle — Air Alerts in Ukraine (p0stscriptum)**
   - URL: https://www.kaggle.com/datasets/p0stscriptum/air-raid-dataset
   - Format: CSV, daily updates
   - Coverage: Feb 25, 2022 to present
   - License: CC-BY-NC-SA 4.0 (non-commercial; use Vadimkin for commercial projects)
   - Note: ~30% have inferred end times; include 'inferred_flag' in models

3. **alerts.in.ua API** (Ukrainian Air Force Official)
   - URL: https://devs.alerts.in.ua/
   - Format: JSON REST API, real-time
   - Coverage: Real-time + historical (unclear depth)
   - License: Not specified
   - Auth: API token required
   - Rate Limit: 8-10 requests/minute (sufficient for real-time monitoring at 2-5 req/min)

### Success Criteria (MVP)
- [ ] Weekly WAPE (primary): candidates must beat the trailing four-week mean baseline (8.52%) on rolling-origin backtest. NOT MET: no candidate beat it; baseline accepted as the deliverable under T1. Daily WAPE secondary. (approved 2026-10-12, see docs/gate2_decisions.md, docs/gate3_results.md)
- [ ] 80%/95% interval coverage within 77–83% / 93–97% (approved metric, see docs/gate2_decisions.md)
- [ ] Real-time monitoring latency < 5 minutes
- [ ] Code reproducible with `python run_pipeline.py`
- [ ] README + requirements.txt + run_pipeline.py complete
- [ ] All external sources timestamped before forecast point

---

## ENTERPRISE SCOPE (OPTIONAL EXPANSION)

### Additional Sources (6 More)
4. **ISW** (Institute for the Study of War) — Academic analysis
5. **Oryx** — Equipment loss tracking
6. **Ukrainian Air Force Telegram (@kpszsu)** — Official confirmations
7. **ACLED** — Conflict events database (verify freshness)
8. **Kaggle — Massive Missile Attacks** — Supplementary strike data
9. **Texty.org.ua** — Data journalism (reference only)

### Enterprise Timeline & Cost
- Timeline: 6-7 months
- Team: 4 engineers
- Cost: $200K-$340K
- **Decision Point:** Implement MVP first, evaluate at 12-week gate before Enterprise expansion

---

## CRITICAL BLOCKERS (MUST VERIFY BEFORE CODING)

### 1. Vadimkin GitHub Status (HIGH PRIORITY)
- **What:** Verify volunteer feed is active after official stopped Sept 7, 2026
- **Why:** If lost, lose 299K historical alerts
- **Action:** Check GitHub last commit date, verify volunteer maintenance ongoing
- **Resolution Time:** 5-10 minutes
- **Gate:** MUST resolve before download stage

### 2. ACLED Data Currency (HIGH PRIORITY)
- **What:** Verify ACLED data updated beyond May 2025
- **Why:** If outdated >6 months, cannot use for validation
- **Action:** Check acleddata.com for Ukraine data update date
- **Resolution Time:** 5 minutes
- **Gate:** MUST resolve before using ACLED in validation stage

---

## KEY FINDINGS FROM RESEARCH PHASE

### What Was Validated ✅
- All 9 primary data sources verified as active
- Two strong MVP datasets (Vadimkin + Kaggle)
- Multiple ground truth sources available for validation
- Rate limits NOT a bottleneck for real-time ops

### What Was Corrected 🔧
- **Original Plan Error:** Used ARIMA/Prophet for sparse military data
- **Correction:** Use ARIMA/Prophet IF EDA shows autocorrelation; otherwise Poisson/negative binomial
- **Impact:** Prevents producing operationally misleading forecasts

### What Needs Documenting 📋
- Data quality scorecard (% real vs. inferred per source)
- License compliance path (Vadimkin for commercial, document Kaggle non-commercial restriction)
- Timezone consistency (ensure all UTC or documented conversions)
- Data leakage prevention checklist

---

## IMPLEMENTATION PREFERENCES

### Architecture Approach
- **Modular design:** Separate data acquisition, preprocessing, features, modeling, forecasting
- **Single entry point:** `python run_pipeline.py` orchestrates all stages
- **Fail-fast validation:** Check data quality at each stage before proceeding
- **Version control:** Git commits after each major stage (data ✓, preprocess ✓, features ✓, model ✓, forecast ✓)

### Code Style & Quality
- Python 3.10+
- Type hints preferred but not required
- Docstrings for public functions
- No heavy abstractions until 3+ similar implementations exist
- Prefer pandas/sklearn over custom implementations
- Log progress with clear print statements (not silent failures)

### Testing Strategy
- Test each stage independently (data_loader, preprocessing, features, model)
- No need for unit tests on one-off operations
- Validate against known ground truth (ISW reports, Telegram, Oryx) if available

### Documentation
- README.md covers: what it does, how to install, how to run, how to extend
- RESEARCH_FINDINGS_MASTER.md documents data sources and limitations
- Inline comments only for WHY, not WHAT (code should be self-explanatory)
- AI interaction log captures methodology and decisions

---

## WHAT NOT TO DO ❌

### Premature Optimization
- ❌ Do NOT over-engineer for 9 sources before MVP works with 3
- ❌ Do NOT build real-time dashboard before model works
- ❌ Do NOT add fault-tolerance before core pipeline runs

### False Generalization
- ❌ Do NOT assume patterns in data without EDA
- ❌ Do NOT use synthetic data as ground truth
- ❌ Do NOT claim 30-day forecast accuracy without proper backtesting

### Scope Creep
- ❌ Do NOT add neural networks before baseline models work
- ❌ Do NOT integrate all 9 sources; focus on 3 for MVP
- ❌ Do NOT over-document features that don't improve performance

---

## DECISION GATES (Go/No-Go Checkpoints)

### Gate 1: Data Verification (Week 1)
- [ ] Vadimkin feed status confirmed
- [ ] ACLED freshness verified
- [ ] alerts.in.ua API token obtained
- [ ] First 1000 rows downloaded and inspected
**Gate Outcome:** Go forward or pivot data sources?

### Gate 2: EDA Complete (Week 2-3)
- [ ] Stationarity tests (ADF)
- [ ] Autocorrelation analysis (ACF/PACF)
- [ ] Sparsity assessment (% zero-alert days)
- [ ] Model selection rationale documented
**Gate Outcome:** Proceed with chosen model(s)?

### Gate 3: Model Baseline (Week 4-6)
- [ ] Baseline model trained and validated
- [ ] RMSE/MAE metrics calculated
- [ ] Ensemble approach if multiple models
**Gate Outcome:** Performance acceptable or need different approach?

### Gate 4: MVP Complete (Week 8-10)
- [ ] Pipeline end-to-end working
- [ ] README complete
- [ ] requirements.txt pinned
- [ ] All success criteria met
**Gate Outcome:** Ready for GitHub submission?

### Gate 5: Enterprise Decision (Week 12)
- [ ] Evaluate MVP performance
- [ ] MVP success criteria met?
- [ ] Decision: Ship MVP or expand to Enterprise?

---

## MULTI-AGENT ORCHESTRATION & MODEL TIERING

### Architecture Overview
**Orchestrator-Worker Pattern** for maximum engineering rigor and token efficiency:

1. **Lead Orchestrator (Master Controller)**
   - Model: Flagship Reasoning (Sonnet/Opus-tier)
   - Responsibilities:
     - High-level architecture governance & milestone tracking
     - Task decomposition → specialized subagents with scoped work orders
     - PR/diff review & output quality verification
     - Global token consumption supervision

2. **Specialized Engineer Subagents (Dynamic Model Routing)**
   - **Tier A: Fast/Lightweight (Haiku)**
     - Repetitive data ingestion scripts
     - Regex parsers & text processing
     - Unit test generation & boilerplate code
     - Lint fixes & telemetry extractors
     - Simple documentation
   
   - **Tier B: Balanced/Deep Engineering (Sonnet)**
     - Core ML architectures (ZINB, Hawkes, ensemble stacking)
     - Mathematical loss functions & optimization
     - Database concurrency & geospatial indexing (H3)
     - Cross-system integration & complex state management

### Token Optimization Rules
1. **Principle of Least Context**
   - Never pass entire codebase to subagents
   - Extract only relevant functions, schemas, minimal context slice needed
   - Include file paths, line numbers for quick navigation

2. **Concise Technical Output**
   - Strict diffs only, zero conversational filler
   - Technical bullets, no greetings or redundant explanations
   - Output = code + tests + brief verification statement

3. **Incremental Validation**
   - Subagents write modular code with immediate unit tests
   - Orchestrator validates tests before dispatching next agent
   - No code merges until quality gates pass

---

## COLLABORATION PREFERENCES

### How Claude Should Work With You
- **Direct approach:** Tell me what to do, don't ask permission repeatedly
- **Show work:** Include code snippets, actual commands, expected output
- **Fail fast:** If something doesn't work, try alternative before long explanation
- **Scope clarity:** Tell me MVP vs. Enterprise upfront; focus on MVP unless told otherwise
- **Documentation:** Prioritize working code over perfect comments
- **Timestamps:** Include timestamps in logs for traceability

### Decision Authority
- **You decide:** Project scope, which data sources, forecast horizon, success thresholds
- **Claude decides:** Implementation details, code structure, model selection (given EDA results)
- **Together:** If fundamental assumptions are wrong (e.g., data not available)

### Red Flags (Stop and Ask)
- ❌ If data source URL returns 404 or changes format
- ❌ If rate limits are actually exceeded
- ❌ If foundational assumptions (no data leakage) are violated
- ❌ If budget/timeline estimate needs revision by >25%

---

## REFERENCES & RESOURCES

### Project Documentation
- `README.md` — User-facing project documentation
- `RESEARCH_FINDINGS_MASTER.md` — Complete data source audit (4,500+ words)
- `DATA_SOURCES_REFERENCE.json` — Structured metadata (machine-readable)
- `CONVERSATION_SUMMARY.md` — Research methodology & timeline
- `AI_INTERACTION_LOG.txt` — Full conversation history
- `CLAUDE.md` — This file (implementation guidelines)

### Data Sources
- Vadimkin GitHub: https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset
- Kaggle: https://www.kaggle.com/datasets/p0stscriptum/air-raid-dataset
- alerts.in.ua: https://devs.alerts.in.ua/

### Key Research Findings
- **Viability:** 75-85% for MVP
- **Cost:** $25K-$50K for MVP
- **Timeline:** 8-12 weeks for MVP
- **Critical Issues:** 2 blockers (Vadimkin status, ACLED currency)
- **Model Choice:** ARIMA/Prophet IF autocorrelation present; Poisson otherwise

---

## NEXT STEPS (READY TO IMPLEMENT)

1. ✅ Verify blockers (Vadimkin, ACLED) — 10 minutes
2. ✅ Obtain alerts.in.ua API token — 5 minutes  
3. ✅ GitHub repository initialization
4. ✅ Data download & initial EDA — 2 hours
5. ✅ Pipeline development (preprocess → features → model)
6. ✅ Model training & validation
7. ✅ Final packaging & README

**Ready to proceed?** Type `yes` and I'll start with data verification.

---

**Document Version:** 1.0  
**Last Updated:** 2026-10-11  
**Status:** Ready for Implementation
