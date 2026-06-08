what was done in this conversation, in mk-format:

    starting point:
        the Agent was already writing AuditEvent FHIR resources into IRIS on error
        a live curl confirmed the pipeline was working end-to-end

    two problems were identified in the AuditEvent output:

        - truncation:
            outcomeDesc was being cut mid-sentence
            cause: IRIS field length limit on that field
            the text ended with "it is not a FHIR " — incomplete

        - flat unstructured data:
            origin, confidence, evidence, suggestion were all flattened into one string
            not queryable — no way to filter by origin or confidence via FHIR or SQL

    decision made:
        keep AuditEvent as a lean audit trail only:
            short outcomeDesc — format: [ORIGIN] confidence=X% — system/operation
            no evidence text inside the FHIR resource

        add a parallel relational save to a new IRIS table: agent_error_report:
            - all unbounded fields as Text (LONGVARCHAR in IRIS)
            - audit_event_id column to cross-reference the FHIR resource
            - full payload_sent and raw_error with no slicing

    file identified as the target:
        agents/tools/fhir_writer.py
        write_audit_event() is the function to fix
        _post_resource() needs to return the created resource id instead of bool

    two implementation prompts were produced:
        - first: a general-scope prompt (before the file was seen)
        - second: a precise prompt targeting fhir_writer.py directly, with exact signatures, column definitions, and the HARD STOP verification step
