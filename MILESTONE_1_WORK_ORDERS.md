# Milestone 1 Work Orders: Data Infrastructure (Weeks 2-3, 80 hours)
**Status:** Ready for Agent Dispatch  
**Orchestrator:** Lead Architect (Sonnet/Opus)  
**Target:** Docker Compose stack with real-time + batch ingestion

---

## WORK ORDER STRUCTURE

Each order specifies:
- **Tier:** A (Haiku/Fast) or B (Sonnet/Deep)
- **Context:** Minimal slice of codebase to pass
- **Deliverable:** Code + unit tests
- **Success Criteria:** Specific, measurable gate

---

## WORK ORDER 1: Project Structure & Environment Setup
**Tier:** A (Lightweight)  
**Duration:** 2-3 hours  
**Owner:** Engineer-A1

### Scope
Create directory structure, .env template, requirements.txt pins, Docker Compose skeleton.

### Context to Pass
- `requirements.txt` (existing)
- Current `src/__init__.py`
- `CLAUDE.md` (Multi-Agent section only)

### Deliverables
```
D:\air\
├── .env.example
├── docker-compose.yml (skeleton)
├── src/
│   ├── __init__.py
│   ├── config.py (read from .env)
│   └── __main__.py (entry point)
├── data/
│   ├── raw/
│   ├── processed/
│   └── .gitkeep
├── tests/
│   ├── __init__.py
│   └── test_config.py (verify .env loading)
└── notebooks/
    └── .gitkeep
```

### Success Criteria
- [ ] All directories created
- [ ] `test_config.py` passes: config loads .env correctly
- [ ] `run_pipeline.py` structure documented (README)

---

## WORK ORDER 2: Docker Compose Stack (Kafka, TimescaleDB, Redis)
**Tier:** A (Lightweight)  
**Duration:** 4-5 hours  
**Owner:** Engineer-A2

### Scope
Write `docker-compose.yml` with:
- Redpanda (Kafka substitute): 3 brokers, RF=3, min.insync.replicas=2
- TimescaleDB + PostGIS
- Redis
- Schema Registry (Confluent)
- Healthchecks for all services

### Context to Pass
- Architecture section from `AIR_ALERTS_IMPLEMENTATION_PLAN.md` (Layer 1-2 only)
- Docker resource constraints (CPU/memory for local dev)

### Deliverables
```
docker-compose.yml (complete, tested locally)
- 3x Redpanda brokers (port 9092, 9093, 9094)
- TimescaleDB (port 5432, CREATE EXTENSION postgis)
- PostGIS enabled on TimescaleDB
- Redis (port 6379)
- Schema Registry (port 8081)
- All services: healthcheck + restart policy
```

### Success Criteria
- [ ] `docker compose up` brings all 6 services online
- [ ] Healthchecks pass within 30s
- [ ] Kafka broker list: `localhost:9092,localhost:9093,localhost:9094`
- [ ] `psql` connects to TimescaleDB, PostGIS extensions loaded
- [ ] Unit test: create Kafka topic, write/read record

---

## WORK ORDER 3: Alerts.in.ua Poller (Real-Time Ingestion)
**Tier:** B (Deep Engineering)  
**Duration:** 6-8 hours  
**Owner:** Engineer-B1

### Scope
Write async poller with:
- 1 active + 1 standby via Kubernetes lease simulation (etcd-like TTL)
- 4 req/min polling (8-10 soft limit headroom)
- Automatic failover on 429 (rate limit)
- Publish to `alerts.raw` Kafka topic
- Avro schema with `event_time`, `ingested_at`, `source_id`

### Context to Pass
```
File: src/ingestion/alerts_in_ua_poller.py
File: src/config.py (for API token, endpoints)
Schema: Avro definition for alerts.raw topic
Dependencies: aiohttp, kafka-python, pydantic-settings
```

### Deliverables
```
src/ingestion/
├── __init__.py
├── alerts_in_ua_poller.py (AsyncAlertsPoller class)
├── schemas.py (Avro + Pydantic models)
└── tests/
    └── test_alerts_poller.py (mock API + Kafka)
```

### Success Criteria
- [ ] Polls `/v1/alerts/active.json` every 15s
- [ ] Publishes Avro-encoded messages to Kafka
- [ ] Handles 429 with exponential backoff
- [ ] Standby election logic: if active heartbeat missing >30s, standby takes over
- [ ] Unit tests: mock API responses, verify Kafka publish format
- [ ] Load test: 4 req/min sustained, <100ms per poll, <10s lag to Kafka

---

## WORK ORDER 4: Batch Ingesters (Vadimkin, Kaggle, ACLED, ISW)
**Tier:** A (Lightweight)  
**Duration:** 8-10 hours  
**Owner:** Engineer-A3

### Scope
Write four batch ingestion scripts (one per source):
- **Vadimkin:** Download CSV from GitHub releases, parse, validate schema
- **Kaggle:** Download via Kaggle API (requires `.kaggle/kaggle.json`), handle CC-BY-NC-SA licensing
- **ACLED:** REST API query (requires registration), paginate results
- **ISW:** Web scrape daily assessment PDFs, extract text
- All: Publish to respective Kafka topics + store to Parquet (data/raw/)

### Context to Pass
```
File: AIR_ALERTS_IMPLEMENTATION_PLAN.md (Section 2: Data & Feature Engineering)
File: DATA_SOURCES_REFERENCE.json (URLs, auth requirements)
Schema definitions: Avro for each topic
```

### Deliverables
```
src/ingestion/batch_loaders.py
├── VadimkinLoader
├── KaggleLoader
├── AcledLoader
├── IswLoader
tests/test_batch_loaders.py
data/raw/.gitkeep
```

### Success Criteria
- [ ] Vadimkin: Download 299K records, parse dates (UTC), validate
- [ ] Kaggle: Download, flag `inferred_flag=True` for rows with inferred end times
- [ ] ACLED: Fetch last 30 days, publish to `osint.batch` topic
- [ ] ISW: Scrape 3 recent PDFs, extract threat levels by region
- [ ] All: Unit tests with mocked data (no live API calls in CI)
- [ ] All: Publish Avro to Kafka + save Parquet with metadata (schema version, ingested_at)

---

## WORK ORDER 5: Telegram Ingestion (Telethon Stream)
**Tier:** B (Deep Engineering)  
**Duration:** 5-7 hours  
**Owner:** Engineer-B2

### Scope
Write Telethon-based async consumer for `@kpszsu` channel:
- Subscribe to channel updates
- Extract location mentions (NER + gazetteer match)
- Classify event type (launch, UAV, missile, all-clear)
- Publish to `telegram.raw` topic
- Handle rate limits & reconnection

### Context to Pass
```
File: AIR_ALERTS_IMPLEMENTATION_PLAN.md (Section 2: Telegram NLP pipeline)
File: src/config.py (Telegram session credentials)
Dependencies: telethon, spacy (Ukrainian NER), sklearn (classifier)
```

### Deliverables
```
src/ingestion/
├── telegram_consumer.py (TelegramStreamConsumer class)
├── telegram_nlp.py (LocationExtractor, EventClassifier)
└── tests/
    └── test_telegram_consumer.py (mock channel messages)
```

### Success Criteria
- [ ] Connect to @kpszsu, receive messages in real-time
- [ ] Extract 3+ Ukrainian city/oblast names per message (if present)
- [ ] Classify event type with confidence threshold (>0.7)
- [ ] Publish to Kafka with structure: `{msg_id, msg_time, text, locations[], event_type, confidence}`
- [ ] Unit tests: mock Telegram API, verify NER + classification F1 >= 0.75
- [ ] Graceful reconnection on network failure

---

## WORK ORDER 6: Weather Ingestion (Open-Meteo)
**Tier:** A (Lightweight)  
**Duration:** 3-4 hours  
**Owner:** Engineer-A4

### Scope
Hourly weather fetch for Ukraine (Kyiv coordinates as proxy):
- Temperature, wind speed, cloud cover, convection potential, visibility
- Publish to `weather.raw` Kafka topic
- Avro schema with `event_time`, `location_uid` (H3 cell)

### Context to Pass
```
File: DATA_SOURCES_REFERENCE.json (Open-Meteo API endpoint)
Schema: Avro for weather.raw
Dependencies: requests, pytz (UTC normalization)
```

### Deliverables
```
src/ingestion/weather_loader.py
└── tests/test_weather_loader.py (mock API response)
```

### Success Criteria
- [ ] Fetch from Open-Meteo every 60 min
- [ ] Parse response, normalize to UTC
- [ ] Publish to Kafka (one message per hour)
- [ ] Unit test: mock API response, verify schema

---

## WORK ORDER 7: Schema Registry & Avro Definitions
**Tier:** A (Lightweight)  
**Duration:** 2-3 hours  
**Owner:** Engineer-A1 (with B1 review)

### Scope
Define Avro schemas for all 6 Kafka topics:
- `alerts.raw` (from alerts.in.ua)
- `telegram.raw` (from @kpszsu)
- `osint.batch` (ACLED, ISW)
- `weather.raw` (Open-Meteo)
- `features.online` (feature-store output)
- `predictions` (model inference output)

### Context to Pass
```
File: AIR_ALERTS_IMPLEMENTATION_PLAN.md (Section 2: Feature vectors)
File: src/ingestion/schemas.py (stub with field definitions)
```

### Deliverables
```
src/schemas/
├── alerts_raw.avsc
├── telegram_raw.avsc
├── osint_batch.avsc
├── weather_raw.avsc
├── features_online.avsc
├── predictions.avsc
└── __init__.py (load all schemas)
```

### Success Criteria
- [ ] All 6 schemas defined, JSON-valid Avro
- [ ] Each schema includes: `event_time` (long, UTC ms), `ingested_at` (long), `source_id` (string)
- [ ] Schema Registry can load all schemas without error
- [ ] Backward compatibility: can read older versions (compatibility mode: BACKWARD)

---

## WORK ORDER 8: Load Tests & Health Checks
**Tier:** A (Lightweight)  
**Duration:** 4-5 hours  
**Owner:** Engineer-A2 (with B1 verification)

### Scope
Write load & chaos tests:
- Sustained 4 req/min to alerts.in.ua (measure latency, p99)
- Kafka consumer lag: verify <5s from producer to consumer
- Redis latency: p99 <50ms
- Chaos: kill Redis, verify graceful fallback to in-memory
- Chaos: block alerts.in.ua, verify failover to backup endpoint (stub)

### Context to Pass
```
File: docker-compose.yml (service names, ports)
File: src/ingestion/ (all loader modules)
Dependencies: locust (load testing), prometheus-client (metrics)
```

### Deliverables
```
tests/
├── test_load_alerts_poller.py (4 req/min, sustained 10 min)
├── test_kafka_lag.py (verify consumer lag <5s)
├── test_redis_latency.py (p99 <50ms, measure after 1000 ops)
└── chaos_tests.py (kill/block services, measure recovery)
```

### Success Criteria
- [ ] Alerts poller: sustained 4 req/min, p99 <1000ms (including network RTT)
- [ ] Kafka: consumer lag <5s for all topics
- [ ] Redis: p99 latency <50ms across 1000 SET/GET operations
- [ ] Kill Redis: system detects failure <2s, logs warning
- [ ] Block alerts.in.ua: system detects 429, backs off exponentially
- [ ] All tests pass in CI/Docker environment

---

## DISPATCH TIMELINE

| Week | Task | Tier | Owner | Hours | Status |
|------|------|------|-------|-------|--------|
| W2 | 1. Project Structure | A | A1 | 3 | 🟡 Ready |
| W2 | 2. Docker Compose | A | A2 | 5 | 🟡 Ready |
| W2-3 | 3. Alerts Poller | B | B1 | 8 | 🟡 Ready |
| W2-3 | 4. Batch Loaders | A | A3 | 10 | 🟡 Ready |
| W3 | 5. Telegram Consumer | B | B2 | 6 | 🟡 Ready |
| W3 | 6. Weather Loader | A | A4 | 4 | 🟡 Ready |
| W2 | 7. Schema Registry | A | A1 (B1) | 3 | 🟡 Ready |
| W3 | 8. Load Tests | A | A2 (B1) | 5 | 🟡 Ready |

**Total:** 44 hours (80 planned includes integration, refinement, documentation)

---

## ORCHESTRATOR CHECKLIST (Validation Gates)

After each work order:
- [ ] Code compiles/imports without error
- [ ] Unit tests pass (100% in target file)
- [ ] Code follows PEP 8 (run `flake8 --max-line-length=100`)
- [ ] No hardcoded secrets (check for `token=`, `password=`, API keys)
- [ ] Docstrings for public functions (1-line minimum)
- [ ] No `print()` statements; use `logging.info()`
- [ ] Diffs reviewed before merge to `main`

**Milestone 1 Gate:** All 8 work orders complete + integrated + load tests pass → Proceed to Milestone 2 (EDA + ML Foundation)

---

**Document Version:** 1.0  
**Created:** 2026-10-12  
**Ready for Dispatch:** YES
