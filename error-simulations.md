# Error Simulation Scenarios — Agent Capture

## How the pipeline works

Every request starts at **core-lab** (`POST /service-requests`).
After core-lab persists the order, it fires a background thread that calls the **agent**.
The agent then routes to the external system. When the external system returns an error,
the agent captures it, deduplicates it, and runs LLM diagnosis.

```
curl → core-lab:8000/service-requests
            ↓  (background thread via agent_trigger.py)
       agents:8003/agent/invoke
            ↓
       ref-lab:8001/fhir/r4/ServiceRequest   (if any exam has can_perform=False)
       vita-care:8002/authorizations          (if covenant_id is present)
            ↓  (on non-2xx response)
       dedup_check → error_checker (LLM) → write_audit_event
```

### Routing rules (from `core-lab/services/agent_trigger.py`)

| Condition | Routed to |
|---|---|
| Any exam in the order has `can_perform=False` in the catalog | `reflab` |
| `covenant_id` is set in the request body | `vitacare` |

### Exam codes that route to ref-lab (`can_perform=False` in seed data)

| Code | Name |
|---|---|
| `ONC001` | Marcadores Tumorais |
| `GEN001` | Teste Genético |
| `CUL001` | Cultura e Antibiograma |
| `ERR-LOINC` | Teste LOINC desconhecido (error simulator) |

### Seed IDs used in these requests

| Type | ID | Name |
|---|---|---|
| Patient | `11c5be47-3215-4890-a79f-9c2b2293a85e` | Ana Paula Silva |
| Patient | `e36e8749-a762-45ea-bd6b-63a5745d6e07` | Carlos Eduardo Oliveira |
| Patient | `664d2678-29ce-450e-ab50-bd463364ded6` | Mariana Souza |
| Practitioner | `0f7f838f-5bbd-43b7-951c-02582e4272a3` | Dra. Helena Martins |
| Practitioner | `8853e3c3-d0f9-469f-ae48-7813dc83b8ec` | Dr. Ricardo Menezes |
| Practitioner | `35ca797f-5099-479d-91d5-fbe12a125b90` | Dra. Camila Azevedo |

### How error triggers reach external systems

**Ref-lab identity errors** — The agent injects `patient_id` into the FHIR payload as
`"subject": { "reference": "Patient/{patient_id}" }`. Ref-lab extracts the bare ID and checks
it against the identity trigger table in `ref-lab/simulators/identity.py`. Sending a trigger
string as `patient_id` in the core-lab request is enough to propagate it all the way through.

**Ref-lab exam errors** — The agent injects `exam_code` into the FHIR payload as the LOINC
coding code. `ERR-LOINC` is already registered in the catalog with `can_perform=False`,
so it routes to ref-lab and triggers the exam error check.

**VitaCare errors** — The agent passes `covenant_id` directly to vita-care's `/authorizations`
endpoint. Vita-care's pipeline checks it against the trigger table in
`vita-care/simulators/covenant.py`. Any value from that table sent as `covenant_id` fires the
corresponding error.

---

## Group A — Ref-Lab: Exam Catalog Errors

### 01 — Unknown LOINC code in RefLab catalog

**Why this error happens:** `ERR-LOINC` is registered in core-lab's exam catalog with
`can_perform=False`, so it is correctly routed to ref-lab. However, ref-lab does not recognize
this LOINC code in its own catalog and rejects the order. The agent should classify this as
**ORIGIN_B** (ref-lab rejected a code that exists in LabCore) or escalate to **ORIGIN_A** if the
exam code should never have been sent externally.

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
    "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
    "priority": "ROUTINE",
    "notes": "Exam exists in LabCore catalog but LOINC code is unknown in RefLab",
    "items": [
      { "exam_code": "ERR-LOINC" }
    ]
  }'
```

**Flow:** core-lab → agent → ref-lab `check_exam` → `ERR-LOINC` match
**Expected error from ref-lab:** `HTTP 404` — `"LOINC code unknown in RefLab catalog"`

---

## Group B — Ref-Lab: Patient Identity Errors

> All requests below use an error trigger string as `patient_id`. Core-lab does not validate
> `patient_id` against the database, so it propagates to the agent payload, which injects it
> into the FHIR resource as `Patient/{patient_id}`. Ref-lab strips the prefix and checks the
> bare ID against `ref-lab/simulators/identity.py`.

### 02 — Patient name with accent causes normalization mismatch

**Why this error happens:** The patient was registered in core-lab with an accented name
(e.g., "João"). When ref-lab normalizes the name to ASCII for its internal index, the result
does not match what was originally indexed. The agent should classify this as **ORIGIN_A**
(data quality issue at registration — core-lab did not normalize before sending).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "ERR-ACCENT",
    "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
    "priority": "ROUTINE",
    "notes": "Patient name contains accented characters — RefLab normalization fails",
    "items": [
      { "exam_code": "ONC001" }
    ]
  }'
```

**Flow:** core-lab → agent → ref-lab `check_identity` → `ERR-ACCENT` match
**Expected error from ref-lab:** `HTTP 422` — `"Patient name has accent — normalized version does not match"`

---

### 03 — CPF vs RG document type conflict

**Why this error happens:** The patient was registered with a CPF number but the document
type field was set to RG (or vice versa). Ref-lab validates both fields together and rejects
the mismatch. The agent should classify this as **ORIGIN_A** (incorrect data entered at
registration — LabCore accepted a contradictory document type + number combination).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "ERR-DOC-TYPE",
    "practitioner_id": "8853e3c3-d0f9-469f-ae48-7813dc83b8ec",
    "priority": "URGENT",
    "notes": "Document type field is RG but the number provided is a CPF",
    "items": [
      { "exam_code": "ONC001" }
    ]
  }'
```

**Flow:** core-lab → agent → ref-lab `check_identity` → `ERR-DOC-TYPE` match
**Expected error from ref-lab:** `HTTP 422` — `"CPF vs RG document type conflict"`

---

### 04 — Date of birth format mismatch

**Why this error happens:** Core-lab stores birth date as `DD/MM/YYYY` (Brazilian format),
but the integration contract with ref-lab requires ISO 8601 (`YYYY-MM-DD`). The agent
sent the date in the wrong format. The agent should classify this as **CONTRACT** (the
serialization format defined in the integration documentation was not followed).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "ERR-DOB-FORMAT",
    "practitioner_id": "35ca797f-5099-479d-91d5-fbe12a125b90",
    "priority": "ROUTINE",
    "notes": "Birth date serialized as DD/MM/YYYY instead of ISO 8601 YYYY-MM-DD",
    "items": [
      { "exam_code": "GEN001" }
    ]
  }'
```

**Flow:** core-lab → agent → ref-lab `check_identity` → `ERR-DOB-FORMAT` match
**Expected error from ref-lab:** `HTTP 422` — `"Date of birth format mismatch"`

---

### 05 — Duplicate patient record in RefLab

**Why this error happens:** The patient already exists in ref-lab under a different ID.
Core-lab issued a new order for them but ref-lab detects a collision on name + CPF + birth date
and refuses to create a second record. The agent should classify this as **ORIGIN_B** (ref-lab
constraint that LabCore cannot detect without a prior lookup).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "ERR-DUPLICATE",
    "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
    "priority": "ROUTINE",
    "notes": "Patient already has a record in RefLab under a different internal ID",
    "items": [
      { "exam_code": "GEN001" }
    ]
  }'
```

**Flow:** core-lab → agent → ref-lab `check_identity` → `ERR-DUPLICATE` match
**Expected error from ref-lab:** `HTTP 409` — `"Duplicate patient record in RefLab"`

---

### 06 — Gender format mismatch (M vs male)

**Why this error happens:** Core-lab stores gender as `"MALE"` / `"FEMALE"` (uppercase FHIR
enum). The FHIR payload built by the agent used a short code (`"M"` / `"F"`) instead. Ref-lab's
validator expects the full FHIR string. The agent should classify this as **CONTRACT**
(the field serialization contract between the two systems was not respected).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "ERR-GENDER",
    "practitioner_id": "8853e3c3-d0f9-469f-ae48-7813dc83b8ec",
    "priority": "STAT",
    "notes": "Gender sent as M/F abbreviation — RefLab requires full FHIR value male/female",
    "items": [
      { "exam_code": "CUL001" }
    ]
  }'
```

**Flow:** core-lab → agent → ref-lab `check_identity` → `ERR-GENDER` match
**Expected error from ref-lab:** `HTTP 422` — `"Gender format mismatch (M vs male)"`

---

### 07 — Underage patient missing guardian data

**Why this error happens:** The patient is under 18. Ref-lab requires a legal guardian name
and document to accompany any exam request for minors. Core-lab did not collect or transmit
this information. The agent should classify this as **ORIGIN_A** (LabCore accepted an order
for a minor without collecting the mandatory guardian fields).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "ERR-MINOR",
    "practitioner_id": "35ca797f-5099-479d-91d5-fbe12a125b90",
    "priority": "ROUTINE",
    "notes": "Minor patient — guardian name and document were not included in the payload",
    "items": [
      { "exam_code": "CUL001" }
    ]
  }'
```

**Flow:** core-lab → agent → ref-lab `check_identity` → `ERR-MINOR` match
**Expected error from ref-lab:** `HTTP 422` — `"Underage patient missing guardian data"`

---

### 08 — CPF check digit validation failure

**Why this error happens:** The CPF stored in core-lab has a typo — the two check digits at
the end do not pass the Receita Federal validation algorithm. Ref-lab validates CPFs before
accepting any order. The agent should classify this as **ORIGIN_A** (bad data in LabCore —
CPF should have been validated at the point of patient registration).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "ERR-CPF",
    "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
    "priority": "URGENT",
    "notes": "CPF fails Receita Federal check digit algorithm — likely a data entry error",
    "items": [
      { "exam_code": "ONC001" }
    ]
  }'
```

**Flow:** core-lab → agent → ref-lab `check_identity` → `ERR-CPF` match
**Expected error from ref-lab:** `HTTP 422` — `"CPF check digit validation failure"`

---

### 09 — Special characters corrupted in transit

**Why this error happens:** The patient name contains characters like `ç`, `ã`, `é`. The HTTP
layer transmitted the payload without enforcing UTF-8, causing the characters to be corrupted
by the time ref-lab parsed the JSON body. The agent should classify this as **INFRA** or
**CONTRACT** (encoding agreement between systems was never established or not enforced).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "ERR-ENCODING",
    "practitioner_id": "35ca797f-5099-479d-91d5-fbe12a125b90",
    "priority": "ROUTINE",
    "notes": "Patient name has accented chars — Content-Type charset was not UTF-8 at transmission",
    "items": [
      { "exam_code": "GEN001" }
    ]
  }'
```

**Flow:** core-lab → agent → ref-lab `check_identity` → `ERR-ENCODING` match
**Expected error from ref-lab:** `HTTP 422` — `"Special characters corrupted in transit"`

---

## Group C — VitaCare: Authorization Errors

> All requests below set `covenant_id` to a trigger string and use a valid internal exam
> (`HEM001`, `can_perform=True`) so only vitacare is triggered — reflab is not involved.
> VitaCare's `simulate()` checks the `covenant_id` directly against its trigger table.

### 10 — Covenant health plan is expired

**Why this error happens:** The patient's health plan was active when first registered in
core-lab but has since lapsed. VitaCare rejects any authorization for an inactive plan.
The agent should classify this as **CONTRACT** (the plan contract between patient and covenant
is no longer valid — LabCore should verify plan status before routing to VitaCare).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
    "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
    "priority": "ROUTINE",
    "covenant_id": "ERR-EXPIRED",
    "notes": "Patient plan expired — VitaCare will reject any authorization attempt",
    "items": [
      { "exam_code": "HEM001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-EXPIRED` match
**Expected error from vita-care:** `HTTP 403` — `"Covenant plan is not active"`

---

### 11 — Exam not covered by the patient's plan tier

**Why this error happens:** The exam exists in the catalog but the patient's specific plan
tier does not cover it. The patient would need an upgraded plan or an out-of-pocket
authorization. The agent should classify this as **CONTRACT** (coverage exclusion defined
by the covenant — LabCore should check coverage before ordering).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "e36e8749-a762-45ea-bd6b-63a5745d6e07",
    "practitioner_id": "8853e3c3-d0f9-469f-ae48-7813dc83b8ec",
    "priority": "ROUTINE",
    "covenant_id": "ERR-NOT-COVERED",
    "notes": "Exam is valid but excluded from coverage in this plan tier",
    "items": [
      { "exam_code": "HEM001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-NOT-COVERED` match
**Expected error from vita-care:** `HTTP 422` — `"Exam not covered by this plan"`

---

### 12 — Patient not enrolled in VitaCare

**Why this error happens:** Core-lab has a covenant_id on record for this patient, but
VitaCare has no enrollment record for them under that plan. This can happen when the plan
was cancelled before enrollment completed, or if the covenant_id was entered incorrectly
at registration. The agent should classify this as **ORIGIN_A** (stale or incorrect
covenant_id stored in LabCore).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "664d2678-29ce-450e-ab50-bd463364ded6",
    "practitioner_id": "35ca797f-5099-479d-91d5-fbe12a125b90",
    "priority": "URGENT",
    "covenant_id": "ERR-PATIENT-NOT-ENROLLED",
    "notes": "Covenant ID is set in LabCore but patient has no enrollment record in VitaCare",
    "items": [
      { "exam_code": "HEM001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-PATIENT-NOT-ENROLLED` match
**Expected error from vita-care:** `HTTP 404` — `"Patient not found in VitaCare"`

---

### 13 — Daily authorization request limit reached

**Why this error happens:** VitaCare imposes a per-clinic daily cap on authorization requests.
The clinic has already exhausted today's quota. Nothing is wrong with the data — the request
would succeed tomorrow. The agent should classify this as **ORIGIN_B** (external throttle —
no LabCore bug, retry should be scheduled for the next business window).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
    "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
    "priority": "ROUTINE",
    "covenant_id": "ERR-AUTH-LIMIT",
    "notes": "Daily authorization quota exhausted — VitaCare is rate-limiting this clinic",
    "items": [
      { "exam_code": "GLI001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-AUTH-LIMIT` match
**Expected error from vita-care:** `HTTP 429` — `"Daily authorization limit reached"`

---

### 14 — Specialist referral required before authorization

**Why this error happens:** The covenant plan requires certain exams to be requested only
after a formal specialist referral. The order came from a general practitioner without a
referral document. The agent should classify this as **CONTRACT** (a business rule defined
by the covenant that LabCore must enforce before routing the order to VitaCare).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "e36e8749-a762-45ea-bd6b-63a5745d6e07",
    "practitioner_id": "8853e3c3-d0f9-469f-ae48-7813dc83b8ec",
    "priority": "ROUTINE",
    "covenant_id": "ERR-REFERRAL",
    "notes": "GP ordered directly — plan requires a specialist referral document to be attached",
    "items": [
      { "exam_code": "COL001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-REFERRAL` match
**Expected error from vita-care:** `HTTP 422` — `"Referral from specialist required"`

---

### 15 — Clinical justification text missing

**Why this error happens:** The covenant plan mandates a free-text clinical justification for
high-complexity exams. The field was omitted or left blank in the LabCore order. The agent
should classify this as **ORIGIN_A** (LabCore did not collect the justification field that
the integration contract requires for this exam category).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "664d2678-29ce-450e-ab50-bd463364ded6",
    "practitioner_id": "35ca797f-5099-479d-91d5-fbe12a125b90",
    "priority": "URGENT",
    "covenant_id": "ERR-JUSTIFICATION",
    "notes": "Clinical justification field is empty — required for this exam category by the covenant",
    "items": [
      { "exam_code": "TSH001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-JUSTIFICATION` match
**Expected error from vita-care:** `HTTP 422` — `"Clinical justification text missing"`

---

### 16 — CID code does not justify the requested exam

**Why this error happens:** The ICD-10 / CID code on the order (e.g., Z00.0 routine check-up)
does not clinically justify the exam. VitaCare applies a CID-to-exam validation matrix to
prevent non-indicated procedures. The agent should classify this as **CONTRACT** (the clinical
indication rules defined by the covenant were not satisfied).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
    "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
    "priority": "ROUTINE",
    "covenant_id": "ERR-CID",
    "notes": "CID Z00.0 (routine check-up) does not justify this exam per covenant clinical rules",
    "items": [
      { "exam_code": "URI001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-CID` match
**Expected error from vita-care:** `HTTP 422` — `"CID code does not justify this exam"`

---

### 17 — Requesting physician not credentialed with this covenant

**Why this error happens:** The doctor who signed the order is not in VitaCare's credentialed
provider list for this specific plan. The patient may have a valid plan but the physician is
not an authorized requester under it. The agent should classify this as **ORIGIN_A** (LabCore
allowed an order from a practitioner who is not credentialed for this covenant).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "e36e8749-a762-45ea-bd6b-63a5745d6e07",
    "practitioner_id": "8853e3c3-d0f9-469f-ae48-7813dc83b8ec",
    "priority": "STAT",
    "covenant_id": "ERR-DOCTOR",
    "notes": "Dr. Ricardo Menezes is not in VitaCare credentialed provider list for this plan",
    "items": [
      { "exam_code": "HEM001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-DOCTOR` match
**Expected error from vita-care:** `HTTP 403` — `"Requesting physician not credentialed with this covenant"`

---

### 18 — Monthly exam limit reached for this patient

**Why this error happens:** The patient's plan has a monthly cap on the number of this exam
type. The patient already hit the limit and this would exceed it. VitaCare denies the
authorization. The agent should classify this as **ORIGIN_B** (plan-level restriction
LabCore cannot predict without querying VitaCare's usage history first).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "664d2678-29ce-450e-ab50-bd463364ded6",
    "practitioner_id": "35ca797f-5099-479d-91d5-fbe12a125b90",
    "priority": "ROUTINE",
    "covenant_id": "ERR-EXAM-LIMIT",
    "notes": "Patient already reached the monthly frequency limit for this exam under the plan",
    "items": [
      { "exam_code": "HEM001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-EXAM-LIMIT` match
**Expected error from vita-care:** `HTTP 429` — `"Monthly exam limit reached for this patient"`

---

### 19 — Doctor CRM not found in credentialed list

**Why this error happens:** The CRM registration number stored for the requesting physician
in LabCore does not exist in VitaCare's credentialing database. This is different from
scenario 17 — here the physician identity itself is entirely unknown to VitaCare, rather
than being known but uncredentialed for a specific plan. The agent should classify this as
**ORIGIN_A** (the CRM stored in LabCore may have a typo or wrong state).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
    "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
    "priority": "URGENT",
    "covenant_id": "ERR-CRM",
    "notes": "CRM-SC-12345 not found in VitaCare registry — possibly wrong state suffix or digit",
    "items": [
      { "exam_code": "GLI001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-CRM` match
**Expected error from vita-care:** `HTTP 403` — `"Doctor CRM not found in credentialed list"`

---

### 20 — TISS standard version mismatch

**Why this error happens:** TISS (Troca de Informações em Saúde Suplementar) is the ANS
standard for health plan data exchange in Brazil. The payload was built using TISS 3.05 but
VitaCare's endpoint now requires TISS 3.06. The version header in the message does not match
what VitaCare expects. The agent should classify this as **CONTRACT** (the integration protocol
version in LabCore was not updated after VitaCare migrated to the new TISS version).

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "e36e8749-a762-45ea-bd6b-63a5745d6e07",
    "practitioner_id": "35ca797f-5099-479d-91d5-fbe12a125b90",
    "priority": "ROUTINE",
    "covenant_id": "ERR-TISS",
    "notes": "Agent payload uses TISS 3.05 — VitaCare endpoint now requires TISS 3.06",
    "items": [
      { "exam_code": "COL001" }
    ]
  }'
```

**Flow:** core-lab → agent `validate_coverage` → vita-care `simulate_covenant` → `ERR-TISS` match
**Expected error from vita-care:** `HTTP 422` — `"TISS standard version mismatch"`

---

## Summary table

| # | Target | Trigger field | Trigger value | HTTP | Error message | Expected agent origin |
|---|---|---|---|---|---|---|
| 01 | ref-lab | `exam_code` | `ERR-LOINC` | 404 | LOINC code unknown in RefLab catalog | ORIGIN_B / ORIGIN_A |
| 02 | ref-lab | `patient_id` | `ERR-ACCENT` | 422 | Patient name accent mismatch | ORIGIN_A |
| 03 | ref-lab | `patient_id` | `ERR-DOC-TYPE` | 422 | CPF vs RG document type conflict | ORIGIN_A |
| 04 | ref-lab | `patient_id` | `ERR-DOB-FORMAT` | 422 | Date of birth format mismatch | CONTRACT |
| 05 | ref-lab | `patient_id` | `ERR-DUPLICATE` | 409 | Duplicate patient record in RefLab | ORIGIN_B |
| 06 | ref-lab | `patient_id` | `ERR-GENDER` | 422 | Gender format mismatch (M vs male) | CONTRACT |
| 07 | ref-lab | `patient_id` | `ERR-MINOR` | 422 | Underage patient missing guardian data | ORIGIN_A |
| 08 | ref-lab | `patient_id` | `ERR-CPF` | 422 | CPF check digit validation failure | ORIGIN_A |
| 09 | ref-lab | `patient_id` | `ERR-ENCODING` | 422 | Special characters corrupted in transit | INFRA / CONTRACT |
| 10 | vita-care | `covenant_id` | `ERR-EXPIRED` | 403 | Covenant plan is not active | CONTRACT |
| 11 | vita-care | `covenant_id` | `ERR-NOT-COVERED` | 422 | Exam not covered by this plan | CONTRACT |
| 12 | vita-care | `covenant_id` | `ERR-PATIENT-NOT-ENROLLED` | 404 | Patient not found in VitaCare | ORIGIN_A |
| 13 | vita-care | `covenant_id` | `ERR-AUTH-LIMIT` | 429 | Daily authorization limit reached | ORIGIN_B |
| 14 | vita-care | `covenant_id` | `ERR-REFERRAL` | 422 | Referral from specialist required | CONTRACT |
| 15 | vita-care | `covenant_id` | `ERR-JUSTIFICATION` | 422 | Clinical justification text missing | ORIGIN_A |
| 16 | vita-care | `covenant_id` | `ERR-CID` | 422 | CID code does not justify this exam | CONTRACT |
| 17 | vita-care | `covenant_id` | `ERR-DOCTOR` | 403 | Physician not credentialed with covenant | ORIGIN_A |
| 18 | vita-care | `covenant_id` | `ERR-EXAM-LIMIT` | 429 | Monthly exam limit reached | ORIGIN_B |
| 19 | vita-care | `covenant_id` | `ERR-CRM` | 403 | Doctor CRM not found in credentialed list | ORIGIN_A |
| 20 | vita-care | `covenant_id` | `ERR-TISS` | 422 | TISS standard version mismatch | CONTRACT |
