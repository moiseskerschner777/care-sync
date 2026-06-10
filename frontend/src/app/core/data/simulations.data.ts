import { SimulationScenario } from '../models/simulation.model';

export const SIMULATION_SCENARIOS: SimulationScenario[] = [
  {
    id: 1,
    title: 'Cache MISS — RefLab FHIR Bundle',
    description: 'First request with ONC001 (non-performable exam). The agent has no cached schema — it indexes the RefLab integration docs, invokes the LLM to build a FHIR R4 Bundle, sends it, and caches the result on success.',
    tag: 'Cache MISS',
    payload: {
      "patient_id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
      "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
      "priority": "ROUTINE",
      "notes": "Test 1 — cache miss, doc_reader builds FHIR Bundle",
      "items": [{ "exam_code": "ONC001", "exam_name": "Marcadores Tumorais" }]
    }
  },
  {
    id: 2,
    title: 'Cache HIT — No LLM',
    description: 'Same operation with different patient/practitioner values and GEN001. The agent finds the cached schema from a previous request and replays it directly — no LLM call, ~55ms response.',
    tag: 'Cache HIT',
    payload: {
      "patient_id": "e36e8749-a762-45ea-bd6b-63a5745d6e07",
      "practitioner_id": "8853e3c3-d0f9-469f-ae48-7813dc83b8ec",
      "priority": "URGENT",
      "notes": "Test 2 — cache hit, no doc_reader",
      "items": [{ "exam_code": "GEN001", "exam_name": "Teste Genetico" }]
    }
  },
  {
    id: 3,
    title: 'Error — Unknown LOINC (ORIGIN_A)',
    description: 'ERR-LOINC is not a valid LOINC code. RefLab rejects with 404 "LOINC code unknown". The Error Checker searches the LabCore source code, integration docs, and IRIS database, then diagnoses the root cause as ORIGIN_A (LabCore data/mapping issue).',
    tag: 'Error',
    payload: {
      "patient_id": "664d2678-29ce-450e-ab50-bd463364ded6",
      "practitioner_id": "35ca797f-5099-479d-91d5-fbe12a125b90",
      "priority": "ROUTINE",
      "notes": "Test 3 — codebase error, unknown LOINC in RefLab",
      "items": [{ "exam_code": "ERR-LOINC", "exam_name": "Unknown LOINC test (simulator)" }]
    }
  },
  {
    id: 4,
    title: 'Contract — VitaCare Covenant Expired',
    description: 'Uses a performable exam (HEM001) so only VitaCare is routed. The covenant_id ERR-EXPIRED triggers VitaCare\'s expired plan simulator, returning 403 "Covenant plan is not active". The Error Checker diagnoses the contract violation as origin CONTRATO.',
    tag: 'Contract',
    payload: {
      "patient_id": "11c5be47-3215-4890-a79f-9c2b2293a85e",
      "practitioner_id": "0f7f838f-5bbd-43b7-951c-02582e4272a3",
      "priority": "ROUTINE",
      "covenant_id": "ERR-EXPIRED",
      "notes": "Test 4 — VitaCare covenant expired",
      "items": [{ "exam_code": "HEM001", "exam_name": "Hemograma" }]
    }
  }
];
