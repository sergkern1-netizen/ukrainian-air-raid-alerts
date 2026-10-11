# Quick-Reference Implementation Checklist

**Primary Document:** `UKRAINIAN_AIR_RAID_ALERTS_RESEARCH_v2.0.md`  
**Decision Record:** `ARBITRATION_SUMMARY.md`

---

## Pre-Implementation: Critical Verifications

### BLOCKER 1: ACLED Data Freshness (MUST COMPLETE FIRST)
- [ ] Visit https://acleddata.com
- [ ] Check "Latest Update" date
- [ ] **IF Oct 2026 or later:**
  - [ ] Update v2.0 doc Section II with current date
  - [ ] Proceed to Phase 1
- [ ] **IF May 2025 or earlier:**
  - [ ] Document: "ACLED historical-only (Feb 2022 – May 2025)"
  - [ ] Use alerts.in.ua + ISW for May 2025 – Oct 2026 coverage
  - [ ] Proceed to Phase 1

**Owner:** Data Engineer | **Estimated Time:** 5 minutes | **Criticality:** BLOCKING

---

## Phase 1: Foundation (Weeks 1-2)

### Data Setup
- [ ] Clone Vadimkin repository
  - Command: `git clone https://github.com/Viacheslav-Vadimovych/air_alarm_analysis_public`
  - Validate: ~50-100K JSON alert records
- [ ] Download Kaggle dataset (p0stscriptum)
  - Source: https://www.kaggle.com/datasets/p0stscriptum/ukraine-air-raid-alerts-and-military-events
  - File: CSV with ~100K records
  - Verify: `inferred_flag` column exists
- [ ] Obtain alerts.in.ua API credentials
  - Contact: https://alerts.in.ua (check for API docs)
  - Verify: 8-10 requests/minute rate limit documented

### Documentation
- [ ] Create data schema document (use Appendix A from v2.0)
- [ ] Document data locations (repo paths, CSV locations, API endpoints)
- [ ] Create quality baseline: Run data profiling on each source
  - Vadimkin: Alert counts, date ranges, null values
  - Kaggle: Record counts, inferred_flag distribution, date ranges
  - alerts.in.ua: Current alert status, API response times

**Owner:** Data Engineer | **Timeline:** Weeks 1-2 | **Deliverables:** Data access, schema docs, baseline quality metrics

---

## Phase 2: MVP Development (Weeks 3-12)

### Data Pipeline (Weeks 3-4)
- [ ] Implement Vadimkin parser (JSON → pandas DataFrame)
- [ ] Implement Kaggle ingestion (CSV → pandas DataFrame)
- [ ] Implement alerts.in.ua API client (Python requests library)
  - Rate limiting: 1 request per 12 seconds (8-10 req/min)
  - Polling: Every 5 minutes across 27 oblasts
- [ ] Deduplication engine
  - Compare Vadimkin vs. alerts.in.ua: Match on (oblast, start_time ± 5 min)
  - Flag duplicates; keep latest version

### Data Processing (Weeks 4-5)
- [ ] Normalize timestamps to ISO 8601
- [ ] Aggregate to time-series:
  - Daily alert counts per oblast
  - Daily alert duration per oblast
  - Alert frequency ranking
- [ ] Create lagged features:
  - Previous day, week, month alert counts
  - Day-of-week, month, season indicators
- [ ] Synthetic data handling:
  - Retain `inferred_flag` from Kaggle
  - Create binary feature: is_inferred (1 if inferred_flag, 0 if observed)

### Model Development (Weeks 5-8)
- [ ] Baseline models:
  - [ ] ARIMA (univariate): Alert count ~ lagged alert count
  - [ ] Prophet: Alert count with daily seasonality
  - [ ] Simple Exponential Smoothing: Baseline comparison
- [ ] Enhanced model:
  - [ ] Multivariate features:
    - Lagged alerts (t-1, t-7, t-30)
    - Day-of-week (one-hot)
    - Season (one-hot)
    - Synthetic data flag (is_inferred)
  - [ ] XGBoost or LightGBM: Alert count ~ (lagged + temporal + synthetic flag)
- [ ] Hyperparameter tuning:
  - [ ] Grid search or Bayesian optimization
  - [ ] Cross-validation: Time-series split (80% train, 20% test)
- [ ] Error analysis:
  - [ ] MAPE (Mean Absolute Percentage Error)
  - [ ] MAE (Mean Absolute Error)
  - [ ] Coverage: How often is 90% confidence interval correct?

### Validation (Weeks 8-10)
- [ ] Cross-reference model output with ground truth:
  - [ ] ISW daily reports: Alert spikes should correlate with ISW military event reports
  - [ ] Oryx confirmed losses: Major operations should precede alert increases
  - [ ] alerts.in.ua real-time: Historical predictions should match observed current status
- [ ] Sensitivity analysis:
  - [ ] Retrain without Kaggle synthetic data (quality impact)
  - [ ] Retrain without Vadimkin (redundancy check)
  - [ ] Retrain with alerts.in.ua only (cost-benefit check)
- [ ] Documentation:
  - [ ] Model card: Approach, features, performance, limitations
  - [ ] Assumptions document: ~30% synthetic data, unknown false alarm rates, oblast-level precision

### Deployment (Weeks 10-12)
- [ ] REST API:
  - [ ] Endpoint: `/forecast?oblast={oblast}&horizon_days={1-7}`
  - [ ] Response: Daily forecasts with 90% confidence intervals
- [ ] Weekly retraining pipeline:
  - [ ] Auto-ingest latest Vadimkin + alerts.in.ua data
  - [ ] Retrain model on new data
  - [ ] Log model performance (MAPE, MAE)
- [ ] Basic monitoring:
  - [ ] Alert if new data fails to load
  - [ ] Alert if model MAPE exceeds baseline by >10%
- [ ] Documentation:
  - [ ] API documentation
  - [ ] Deployment runbook

**Owner:** Data Scientist + Data Engineer | **Timeline:** Weeks 3-12 | **Deliverables:** Trained model, REST API, retraining pipeline, monitoring

---

## Phase 3: Validation & Acceptance (Weeks 12-16)

### Stakeholder Review
- [ ] Demo to data leadership: Model forecasts, API, retraining
- [ ] Demo to ops: Real-time monitoring dashboard
- [ ] FAQ preparation: "Why 75-85% accuracy? Why oblast-level? Why synthetic data?"

### Production Readiness
- [ ] Error budgets defined:
  - [ ] Acceptable MAPE: 15-25% (will this level support decision-making?)
  - [ ] Acceptable false alert rate: <2%
  - [ ] Acceptable data lag: <1 hour
- [ ] SLO defined:
  - [ ] API uptime: 99% (168 hours/month)
  - [ ] Forecast freshness: Daily (updated by 6 AM UTC)
  - [ ] Alert on missing data: Within 4 hours of expected update

### Go/No-Go Decision
- [ ] **GO Decision Criteria:**
  - [ ] Model MAPE <25% on test set
  - [ ] API uptime ≥99% in staging
  - [ ] Real-time alerts.in.ua monitoring validates predictions in 4/5 recent weeks
  - [ ] Cost <$50K (MVP scope confirmed)
- [ ] **NO-GO Decision:** If any criterion fails, document why; iterate Phase 2

**Owner:** Tech Lead + Data Scientist | **Timeline:** Weeks 12-16 | **Decision:** Deploy to production or extend Phase 2

---

## Phase 3b: If Going Enterprise (Weeks 17-26, OPTIONAL)

Only proceed if MVP validation proves forecasting value and org justifies $200K+ investment.

### Multi-Source Integration (Weeks 17-19)
- [ ] ISW integration: Daily event reports → feature engineering (major event binary flag)
- [ ] ACLED integration: Weekly conflict events → feature engineering
- [ ] Telegram scraping: Ukrainian Air Force alerts → validation feature
- [ ] Oryx integration: Weekly loss reports → cross-validation

### Distributed Architecture (Weeks 20-23)
- [ ] Kafka topic for real-time data streams
- [ ] S3 data lake (Parquet format)
- [ ] Distributed training (Ray or Spark MLlib)
- [ ] Model versioning (MLflow)

### 24/7 Operations (Weeks 24-26)
- [ ] On-call rotation (escalation)
- [ ] Incident runbooks (data outage, model drift, API failure)
- [ ] Quarterly model review process
- [ ] Monitoring dashboard (Grafana or similar)

**Owner:** Full team (4 engineers) | **Timeline:** 6-7 months | **Decision:** Justify cost before starting

---

## Cost Validation Checkpoints

### After Week 4 (Data Setup)
- [ ] Actual cost-to-date vs. budget ($5K budgeted)
- [ ] Status: On track? Over? Adjust scope if needed

### After Week 8 (Modeling)
- [ ] Actual cost-to-date vs. budget ($15-20K budgeted)
- [ ] Status: Model performing? Yes → continue; No → extend Phase 2

### After Week 12 (Deployment)
- [ ] Total cost-to-date vs. $25-50K budget
- [ ] Decision: MVP working? Yes → Phase 3; No → iterate

### After Week 16 (Acceptance)
- [ ] MVP total cost confirmed
- [ ] Value delivered: What decisions did forecasts enable?
- [ ] Decision: Justify enterprise expansion (Phase 3b)?

---

## Common Pitfalls & Mitigations

| Pitfall | Likelihood | Mitigation |
|---------|------------|-----------|
| Vadimkin data stops updating mid-project | Low | Week 1: Set up alerts.in.ua as backup; test dual-source pipeline |
| Kaggle synthetic data breaks model | Medium | Week 4: Include is_inferred feature from day 1; test without synthetic data separately |
| ACLED is still outdated (May 2025) | Medium | Week 1: Verify ACLED status; if outdated, use alerts.in.ua + ISW only |
| Rate limiting blocks API during peak hours | Low | Week 2: Implement exponential backoff; cache last 7 days locally |
| Model MAPE >30% (unacceptable) | Medium | Week 10: Extend feature engineering; add ISW event features; try LSTM |
| Deployment timeline slips beyond Week 12 | Medium | Week 8: If model not ready, drop advanced features; ship with ARIMA baseline |
| Ops team rejects API design | Low | Week 11: Co-design API with ops; validate response format in staging |

---

## Success Criteria

### MVP Success (Weeks 1-16)
- ✓ Data pipeline: All 3 sources loading cleanly
- ✓ Model: MAPE <25% on test set
- ✓ API: Responding <100ms, uptime ≥99%
- ✓ Cost: <$50K total
- ✓ Timeline: Completed by Week 16
- ✓ Validation: Predictions match observed alerts.in.ua data in 4/5 recent weeks

### Enterprise Success (Weeks 17-26, if pursued)
- ✓ All 9 sources integrated and cross-validated
- ✓ Model ensemble: MAPE <20%
- ✓ Distributed: Training time <4 hours for monthly retraining
- ✓ Monitoring: 24/7 SLA met for 8+ consecutive weeks
- ✓ Cost: Confirmed <$350K total
- ✓ Operations: On-call rotation established; incident response validated

---

## Weekly Status Template

Use this for Phase 1-3 standup meetings:

```markdown
## Week [N]: [Phase Name]

### What We Built This Week
- [ ] Specific deliverable 1
- [ ] Specific deliverable 2

### What We Learned
- Finding 1
- Finding 2

### Blockers
- Blocker 1: [Status/Impact] (Owner: X)

### On Track?
- Timeline: Yes / No / At Risk
- Budget: Yes / No / At Risk
- Quality: Yes / No / At Risk

### Next Week's Plan
- [ ] Action 1 (Owner: X)
- [ ] Action 2 (Owner: Y)
```

---

## Questions to Answer Before Starting

1. **Is this commercial or non-commercial?**
   - Commercial → Source from Vadimkin (MIT license)
   - Non-commercial → Can use Kaggle (CC-BY-NC-SA)

2. **What accuracy is "good enough"?**
   - Nowcasting (what's happening right now)? Need <5% MAPE, real-time data
   - Forecasting (next week)? Can tolerate 20-30% MAPE
   - Trend analysis (seasonal patterns)? Can tolerate 40% MAPE

3. **Who is the decision-maker?**
   - Military ops? Need <1% false alert rate; real-time
   - Researchers? Can work with historical; accept unknown quality metrics

4. **What's the timeline for decisions?**
   - Do you need working MVP in 12 weeks? (Yes → commit to MVP)
   - Do you need enterprise at scale? (Yes → plan for 6-7 months)
   - Is there flexibility? (Yes → start with MVP; expand if justified)

---

**For questions or clarifications, refer to:**
- **Detailed guidance:** `UKRAINIAN_AIR_RAID_ALERTS_RESEARCH_v2.0.md`
- **Decision logic:** `ARBITRATION_SUMMARY.md`
- **Blockers/Issues:** Section VII in v2.0 (Critical Blockers & Solutions)

---

**Last Updated:** Oct 2026 | **Next Review:** Jan 2027
