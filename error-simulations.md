# Error Simulation — curl Requests

This document contains 20 HTTP curl requests that simulate realistic error scenarios
across the three services in this system:

| Service   | Port | Role                              |
|-----------|------|-----------------------------------|
| core-lab  | 8000 | Internal lab management system    |
| ref-lab   | 8001 | External reference lab (FHIR R4)  |
| vita-care | 8002 | Health insurance authorization    |

---

## CORE-LAB (port 8000) — Internal Errors

---

### 01 — Patient not found (404)
**Scenario:** The service request references a patient UUID that does not exist in the core-lab
database. This can happen when a patient was registered in an external system but not yet
imported into core-lab.

```bash
curl -s -X GET http://localhost:8000/patients/00000000-0000-0000-0000-000000000000 \
  -H "Accept: application/json" | jq
```

**Expected:** `404 Not Found` — `"Patient not found"`

---

### 02 — Practitioner not found (404)
**Scenario:** A doctor's ID was typed incorrectly when creating a service request.
Core-lab cannot find the practitioner in its registry.

```bash
curl -s -X GET http://localhost:8000/practitioners/00000000-dead-beef-0000-000000000000 \
  -H "Accept: application/json" | jq
```

**Expected:** `404 Not Found` — `"Practitioner not foundxxx"`

---

### 03 — Exam code not in catalog (404)
**Scenario:** The receptionist typed an exam code that does not exist in the lab catalog.
The lab cannot accept a service request for an unknown exam.

```bash
curl -s -X GET http://localhost:8000/exam-catalog/XXXX999 \
  -H "Accept: application/json" | jq
```

**Expected:** `404 Not Found` — `"Exam not found"`

---

### 04 — Service request not found (404)
**Scenario:** A frontend tries to fetch a service request using a stale or incorrect ID
(e.g., an ID copied from a different environment).

```bash
curl -s -X GET http://localhost:8000/service-requests/nonexistent-id \
  -H "Accept: application/json" | jq
```

**Expected:** `404 Not Found`

---

### 05 — Service request with non-existent patient (422)
**Scenario:** A new service request is submitted with a `patient_id` that does not exist
in the database. The foreign key constraint in core-lab will reject the insertion.

```bash
curl -s -X POST http://localhost:8000/service-requests \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "00000000-0000-0000-0000-000000000000",
    "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
    "priority": "ROUTINE",
    "notes": null,
    "items": [
      { "exam_code": "HEM001", "exam_name": "Hemograma" }
    ]
  }' | jq
```

**Expected:** `422 Unprocessable Entity` — patient FK violation

---

### 06 — Double cancellation of a service request (422)
**Scenario:** The same service request is cancelled twice. Core-lab must reject the second
cancellation because the order is already in `CANCELLED` status — re-cancelling it makes
no sense and could indicate a double-click bug on the frontend.

```bash
curl -s -X PUT http://localhost:8000/service-requests/6f9036b2-7130-47a5-9574-2bf5ce213fc7/cancel \
  -H "Accept: application/json" | jq
```

**Expected:** `422 Unprocessable Entity` — already cancelled

---

### 07 — Cancel a non-existent service request (404)
**Scenario:** The cancellation endpoint is called with an ID that never existed.
This could happen if a webhook fires twice and the second call arrives after the record
was already deleted.

```bash
curl -s -X PUT http://localhost:8000/service-requests/nonexistent-id/cancel \
  -H "Accept: application/json" | jq
```

**Expected:** `404 Not Found`

---

## REF-LAB (port 8001) — FHIR R4 External Lab Errors

---

### 08 — Patient CPF mismatch (422)
**Scenario:** The patient's CPF (Brazilian tax ID) sent in the ServiceRequest does not match
the document registered in the reference lab. The lab cannot process the exam without
confirmed patient identity.

```bash
curl -s -X POST http://localhost:8001/fhir/r4/ServiceRequest \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "ServiceRequest",
    "subject": { "reference": "Patient/ERR-CPF" },
    "code": { "coding": [{ "system": "http://loinc.org", "code": "HEM001", "display": "Hemograma" }] }
  }' | jq
```

**Expected:** `422 Unprocessable Entity` — FHIR `OperationOutcome` identity error

---

### 09 — Discontinued exam code (410)
**Scenario:** The doctor requested an exam that was retired from the reference lab's
catalog. The LOINC code is no longer valid and the lab cannot accept orders for it.
The `410 Gone` status signals that the resource existed but has been permanently removed.

```bash
curl -s -X POST http://localhost:8001/fhir/r4/ServiceRequest \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "ServiceRequest",
    "subject": { "reference": "Patient/PAC-001" },
    "code": { "coding": [{ "system": "http://loinc.org", "code": "ERR-DISCONTINUED", "display": "Exam Discontinued" }] }
  }' | jq
```

**Expected:** `410 Gone` — FHIR `OperationOutcome` with code `"gone"`

---

### 10 — Wrong tube type used for blood collection (422)
**Scenario:** The blood sample was collected in the wrong tube (e.g., EDTA tube was used
instead of a gel-separator tube). The reference lab rejects the specimen before analysis.

```bash
curl -s -X POST http://localhost:8001/fhir/r4/ServiceRequest \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "ServiceRequest",
    "subject": { "reference": "Patient/PAC-001" },
    "code": { "coding": [{ "system": "http://loinc.org", "code": "HEM001", "display": "Hemograma" }] },
    "specimen": [{ "reference": "Specimen/ERR-TUBE" }]
  }' | jq
```

**Expected:** `422 Unprocessable Entity` — `"Wrong tube type"`

---

### 11 — Hemolyzed sample rejected (422)
**Scenario:** The blood sample arrived hemolyzed (red blood cells ruptured during transport).
Hemolysis contaminates the serum and invalidates biochemistry results. The lab rejects
the specimen and requires a new collection.

```bash
curl -s -X POST http://localhost:8001/fhir/r4/ServiceRequest \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "ServiceRequest",
    "subject": { "reference": "Patient/PAC-001" },
    "code": { "coding": [{ "system": "http://loinc.org", "code": "HEM001", "display": "Hemograma" }] },
    "specimen": [{ "reference": "Specimen/ERR-HEMOLYZED" }]
  }' | jq
```

**Expected:** `422 Unprocessable Entity` — `"Hemolyzed sample"`

---

### 12 — Temperature deviation during transport (422)
**Scenario:** The sample was transported outside the required temperature range
(e.g., a frozen sample thawed in transit). Thermal deviation compromises test integrity.

```bash
curl -s -X POST http://localhost:8001/fhir/r4/ServiceRequest \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "ServiceRequest",
    "subject": { "reference": "Patient/PAC-001" },
    "code": { "coding": [{ "system": "http://loinc.org", "code": "GLI001", "display": "Glicemia" }] },
    "specimen": [{ "reference": "Specimen/ERR-TEMPERATURE" }]
  }' | jq
```

**Expected:** `422 Unprocessable Entity` — `"Temperature deviation"`

---

### 13 — Order placed after daily collection cutoff (422)
**Scenario:** The service request was sent after the reference lab's daily cutoff time
(e.g., after 18:00). The lab cannot guarantee next-day results and rejects late orders.

```bash
curl -s -X POST http://localhost:8001/fhir/r4/ServiceRequest \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "ServiceRequest",
    "id": "ERR-CUTOFF",
    "subject": { "reference": "Patient/PAC-001" },
    "code": { "coding": [{ "system": "http://loinc.org", "code": "HEM001", "display": "Hemograma" }] }
  }' | jq
```

**Expected:** `422 Unprocessable Entity` — `"Order placed after daily cutoff"`

---

### 14 — Duplicate order detected (409)
**Scenario:** The same order ID is submitted twice in the same day (e.g., a retry loop
sent the request twice after a network timeout). The lab detects the duplicate and
rejects the second submission to prevent double billing and double processing.
> Send this request twice — first call returns 201, second call returns 409.

```bash
curl -s -X POST http://localhost:8001/fhir/r4/ServiceRequest \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "ServiceRequest",
    "id": "ERR-DUPLICATE-ORDER",
    "subject": { "reference": "Patient/PAC-001" },
    "code": { "coding": [{ "system": "http://loinc.org", "code": "HEM001", "display": "Hemograma" }] }
  }' | jq
```

**Expected (2nd call):** `409 Conflict` — `"Duplicate order same day"`

---

### 15 — Cancel race condition — sample already in analyzer (409)
**Scenario:** Core-lab sends a cancellation request at the exact moment the reference lab
starts processing the sample on the analyzer. The lab cannot stop mid-analysis and
returns a conflict.

```bash
curl -s -X POST http://localhost:8001/fhir/r4/ServiceRequest \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "ServiceRequest",
    "id": "ERR-CANCEL-RACE",
    "subject": { "reference": "Patient/PAC-001" },
    "code": { "coding": [{ "system": "http://loinc.org", "code": "HEM001", "display": "Hemograma" }] }
  }' | jq
```

**Expected:** `409 Conflict` — `"Cancel during processing"`

---

### 16 — Partial batch acceptance (207)
**Scenario:** A batch of 3 exams is sent to the reference lab. The lab accepts 2 items
but rejects the 3rd because the exam code is not in its catalog. The `207 Multi-Status`
response reports per-item outcomes so core-lab can handle each item individually.

```bash
curl -s -X POST http://localhost:8001/fhir/r4/ServiceRequest \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "ServiceRequest",
    "subject": { "reference": "Patient/PAC-001" },
    "code": { "coding": [{ "system": "http://loinc.org", "code": "HEM001", "display": "Hemograma" }] },
    "extension": [{ "url": "batch_id", "valueString": "ERR-PARTIAL" }]
  }' | jq
```

**Expected:** `207 Multi-Status` — 2 accepted, 1 rejected with reason `"exam not available in RefLab catalog"`

---

### 17 — Cancel after result already signed (422)
**Scenario:** The doctor tries to cancel a service request after the reference lab has
already issued and digitally signed the DiagnosticReport. A signed result cannot be
retroactively cancelled.

```bash
curl -s -X DELETE http://localhost:8001/fhir/r4/ServiceRequest/ERR-RESULT-ISSUED \
  -H "Accept: application/json" | jq
```

**Expected:** `422 Unprocessable Entity` — `"DiagnosticReport already signed"`

---

### 18 — Cancel while sample is being processed (409)
**Scenario:** A cancellation request arrives while the sample is actively running on the
analyzer. The lab system cannot interrupt the hardware mid-run and rejects the
cancellation with a conflict.

```bash
curl -s -X DELETE http://localhost:8001/fhir/r4/ServiceRequest/ERR-PROCESSING \
  -H "Accept: application/json" | jq
```

**Expected:** `409 Conflict` — `"Sample already in analyzer"`

---

## VITA-CARE (port 8002) — Health Insurance Authorization Errors

---

### 19 — Patient not enrolled in health plan (404)
**Scenario:** Core-lab tries to request pre-authorization from VitaCare for a patient
who is not registered as a beneficiary in that health plan. The patient may have switched
plans or their registration is pending in VitaCare's system.

```bash
curl -s -X POST http://localhost:8002/authorizations \
  -H "Content-Type: application/json" \
  -d '{
    "covenant_id": "ERR-PATIENT-NOT-ENROLLED",
    "patient_id": "PAC-001",
    "exam_code": "HEM001",
    "exam_name": "Hemograma Completo",
    "practitioner_id": "DR-001",
    "cid_code": "Z00.0",
    "justification": "Rotina anual"
  }' | jq
```

**Expected:** `404 Not Found` — `"Patient not found in VitaCare"`

---

### 20 — CID code does not justify the requested exam (422)
**Scenario:** The health plan's rules engine evaluates the CID-10 (diagnosis code) against
the requested exam. The submitted CID code does not clinically justify this exam — for
example, requesting a Marcadores Tumorais panel under a routine check-up CID when the
plan requires an oncology-related CID for that exam.

```bash
curl -s -X POST http://localhost:8002/authorizations \
  -H "Content-Type: application/json" \
  -d '{
    "covenant_id": "ERR-CID",
    "patient_id": "PAC-001",
    "exam_code": "ONC001",
    "exam_name": "Marcadores Tumorais",
    "practitioner_id": "DR-001",
    "cid_code": "Z00.0",
    "justification": "Rotina anual"
  }' | jq
```

**Expected:** `422 Unprocessable Entity` — `"CID code does not justify this exam"`

---

## Summary Table

| # | Service   | Method | Endpoint                                              | Trigger               | Expected Status |
|---|-----------|--------|-------------------------------------------------------|-----------------------|-----------------|
| 01 | core-lab | GET    | /patients/{id}                                       | Unknown UUID          | 404             |
| 02 | core-lab | GET    | /practitioners/{id}                                  | Unknown UUID          | 404             |
| 03 | core-lab | GET    | /exam-catalog/{code}                                 | Unknown exam code     | 404             |
| 04 | core-lab | GET    | /service-requests/{id}                               | Unknown ID            | 404             |
| 05 | core-lab | POST   | /service-requests                                    | Non-existent patient  | 422             |
| 06 | core-lab | PUT    | /service-requests/{id}/cancel                        | Already cancelled     | 422             |
| 07 | core-lab | PUT    | /service-requests/nonexistent-id/cancel              | Unknown ID            | 404             |
| 08 | ref-lab  | POST   | /fhir/r4/ServiceRequest                              | ERR-CPF               | 422             |
| 09 | ref-lab  | POST   | /fhir/r4/ServiceRequest                              | ERR-DISCONTINUED      | 410             |
| 10 | ref-lab  | POST   | /fhir/r4/ServiceRequest                              | ERR-TUBE              | 422             |
| 11 | ref-lab  | POST   | /fhir/r4/ServiceRequest                              | ERR-HEMOLYZED         | 422             |
| 12 | ref-lab  | POST   | /fhir/r4/ServiceRequest                              | ERR-TEMPERATURE       | 422             |
| 13 | ref-lab  | POST   | /fhir/r4/ServiceRequest                              | ERR-CUTOFF            | 422             |
| 14 | ref-lab  | POST   | /fhir/r4/ServiceRequest                              | ERR-DUPLICATE-ORDER   | 409 (2nd call)  |
| 15 | ref-lab  | POST   | /fhir/r4/ServiceRequest                              | ERR-CANCEL-RACE       | 409             |
| 16 | ref-lab  | POST   | /fhir/r4/ServiceRequest                              | ERR-PARTIAL           | 207             |
| 17 | ref-lab  | DELETE | /fhir/r4/ServiceRequest/ERR-RESULT-ISSUED            | Signed result         | 422             |
| 18 | ref-lab  | DELETE | /fhir/r4/ServiceRequest/ERR-PROCESSING               | Sample in analyzer    | 409             |
| 19 | vita-care | POST  | /authorizations                                      | ERR-PATIENT-NOT-ENROLLED | 404          |
| 20 | vita-care | POST  | /authorizations                                      | ERR-CID               | 422             |
