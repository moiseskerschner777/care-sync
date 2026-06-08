# MedBridge

An intelligent interoperability platform for the laboratory sector, built for the **InterSystems IRIS for Health AI Agents** contest.

---

## The Problem

Healthcare systems don't speak the same language — and someone always pays for it.

A laboratory information system (LIS) needs to route exam orders to external systems: a reference lab for exams it can't perform internally, and an insurance provider for coverage authorization. Each external system has its own protocol, its own payload format, its own error vocabulary. One uses FHIR R4. Another uses flat proprietary JSON. A third uses SOAP. None of them agree on field names, code systems, or error formats.

Today, integrating a new external system takes weeks or months. A developer reads the documentation, writes hardcoded payload builders, maps field by field, tests against the real system, and handles every error case manually. When an integration breaks in production, someone has to read the error, check the source code, check the database, cross-reference the documentation, and make a judgment call. In high-volume labs, this happens dozens of times a day — and every delay is a delay in patient care.

The root causes are always the same:

- **No standardization** — every system calls the same concept a different name (`patient_name`, `nm_paciente`, `nomeCli`)
- **Hardcoded integrations** — payload builders are written once and break silently when the contract changes
- **Opaque errors** — "exam code not found" could mean a bug in the payload, a typo in the catalog, a missing mapping, or a problem on the external system's side — and there's no way to know without manual investigation
- **Manual onboarding** — every new external system requires a new integration project

---

## What MedBridge Does

MedBridge places an AI agent between the LIS and its external systems. The agent handles the full integration lifecycle autonomously:

**Intelligent normalization**
The agent reads the integration documentation of each external system and builds the correct payload for that system's contract — without hardcoded field mappings. RefLab expects a FHIR R4 Bundle. VitaCare expects flat proprietary JSON. The agent adapts to each one from documentation alone.

**Learning from success**
Every successful operation is cached. The agent extracts the payload schema that worked and stores it in IRIS. On subsequent identical requests, it replays the cached schema directly — no LLM call, no documentation lookup, ~55ms response time. The system gets faster as it learns.

**Autonomous error diagnosis**
When an integration fails, the agent cross-references three sources simultaneously: the source code that built the payload, the integration documentation of the target system, and the LabCore database. It produces a structured diagnosis — origin, confidence score, evidence, and actionable suggestion. If confidence is below 70%, it escalates to AMBIGUOUS rather than guessing. The system knows what it doesn't know.

**Full auditability**
Every error is recorded as both a FHIR AuditEvent in IRIS's native FHIR R4 server and a structured row in a relational table — queryable, traceable, and ready for similarity search against future errors.

**Zero-code onboarding of new systems**
To add a new external system, drop an `integration.md` into `agents/knowledge/<system>/`. The agent indexes it on the first request and starts building correct payloads immediately. No code changes. No new payload builders. No redeployment.

---

## Architecture

Three systems form the integration landscape:

| System | Name | Protocol | Port | Role |
|--------|------|----------|------|------|
| A | **LabCore** | REST (proprietary) | 8000 | Main LIS — source of truth. Real FastAPI + IRIS database. |
| B | **RefLab** | FHIR R4 | 8001 | External reference lab — stateless mock, trigger-based simulation. |
| C | **VitaCare** | REST (proprietary) | 8002 | External insurance/covenant — stateless mock, trigger-based simulation. |

Plus the agent infrastructure:

| Service | Port | Role |
|---------|------|------|
| **Agent** | 8003 | LangGraph AI Agent — orchestrates everything |
| **python-code-rag** | 8004 / 8005 | MCP server — semantic search over LabCore codebase |
| **IRIS** | 1972 | Database — relational + vector storage |
| **IRIS Portal** | 52773 | Management portal |

### MCP Servers

The Error Checker Agent uses two MCP servers to gather evidence before diagnosing an error:

| MCP Server | Transport | Used by | Purpose |
|------------|-----------|---------|---------|
| **python-code-rag** | SSE (`http://python-code-rag:8004/sse`) | Error Checker | Semantic search over LabCore Python source code — finds the function that built the failing payload |
| **IRIS database** | stdio | Error Checker | Queries LabCore relational tables directly — verifies exam codes, patient records, and catalog entries |

`python-code-rag` is a standalone service that indexes all `.py` files in the LabCore codebase using AST-based chunking and vector embeddings. The Error Checker queries it with natural language and gets back the relevant functions ranked by similarity score.

RefLab and VitaCare use intentionally different protocols — RefLab speaks FHIR R4, VitaCare speaks proprietary JSON. This forces the agent to handle real-world heterogeneity, not a toy scenario.

---

## Agents

| Agent | Status | Role |
|-------|--------|------|
| **Parent Agent** | Built | Entry point — routes to Doc Reader or Error Checker based on cache state |
| **Doc Reader Agent** | Built | Reads integration docs, builds correct payload via LLM, saves to cache on success |
| **Error Checker Agent** | Built | Diagnoses error origin using codebase search (MCP), doc search (vector), and database (MCP) |
| **Reporter Agent** | Built | Saves structured diagnosis + full context to IRIS — AuditEvent (FHIR) + error_report (SQL) |

---

## How the Agent Works

Every exam order created in LabCore triggers the agent in a background thread. The agent follows a strict cache-first flow:

```
POST /service-requests  (LabCore)
        ↓
  trigger_agent()  (background thread)
        ↓
  POST /agent/invoke
        ↓
  check MappingCache  (SQL — no LLM)
        ↓
  HIT  ──→  send_direct  ──→  update use_count  ──→  done  (~55ms, zero LLM cost)
        ↓
  MISS ──→  Doc Reader Agent
                ↓
          check KnowledgeBase for system_target
          if empty → index integration docs on demand
                ↓
          vector search (embedding model)
                ↓
          LLM builds correct payload from docs
                ↓
          send to RefLab or VitaCare
                ↓
          SUCCESS ──→  save to MappingCache  ──→  done
          ERROR   ──→  Error Checker Agent
                            ↓
                      search LabCore codebase (MCP)
                      search integration docs (vector)
                      query LabCore database (MCP)
                            ↓
                      LLM diagnoses error origin:
                        ORIGIN_A  — bug or data issue in LabCore
                        ORIGIN_B  — external system rejected the request
                        CONTRACT  — business rule / contract violation
                        INFRA     — network or system failure
                        AMBIGUOUS — not enough evidence (confidence < 0.70)
                            ↓
                      Reporter Agent
                            ↓
                      write AuditEvent to IRIS FHIR R4
                      write structured row to agent_error_report (SQL)
```

**Key design rule:** The LLM is never called on a cache hit. Once the agent has seen an operation succeed, it replays the cached payload schema directly. LLM cost only occurs on the first call per operation, or when an error happens.

---

## Tech Stack

- **Python 3.11** + **FastAPI 0.115.0** — all services
- **SQLAlchemy 2.0** + **sqlalchemy-iris 0.11.2** — LabCore + Agent
- **IRIS for Health Community Edition** — relational + VECTOR database
- **LangGraph 0.2.0** — agent graph orchestration
- **LiteLLM 1.40.0** — LLM abstraction layer (provider configured via `.env`, zero code change to swap)
- **Reasoning LLM** — used by Doc Reader and Error Checker to build payloads and diagnose errors
- **Embedding model** — used to index integration docs and run vector search
- **Docker + Docker Compose** — single compose file for all services

---

## Repository Structure

```
care-sync/
├── docker-compose.yml          # all services
├── .env                        # LLM config — not committed
│
├── core-lab/                   # System A — LabCore (FastAPI + IRIS)
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   └── seed/
│
├── ref-lab/                    # System B — RefLab (FHIR R4 mock)
│   ├── routes/
│   └── simulators/
│
├── vita-care/                  # System C — VitaCare (proprietary mock)
│   ├── routes/
│   └── simulators/
│
├── agents/                     # AI Agent (LangGraph)
│   ├── agents/
│   │   ├── parent.py
│   │   ├── doc_reader.py
│   │   └── error_checker.py
│   ├── tools/
│   │   ├── http_client.py
│   │   ├── knowledge_base.py
│   │   ├── codebase.py         # MCP client for python-code-rag
│   │   └── fhir_writer.py      # writes AuditEvent + error_report to IRIS
│   ├── memory/
│   │   ├── mapping_cache.py
│   │   └── knowledge_base_indexer.py
│   └── knowledge/
│       ├── ref-lab/integration.md
│       └── vita-care/integration.md
│
└── python_code_rag/            # MCP server — semantic search over LabCore code
```

---

## Running the Project

### Prerequisites

- Docker + Docker Compose
- An embedding model accessible via API (for indexing integration docs and running vector search)
- An API key for your chosen reasoning LLM



```bash

```

### 1. Create the `.env` file

At the root of `care-sync/`, create a `.env` file:

```env
LLM_PROVIDER=<provider/model>          # reasoning LLM
LLM_API_KEY=<your_api_key>
LLM_API_BASE=

EMBEDDING_PROVIDER=<provider/model>      # embedding model — for doc indexing and vector search
EMBEDDING_API_BASE=<embedding_api_base>
```

### 2. Start all services

```bash
docker compose up -d
```

This starts LabCore, RefLab, VitaCare, the Agent, python-code-rag, and IRIS.

Wait ~30 seconds for IRIS to fully initialize on first boot.

### 3. Verify services are up

```bash
curl http://localhost:8000/health   # LabCore
curl http://localhost:8001/health   # RefLab
curl http://localhost:8002/health   # VitaCare
curl http://localhost:8003/health   # Agent
```

All should return `200 OK`.

### 4. Send a test request

Create an exam order from LabCore — this triggers the full agent flow:

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
    "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
    "priority": "ROUTINE",
    "items": [{ "exam_code": "HEM001" }]
  }'
```

Watch the agent logs:

```bash
docker compose logs -f agent
```

First call: the Doc Reader Agent runs, LLM builds the payload from integration docs, result is cached.
Second identical call: cache hit, ~55ms, zero LLM calls.

### 5. Trigger an error scenario

Send an order with a known error trigger to see the Error Checker Agent in action:

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "664d2678-29ce-450e-ab50-bd463364ded6",
    "practitioner_id": "35ca797f-5099-479d-91d5-fbe12a125b90",
    "priority": "ROUTINE",
    "items": [{ "exam_code": "ERR-LOINC" }]
  }'
```

The agent will receive a 404 from RefLab, run the Error Checker, write an `AuditEvent` to IRIS FHIR R4, and save a structured diagnosis row to `agent_error_report`.

Query the result:

```bash
curl -s -u _SYSTEM:SYS http://localhost:52773/fhir/r4/AuditEvent \
  | python3 -m json.tool
```

### 6. IRIS Management Portal

Available at `http://localhost:52773/csp/sys/UtilHome.csp`
Credentials: `_SYSTEM` / `SYS`
Namespace: `USER`

---

## Error Scenarios

62 test scenarios are available in `medbridge.http`, covering 8 error categories:

| Category | Type | Trigger field | Count |
|----------|------|---------------|-------|
| 1 | Identity errors | `patient_id` | 8 |
| 2 | Exam/clinical errors | `exam_code` | 9 |
| 3 | Sample errors | `sample_type` | 6 |
| 4 | Authorization errors | `covenant_id` (VitaCare) | 15 |
| 5 | Timing/workflow errors | `order_id` | 7 |
| 6 | Format/encoding errors | field-level | 6 |
| 7 | Partial success | `batch_id` | 5 |
| 8 | Cancellation errors | `cancel_id` | 4 |

---

## IRIS Database Tables

All tables live in the `USER` namespace, `SQLUser` schema.

| Table | Service | Contents |
|-------|---------|----------|
| `SQLUser.labcore_patient` | LabCore | Synthetic patients |
| `SQLUser.labcore_practitioner` | LabCore | Doctors |
| `SQLUser.labcore_service_request` | LabCore | Exam orders |
| `SQLUser.labcore_service_request_item` | LabCore | Individual exams per order |
| `SQLUser.labcore_exam_catalog` | LabCore | Exam catalog with routing flag |
| `SQLUser.agent_mapping_cache` | Agent | Cached payload schemas |
| `SQLUser.agent_knowledge_base` | Agent | Doc chunks with VECTOR embeddings |
| `SQLUser.agent_error_report` | Agent | Structured error diagnoses |

---
