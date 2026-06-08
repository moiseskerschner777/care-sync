# VitaCare Proprietary API Integration Guide

## CRITICAL — Required Fields
The following fields are ALWAYS required and must be taken
exactly from the user payload. Never generate or substitute them:

- `covenant_id` — the covenant/insurance plan identifier
- `patient_id`  — the patient identifier
- `exam_code`   — the exam being requested
- `practitioner_id` — the requesting doctor

## Request Format
POST /authorizations

{
  "covenant_id":     "<covenant_id from payload>",
  "patient_id":      "<patient_id from payload>",
  "exam_code":       "<exam_code from payload>",
  "exam_name":       "Exam Name",
  "practitioner_id": "<practitioner_id from payload>",
  "cid_code":        "<cid_code from payload>",
  "justification":   "Clinical justification"
}

## Overview
VitaCare is an external insurance validation system that uses its own proprietary REST API format. It does NOT use FHIR.

## Base URL
`http://vitacare:8002`

## Authentication
No authentication required for this environment.

## Supported Operations

### Validate Coverage
Validates insurance coverage for a medical procedure.

**Endpoint:** `POST /authorizations`

**Request Format:**
```json
{
  "patient_id": "<patient_id>",
  "exam_code": "<exam_code>",
  "practitioner_id": "<practitioner_id>"
}
```

**Field Descriptions:**
- `patient_id`: The patient identifier in the LabCore system
- `exam_code`: The exam code from the LabCore exam catalog
- `practitioner_id`: The requesting practitioner identifier

**Response Format (Approved):**
```json
{
  "status": "approved",
  "authorization_id": "<auth_id>",
  "patient_id": "<patient_id>",
  "exam_code": "<exam_code>",
  "coverage_details": {
    "copay": 0,
    "deductible_applied": false,
    "network": "in_network"
  }
}
```

**Response Format (Denied):**
```json
{
  "status": "denied",
  "patient_id": "<patient_id>",
  "exam_code": "<exam_code>",
  "reason": "Coverage not available for this procedure"
}
```

### Create Authorization (Pre-authorization Request)
**Endpoint:** `POST /authorizations`

Same as Validate Coverage — the endpoint accepts a single request format.

### Health Check
**Endpoint:** `GET /health`
**Response:** `{"status": "ok"}`

## Field Mapping Notes
- LabCore `patient_id` maps directly to VitaCare `patient_id`
- LabCore `practitioner_id` maps directly to VitaCare `practitioner_id`
- Exam codes are passed as-is from LabCore catalog
- No FHIR wrapping — send plain JSON only
- Authorization response includes VitaCare-generated `authorization_id`

## Important Rules
- Never use FHIR format with VitaCare
- Never include `resourceType` fields
- Never wrap requests in a Bundle
- VitaCare is intentionally proprietary — no FHIR resources, no OperationOutcome
- Required fields: `patient_id`, `exam_code`, `practitioner_id`
