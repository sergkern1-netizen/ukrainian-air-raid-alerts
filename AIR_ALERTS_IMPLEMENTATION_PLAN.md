# AIR ALERTS IMPLEMENTATION PLAN
**Ukrainian Air Raid Alert Prediction System: Master Plan (Phase 3 Synthesis)**

**Date:** 2026-10-12
**Author role:** Chief Architect (synthesis of Agents 1-4 and the Phase 2 debate)
**Status:** Approved for Phase 0 (Verification)
**Related documents:** `CLAUDE.md`, `STRESS_TEST_CONSOLIDATED_FINDINGS.md`, `COMPLETE_SOURCE_INVENTORY.md`, `air_raid_prediction_architecture.html`

---

## 0. ARCHITECT'S CORRECTIONS TO PHASE 1-2 INPUTS

The synthesis surfaced several internal inconsistencies. They are resolved here so later sections stay consistent:

| # | Input as stated | Problem | Resolution in this plan |
|---|-----------------|---------|-------------------------|
| C1 | Kafka "2 brokers, 3x replication" | Replication factor cannot exceed broker count | **3 brokers**, RF=3, `min.insync.replicas=2` |
| C2 | Phase 1 gate "<40 min lead time" | Inverted: lead time is a floor, not a ceiling | Gate is **median lead time >= 20 min at precision >= 70%** |
| C3 | Kaggle listed as a Phase 2 source, but used in Milestone 3 | Sequencing conflict | Kaggle and Vadimkin are **MVP historical training sources**. Kaggle is CC-BY-NC-SA, so commercial builds train on Vadimkin (MIT) only |
| C4 | 4 producers x 2 req/min against alerts.in.ua | The rate limit applies per token, not per producer | **1 active poller at 4 req/min + 1 hot standby** (leader election), about 50% headroom under the 8-10 req/min limit |
| C5 | Telegram "webhook receiver" | Bot webhooks cannot read public channels | Use an **MTProto client (Telethon)** subscribed to @kpszsu |
| C6 | Kafka + Spark + K8s in the 8-week MVP | Conflicts with `CLAUDE.md` (one data scientist, $25-50K, "no fault tolerance before the core pipeline runs") | Phase 1 runs a **lean profile** (Docker Compose, Python consumers). The full 5-layer K8s stack arrives in Phase 2 behind the same interfaces |
| C7 | RMSE as a Phase 0 baseline while also called a "vanity metric" | Mixed messaging | RMSE/MAE are kept **only** as count-forecast sanity checks, required by `CLAUDE.md`. Go/no-go decisions use precision, recall and lead time |
| C8 | ISW "weekly GeoJSON" | ISW publishes daily assessments plus periodic map layers | Daily text ingest; map layers whenever they update |

---

## 1. SYSTEM VISION & CORE MISSION

### What we are building
One integrated decision-support product with three tiers that share a single data and modeling core:

1. **Early Warning:** a short-horizon (0-60 min) probability that an oblast or H3 cell will be under alert. It is a forecast that complements the official alert system and never replaces it.
2. **Regional Risk:** a 6-72 hour risk outlook per oblast and city, with confidence bands. It is meant for civil-protection planners, utilities, schools and hospitals.
3. **Humanitarian Impact:** expected population exposure, shelter-capacity strain and pre-positioning recommendations (generators, medical teams, water) for NGOs and regional administrations.

### Why
- **Lead time saves lives.** An official siren gives minutes of warning. A calibrated 20-40 minute heads-up on a high-risk window lets hospitals move patients, transit operators stage shelters and families reach cover before the siren sounds.
- **Reduce alert fatigue.** Long, frequent and geographically broad alerts teach people to ignore sirens. Regional risk scores tell people *which* alerts are most likely to involve strikes on their area.
- **Enable pre-positioning.** Humanitarian logistics run on hours and days. A 24-72 hour risk outlook turns reactive response into planned deployment.

### Guiding principles
- **Official alerts stay authoritative.** Every output carries the disclaimer "forecast, not an alert."
- **OPSEC by design.** The system never publishes real-time strike locations, impact sites or air-defense positions. Ukrainian martial-law rules restrict publishing these. Public outputs are aggregated and delayed; precise outputs are available only to authenticated civil-protection users.
- **No leakage, no fabrication.** These non-negotiables are inherited from `CLAUDE.md`.

### Success definition
| Dimension | MVP (week 8) | Production (week 18) | Scale (month 18) |
|-----------|--------------|----------------------|------------------|
| Precision @ 70% recall (alert-onset, 30-min horizon) | >= 70% backtest | >= 75% live | >= 80% live |
| Median lead time at that operating point | >= 20 min | >= 25 min | >= 30 min |
| False alarm rate | < 30% | < 25% | < 20% |
| Adoption | n/a | 50%+ of civil-protection units in 3 pilot cities | 2M+ people served via partners |
| Availability (prediction API) | best effort | 99.5% | 99.9% |

---

## 2. DATA & FEATURE ENGINEERING MATRIX

### Ingestion breakdown

**MVP (months 0-6)**

| Source | Role | Mode | Cadence | License note |
|--------|------|------|---------|--------------|
| alerts.in.ua API | Real-time label and alert-count series | Poll (C4) | 15 s | Token required; terms unspecified, so get them in writing |
| Vadimkin dataset | Historical labels 2022 to present | Batch | Daily | MIT |
| Kaggle (p0stscriptum) | Cross-check labels; inferred-end flag | Batch | Daily | CC-BY-NC-SA (research builds only) |
| ACLED | Ground-truth event validation | Batch | Weekly | Register; check freshness (Blocker #2) |
| ISW | Military context, threat level by region | Scrape + NLP | Daily | Cite; no redistribution |
| Telegram @kpszsu | Launch and confirmation signals, location mentions | Stream (Telethon) | Real-time | Public channel |
| Open-Meteo | Weather covariates (drone flight conditions) | API | Hourly | Free (CC-BY) |

**Phase 2 and later (months 6-18):** Sentinel Hub (infrastructure-damage correlation), Oryx (strike confirmation proxy), CSIS Missile Threat (launch patterns), DeepState (frontline geometry), raid.fly.dev (backup alert API), Kaggle Massive Missile Attacks (strike-level labels).

### Derived feature vectors

All sources are normalized to **UTC** and to an **H3 index** (resolution 5 for oblast/raion aggregation, resolution 7 for cities). Each record carries `source_id`, `ingested_at` and `event_time`. Features may only use rows where `ingested_at <= forecast_time`, which prevents leakage.

| Source | Feature vector |
|--------|----------------|
| alerts.in.ua / Vadimkin | `(alert_count_{15m,1h,6h,24h}, active_flag, oblast, h3, duration, time_since_last_alert, neighbor_active_count, inferred_end_flag)` |
| ACLED | `(event_type, h3, fatality_estimate, source_confidence, days_since_last_event_in_cell)` |
| Telegram NLP | `(mentioned_locations[], event_type ∈ {launch, UAV group, missile, all-clear}, msg_time, extraction_confidence)` |
| ISW | `(threat_level_by_region, ops_intensity_index, distance_frontline_to_city_km)` |
| Open-Meteo | `(pressure, wind_speed, cloud_cover, convective_potential, visibility)` |
| CSIS (Ph2) | `(launch_pattern_cluster, missile_type_mix, est_target_class)` |
| DeepState (Ph2) | `(frontline_distance_km, frontline_change_7d)` |
| Calendar | `(hour_of_day, day_of_week, holiday_flag, days_since_last_mass_strike)` |

**Core feature budget:** 10-12 features in the MVP model (Agent 1). Additional features enter only if walk-forward validation shows at least a 2-point precision gain.

### Telegram NLP pipeline
Steps: language ID (uk/ru) → rule-based plus fine-tuned NER for Ukrainian toponyms → gazetteer match to KATOTTH codes → H3 → event-type classifier → confidence score. Messages with location confidence below 0.6 are kept as region-level signals only.

### Quality metrics (dashboarded from Milestone 2)
- **Cross-source agreement rate:** at least 80% agreement among alerts.in.ua, Vadimkin and Telegram on "alert active in oblast X at time t."
- **False alarm rate:** predicted onset with no official alert within the horizon. Target below 25%.
- **Label noise register:** record the inferred end-time share per source (Kaggle is about 20-40%) and carry `inferred_end_flag` as a feature and as a sample weight.
- **Ground-truth validation:** join alerts to ACLED, ISW and (Phase 2) Oryx confirmed strikes to measure "alerts with strikes" against "alerts without strikes."
- **Freshness SLOs:** alerts.in.ua < 60 s; Telegram < 30 s; ACLED < 14 days; ISW < 36 h.

---

## 3. ML & PREDICTIVE MODELING BLUEPRINT

### Prediction targets
1. **Onset classification:** P(alert starts in cell c within horizon h) for h ∈ {15, 30, 60} min. This target serves Early Warning.
2. **Count forecast:** expected alert count per oblast in the next 6/24/72 h. This target serves Regional Risk and Humanitarian Impact.

### Model selection
| Role | Model | Rationale |
|------|-------|-----------|
| Primary (counts) | **Zero-inflated Negative Binomial / Poisson GLM** | Sparse, overdispersed counts with many zero intervals. Interpretable coefficients for civil-protection users |
| Ensemble (onset) | **Multivariate temporal Hawkes process** (exponential kernel, cross-excitation between neighboring oblasts) | Mass strikes are self-exciting: one alert raises near-term intensity in its own region and in adjacent regions |
| Combiner | Logistic stacker on [GLM rate, Hawkes intensity, Telegram signal] | Calibrated probability output |
| Fallback | **Rule engine**: launch signal + missile/UAV type + projected track + distance to city < 50 km → HIGH | Deterministic and auditable. Runs when ML is unavailable |

Phase 0 EDA confirms or rejects these choices (per `CLAUDE.md`). If ACF/PACF show strong linear autocorrelation and low sparsity, an ARIMA-family baseline is added.

### Training regime
- **Splits:** train 2022-02-24 to 2024-12-31; validation 2025; test 2026 to date, then live.
- **Walk-forward:** 5 non-overlapping folds with an expanding window and a 24 h embargo gap between train and test, so label windows cannot overlap.
- **Retraining:** monthly. An emergency retrain triggers if drift alarms fire (see below).
- **Sampling:** stratify by (oblast, activity regime) so the model does not train mostly on quiet periods. Oversample the 15 min windows before onsets.

### Loss and evaluation
- **Primary KPI:** precision at 70% recall (onset, 30-min horizon), reported per oblast and in aggregate.
- **Secondary:** lead time, the median minutes between first prediction above threshold and the official onset, measured at the primary operating point.
- **Tertiary:** false alarm rate (< 25%), Brier score and a calibration curve.
- **Diagnostics only:** RMSE/MAE on daily counts (`CLAUDE.md` targets: RMSE < 5, MAE < 3).
- **Training loss:** negative log-likelihood (GLM, Hawkes), with sample weights applied (below).

### Baselines (each must be beaten)
1. Seasonal naive: 7-day moving average by hour of day. This sets the hurdle rate.
2. Zero-inflated Poisson with calendar features only. This shows whether external signals add value.
3. Hawkes alone. This quantifies the ensemble gain.

### Data quality handling
- **Label noise:** sample weight = cross-source agreement score × (0.5 if `inferred_end_flag` else 1.0).
- **Class imbalance:** zero inflation handles count sparsity. The onset classifier uses class weights and is tuned at the 70% recall operating point, not at 0.5.
- **Drift:** weekly PSI on the top features plus monthly precision on the trailing 30 days. If precision drops more than 5 points, page the on-call, shift weight toward the rule engine and schedule a retrain.
- **Gaps:** forward-fill temporal features (with a maximum staleness, after which the value becomes null plus a missing flag); median-impute cross-sectional features; always emit `*_missing` indicators.

### Validation methodology
1. **Backtest** 2022-2025 with point-in-time feature reconstruction, so `ingested_at` is respected.
2. **Walk-forward** across 2025-2026 on an expanding window.
3. **Shadow mode** for at least 4 weeks: live predictions are logged and scored but never shown.
4. **Real-world validation:** compare against ISW, ACLED and Oryx confirmations as well as alert labels, which checks that "high risk" means actual strikes and not only sirens.

---

## 4. SYSTEM ARCHITECTURE

### Deployment profiles
| Profile | When | Runtime |
|---------|------|---------|
| **Lean** | Phase 1 (weeks 2-8) | Docker Compose on 1-2 VMs. Single-node Redpanda/Kafka, Python consumers, TimescaleDB+PostGIS, Redis, FastAPI |
| **Production** | Phase 2 (weeks 9-18) | Kubernetes across 2+ AZs. Full five-layer design below |
| **Federated** | Phase 3 | Multi-cluster (UA, PL, MD) with a federated feature registry |

Interfaces (topic names, schemas, API contracts) are the same in every profile, so promotion between profiles needs no rewrite.

### Layer 1: Ingestion
- **alerts.in.ua:** 1 active poller plus 1 standby (Kubernetes lease) at 4 req/min, publishing to `alerts.raw` (C4).
- **Kafka:** 3 brokers, RF=3, `min.insync.replicas=2`, retention 24 h on raw topics (C1). Topics: `alerts.raw`, `telegram.raw`, `osint.batch`, `weather.raw`, `features.online`, `predictions`.
- **Telegram:** Telethon stream consumer (C5). **Batch fetchers** (ACLED, ISW, Vadimkin, Kaggle, Open-Meteo) run as scheduled Kubernetes CronJobs, or cron in Lean.
- **Schemas:** Avro with a schema registry. Every message has `event_time`, `ingested_at` and `source_id`.

### Layer 2: Storage
| Store | Contents | Retention |
|-------|----------|-----------|
| TimescaleDB | Alerts, weather, telemetry hypertables | 7 days hot, 3 months warm (compressed) |
| PostGIS (same cluster) | Admin boundaries, H3 polygons, gazetteer | Permanent |
| Redis | Online feature cache, latest predictions | TTL 1 h; p99 read < 50 ms |
| DuckDB over Parquet | Training sets, analytics | Rebuilt on demand |
| S3-compatible object store | Raw archive, model artifacts, backups | 7 years, Parquet, versioned |

### Layer 3: Processing
- **Lean:** Python stream consumers compute rolling windows into Redis and Timescale.
- **Production:** Spark Structured Streaming with exactly-once semantics through Kafka transactions and idempotent sinks.
- **Feature store:** offline features (Parquet) and online features (Redis) share one feature definition registry, which removes train/serve skew.
- **SLO:** < 10 s from raw alert to feature-ready.

### Layer 4: Inference
- **Online ensemble** (GLM + Hawkes + stacker) served by FastAPI. Ray Serve takes over in Phase 3.
- **Latency:** < 100 ms p95, < 150 ms p99.
- **Automatic fallback:** the rule engine answers if inference p99 exceeds 150 ms for 60 s, Redis is unavailable, or the drift alarm is active. Responses carry `"mode": "ml" | "fallback"`.
- **Model registry (MLflow):** a model is promoted only after it passes the walk-forward gate and 7 days of shadow comparison.

### Layer 5: User API
- **REST:** `/v1/risk/{oblast}`, `/v1/forecast/{h3}`, `/v1/impact/{oblast}`.
- **WebSocket:** `/v1/stream` pushes prediction updates.
- **Audience tiers:**
  - *Civil protection:* authenticated, high-precision operating point, cell-level detail, confidence intervals.
  - *Public:* simplified three-level risk, oblast-level only, rate-limited, CDN-cached, with OPSEC filtering.
  - *Humanitarian:* 6-72 h outlooks plus exposure estimates.

### Resilience mechanisms
| Failure | Mechanism | Target |
|---------|-----------|--------|
| Network or upstream outage | Kafka 24 h backlog; serve from cached features with a staleness flag | RTO 2-5 min |
| alerts.in.ua rate-limited or down | Fail over to raid.fly.dev, then to Telegram-derived alert state | < 60 s switchover |
| Redis or ML failure | Rule-based fallback | Seamless (mode flag) |
| Data loss | Kafka RF=3; Timescale WAL streaming; nightly S3 snapshots | RPO 60 s |
| AZ loss | Multi-AZ K8s, PodDisruptionBudgets | Survives 1 AZ |

### Scalability path
- **Day 1 of production:** 5,000 req/s sustained, 15,000 req/s p99 during mass strikes (CDN absorbs the public tier), 49 regions.
- **Phase 3, regional expansion:** separate clusters for Poland and Moldova, Kafka partition expansion keyed by H3 parent, cross-cluster MirrorMaker.
- **Phase 3, EU-wide:** federated architecture with Ray Serve autoscaling and a regional feature-store federation.

---

## 5. ACTIONABLE IMPLEMENTATION ROADMAP

### PHASE 0: VERIFICATION (Week 1, 40 h)
- [ ] Verify the Vadimkin volunteer feed is active (last commit date, update cadence). **Blocker #1**
- [ ] Verify ACLED Ukraine data is current beyond May 2025. **Blocker #2**
- [ ] Obtain an alerts.in.ua API token; measure historical endpoint depth; get usage terms in writing
- [ ] Download the first 1,000 rows from each MVP source; build the UTC/timezone audit
- [ ] Profile per-oblast alert distributions (dispersion index, % zero intervals: Poisson or NegBin?)
- [ ] Run ADF stationarity and ACF/PACF tests; fit a quick Hawkes model and check the branching ratio (confirms Hawkes vs. ARIMA)
- [ ] Compute seasonal-naive baseline metrics (precision/recall/lead time, plus RMSE/MAE)
- **Gate 0:** both blockers resolved or replacement sources chosen, baseline recorded, model family confirmed → go to Phase 1

### PHASE 1: MVP FOUNDATION (Weeks 2-8, 280 h, Lean profile)

**Milestone 1 (Weeks 2-3, 80 h): Data infrastructure**
- [ ] Docker Compose stack: Kafka/Redpanda, TimescaleDB+PostGIS, Redis, MLflow
- [ ] alerts.in.ua poller with standby and backoff; schema registry
- [ ] Load tests: consumer lag < 5 s, Redis p99 < 50 ms

**Milestone 2 (Weeks 4-5, 80 h): Data pipelines**
- [ ] Batch ingest for Vadimkin and Kaggle (daily), ACLED (weekly) and ISW (daily)
- [ ] Telethon consumer for @kpszsu; NLP location and event extraction (target F1 >= 0.8 on 500 hand-labeled messages)
- [ ] Open-Meteo hourly ingest
- [ ] H3 normalization for all sources; point-in-time joins
- [ ] Data quality dashboard (agreement, freshness, inferred-label share)

**Milestone 3 (Weeks 6-7, 80 h): ML foundation**
- [ ] Feature engineering (10-12 core features, shared registry)
- [ ] Three baselines; ZINB/Poisson GLM; multivariate Hawkes; stacker
- [ ] 5-fold walk-forward validation 2022-2025; precision-recall curves; lead-time distribution per oblast
- [ ] Rule-based fallback engine with unit tests

**Milestone 4 (Week 8, 40 h): Integration and testing**
- [ ] End-to-end path: alerts.in.ua → features → inference → API
- [ ] FastAPI REST and WebSocket; < 100 ms p95
- [ ] Chaos tests: kill Redis, kill model server, block alerts.in.ua; confirm fallback and failover
- [ ] `python run_pipeline.py` reproduces training from scratch
- **Gate 1:** precision >= 70% @ 70% recall on the walk-forward backtest, median lead time >= 20 min, beats all three baselines, chaos tests pass → start shadow mode and Phase 2

### PHASE 2: PRODUCT & OPERATIONS (Weeks 9-18, 360 h, Production profile)

**Milestone 5 (Weeks 9-11): Product layer**
- [ ] Civil-protection dashboard (regional risk map, lead time, confidence, model mode)
- [ ] Public API with OPSEC filter and simplified risk levels
- [ ] Humanitarian impact module (population exposure from WorldPop/Kontur, shelter-capacity strain)
- [ ] OAuth2/OIDC auth; tiered access control; audit log

**Milestone 6 (Weeks 12-14): Operational excellence**
- [ ] Kubernetes across 2+ AZs (Helm); 3-broker Kafka; Spark Structured Streaming
- [ ] CI/CD with a model-validation gate (walk-forward and shadow diff before promotion)
- [ ] Monitoring: Prometheus/Grafana for Kafka lag, Redis latency, inference p99, drift PSI, precision on the trailing 30 days
- [ ] Incident playbooks: (1) alerts.in.ua down, (2) network partition, (3) model failure or drift, (4) mass-strike load surge, (5) data-source poisoning or anomalous Telegram content

**Milestone 7 (Weeks 15-18): Optimization and scaling**
- [ ] A/B test of ensemble weights (GLM vs. Hawkes vs. Telegram signal) on the civil-protection pilot
- [ ] Latency and throughput tuning to 5k req/s sustained and 15k req/s burst
- [ ] Onboard Phase 2 sources (Oryx, CSIS, DeepState, Sentinel Hub pilot)
- [ ] Runbooks, architecture docs, knowledge transfer
- **Gate 2:** >= 75% precision @ 70% recall **live**, median lead time >= 25 min, false alarm rate < 25%, 99.5% availability over 4 weeks → general availability

### PHASE 3: ENTERPRISE EXPANSION (Months 5-18)
- Sentinel Hub imagery for damage correlation and target-class priors
- Expansion to Poland and Moldova (border-region early warning) with partner agencies
- Advanced OSINT: DeepState frontline geometry, Bellingcat-verified incidents
- Multilingual UX (Ukrainian, English, Polish, Romanian) and multilingual NLP (Ukrainian, Russian)
- EU-wide federation and Ray Serve autoscaling

### Success criteria by phase
| Phase | Criteria |
|-------|----------|
| 0 | Blockers resolved; baselines and model family recorded |
| 1 | MVP live on historical replay; >= 70% precision @ 70% recall; >= 20 min median lead time |
| 2 | Production GA; >= 75% live precision; < 25% false alarms; 50%+ adoption among civil-protection units in 3 pilot cities |
| 3 | Multi-country operation; < 20% false alarms; 2M+ people served via partners |

### Resourcing and budget
- **Phase 0-1:** 1 senior data scientist plus 0.5 data/platform engineer, $25-50K (consistent with `CLAUDE.md`)
- **Phase 2:** 4 engineers (ML, data, platform/SRE, frontend), $200-340K cumulative for Enterprise
- **Phase 3:** cost is set at the Gate 2 review

---

## 6. RISK MITIGATION STRATEGY

| # | Risk | Likelihood / Impact | Mitigation | Early indicator |
|---|------|---------------------|------------|-----------------|
| 1 | **Data drift**: enemy tactics change (new drone routes, launch timing) and alert policy changes | High / High | Monthly retraining, PSI drift alarms, walk-forward evaluation, automatic shift toward the rule engine | Precision on the trailing 30 days drops more than 5 points |
| 2 | **Alert fatigue** if our forecasts add noise | Medium / High | Precision-first operating point, per-audience thresholds, user feedback loop, false alarm rate on the dashboard | Rising dismissals or unsubscribes from pilot users |
| 3 | **Infrastructure unavailable at conflict peaks** (outages, cyberattacks) | High / High | 24 h Kafka backlog, backup APIs, rule fallback, multi-AZ, a hosting region outside Ukraine | Upstream error rate, consumer lag |
| 4 | **Single-source dependency** (Vadimkin volunteer burnout, alerts.in.ua terms change) | Medium / High | Store our own copy of the real-time alert history from day 1; maintain the raid.fly.dev and Telegram fallbacks; contact maintainers | Feed staleness over 24 h |
| 5 | **OPSEC and legal**: outputs could help an adversary or break publication restrictions | Low / Critical | No precise public locations or impact sites, delayed and aggregated public outputs, legal review before GA, partnership with civil-protection authorities | Any request for raw cell-level data from unauthenticated clients |
| 6 | **Overclaimed lead time**: alerts follow detected launches, so the true predictable horizon may be shorter than 20-40 min | Medium / Medium | Report the lead-time distribution honestly per oblast; position Regional Risk (hours) as the guaranteed-value tier | Phase 1 median lead time < 20 min |
| 7 | **Licensing** (Kaggle CC-BY-NC-SA) | Medium / Medium | Build commercial models on Vadimkin (MIT) only; keep a license register | n/a |
| 8 | **Data poisoning** via Telegram or crowdsourced inputs | Low / High | Trust only allow-listed official channels; cross-source agreement gating; anomaly detection | Agreement rate drops sharply |

---

## 7. VIABILITY ASSESSMENT & TIMELINE

- **Viability:** 80-85% with proper execution. The largest risk is underestimating data drift (Risk 1), followed by achievable lead time (Risk 6).
- **Timeline:** 1 week of verification → **8 weeks to the MVP** (Phase 1, historical replay and shadow mode) → **18 weeks to Phase 2 production GA** → 18 months to multi-country operation.
- **Critical path:** Blocker #1/#2 → Kaggle/Vadimkin ingest → walk-forward validation → Gate 1 → shadow mode (4 weeks, overlapping Milestones 5-6) → Gate 2.
- **Next action:** run Phase 0 checklist items 1-3. Today they are the only blockers.

---

**END OF IMPLEMENTATION PLAN**
