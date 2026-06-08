FHIRSERVER@localhost:
    query:
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'HSFHIR_X0001_S'
          AND TABLE_NAME = 'AuditEvent'
        ORDER BY ORDINAL_POSITION


    curl:
        curl -s -u _SYSTEM:SYS http://localhost:52773/fhir/r4/AuditEvent/2640 | python3 -m json.tool
        {
            "resourceType": "AuditEvent",
            "id": "2640",
            "type": {
                "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
                "code": "110106",
                "display": "Export"
            },
            "action": "E",
            "recorded": "2026-06-07T20:34:00.983645Z",
            "outcome": "8",
            "outcomeDesc": "[ORIGIN_A] confidence=100% \u2014 The payload sent to RefLab is not a FHIR Bundle as documented. The `build_reflab_payload` function in `labcore` source code constructs a proprietary dictionary with keys like `operation`, `system_target`, and `payload`, while RefLab expects a FHIR R4 Bundle with `resourceType`, `type`, `entry`, and FHIR resources. Additionally, the error shows the exam code `ERR-FORMAT` was sent, but the error message indicates a format issue (e.g., `HEM001 vs HEM-001`), suggesting the exam code itself might be ",
            "agent": [
                {
                    "who": {
                        "identifier": {
                            "value": "MedBridge Agent"
                        }
                    },
                    "requestor": true,
                    "role": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                                    "code": "AUT",
                                    "display": "author"
                                }
                            ]
                        }
                    ]
                }
            ],
            "source": {
                "observer": {
                    "identifier": {
                        "value": "MedBridge Agent"
                    }
                }
            },
            "entity": [
                {
                    "what": {
                        "identifier": {
                            "value": "reflab"
                        }
                    },
                    "type": {
                        "system": "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                        "code": "2",
                        "display": "System Object"
                    },
                    "role": {
                        "system": "http://terminology.hl7.org/CodeSystem/object-role",
                        "code": "13",
                        "display": "Security Resource"
                    },
                    "detail": [
                        {
                            "type": "operation",
                            "valueString": "create_exam"
                        },
                        {
                            "type": "payload_sent",
                            "valueString": "{\"resourceType\": \"Bundle\", \"type\": \"collection\", \"entry\": [{\"resource\": {\"resourceType\": \"ServiceRequest\", \"status\": \"active\", \"intent\": \"order\", \"code\": {\"coding\": [{\"system\": \"http://ref-lab.org/exam-codes\", \"code\": \"ERR-FORMAT\"}]}, \"subject\": {\"reference\": \"Patient/11c5be47-3215-4890-a79f-9c2b2293a85e\"}, \"requester\": {\"reference\": \"Practitioner/0f7f838f-5bbd-43b7-951c-02582e4272a3\"}}}]}"
                        }
                    ]
                }
            ],
            "meta": {
                "lastUpdated": "2026-06-07T20:34:01Z",
                "versionId": "1"
            }
        }


