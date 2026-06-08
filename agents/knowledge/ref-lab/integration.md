# RefLab FHIR R4 Integration Guide

## Overview
RefLab is an external reference laboratory system that uses FHIR R4 protocol. All API calls must use FHIR R4 resource formats.

## Base URL
`http://reflab:8001/fhir/r4`

## Authentication
No authentication required for this environment.

## Supported Operations

### Create Service Request (Exam Order)
Creates a new exam order in RefLab.

**Endpoint:** `POST /fhir/r4/ServiceRequest`

**Request Format (FHIR Bundle):**
```json
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "resource": {
        "resourceType": "ServiceRequest",
        "status": "active",
        "intent": "order",
        "code": {
          "coding": [
            {
              "system": "http://ref-lab.org/exam-codes",
              "code": "<exam_code>"
            }
          ]
        },
        "subject": {
          "reference": "Patient/<patient_id>"
        },
        "requester": {
          "reference": "Practitioner/<practitioner_id>"
        }
      }
    }
  ]
}
```

**Field Descriptions:**
- `exam_code`: The exam identifier from the LabCore exam catalog
- `patient_id`: The patient identifier in LabCore system
- `practitioner_id`: The requesting practitioner identifier

**Response Format (FHIR Bundle):**
```json
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "resource": {
        "resourceType": "ServiceRequest",
        "id": "<ref_lab_id>",
        "status": "active",
        "intent": "order",
        "code": {
          "coding": [
            {
              "system": "http://ref-lab.org/exam-codes",
              "code": "<exam_code>"
            }
          ]
        }
      }
    }
  ]
}
```

**Error Response:**
```json
{
  "resourceType": "OperationOutcome",
  "issue": [
    {
      "severity": "error",
      "code": "invalid",
      "details": {
        "text": "Error description"
      }
    }
  ]
}
```

### Health Check
**Endpoint:** `GET /health`
**Response:** `{"status": "ok"}`

## Field Mapping Notes
- LabCore `patient_id` maps to FHIR `Patient/<id>` reference
- LabCore `practitioner_id` maps to FHIR `Practitioner/<id>` reference
- Exam codes from LabCore catalog map to RefLab coding system `http://ref-lab.org/exam-codes`
- All requests must be wrapped in a FHIR Bundle of type `collection`
- Response contains the RefLab-assigned ID for the created ServiceRequest

## Important Rules
- Always use FHIR R4 format
- Never send proprietary formats to RefLab
- Required fields: `status`, `intent`, `code`, `subject`, `requester`
- The `status` must be `active` for new orders
- The `intent` must be `order`
