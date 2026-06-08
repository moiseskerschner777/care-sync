#!/bin/bash
# MedBridge — FHIR Server Verification
# Run from care-sync/ root

IRIS_URL="http://localhost:52773"
FHIR_BASE="$IRIS_URL/fhir/r4"
AUTH="Authorization: Basic $(echo -n '_SYSTEM:SYS' | base64)"

echo "================================================"
echo " MedBridge — FHIR Server Check"
echo "================================================"

# 1 — CapabilityStatement
echo ""
echo "1. CapabilityStatement (server live?)"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" \
  "$FHIR_BASE/metadata" \
  -H "Accept: application/fhir+json" \
  -H "$AUTH"

# 2 — POST Patient
echo ""
echo "2. POST Patient"
PATIENT_BODY='{"resourceType":"Patient","name":[{"family":"Kerschner","given":["Moises"]}],"gender":"male","birthDate":"1990-01-01"}'
PATIENT=$(curl -s -X POST "$FHIR_BASE/Patient" \
  -H "Content-Type: application/fhir+json" \
  -H "Accept: application/fhir+json" \
  -H "$AUTH" \
  -d "$PATIENT_BODY")
PATIENT_ID=$(echo "$PATIENT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
echo "   id: $PATIENT_ID"
echo "   resourceType: $(echo $PATIENT | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('resourceType','error'))" 2>/dev/null)"

# 3 — GET Patient back
echo ""
echo "3. GET Patient/$PATIENT_ID"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" \
  "$FHIR_BASE/Patient/$PATIENT_ID" \
  -H "Accept: application/fhir+json" \
  -H "$AUTH"

# 4 — POST Task
echo ""
echo "4. POST Task (agent success write-back)"
TASK_BODY='{"resourceType":"Task","status":"completed","intent":"order","description":"MedBridge agent routed exam to RefLab","focus":{"reference":"ServiceRequest/OS-00001"}}'
TASK=$(curl -s -X POST "$FHIR_BASE/Task" \
  -H "Content-Type: application/fhir+json" \
  -H "Accept: application/fhir+json" \
  -H "$AUTH" \
  -d "$TASK_BODY")
echo "   id: $(echo $TASK | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','error'))" 2>/dev/null)"
echo "   status: $(echo $TASK | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','error'))" 2>/dev/null)"

# 5 — POST AuditEvent
echo ""
echo "5. POST AuditEvent (agent error write-back)"
AUDIT_BODY='{"resourceType":"AuditEvent","type":{"system":"http://terminology.hl7.org/CodeSystem/audit-event-type","code":"rest"},"action":"E","recorded":"2026-06-07T00:00:00Z","outcome":"8","outcomeDesc":"ORIGIN_A — exam code format mismatch","agent":[{"requestor":true,"name":"MedBridge Agent"}],"source":{"observer":{"display":"MedBridge"}}}'
AUDIT=$(curl -s -X POST "$FHIR_BASE/AuditEvent" \
  -H "Content-Type: application/fhir+json" \
  -H "Accept: application/fhir+json" \
  -H "$AUTH" \
  -d "$AUDIT_BODY")
echo "   id: $(echo $AUDIT | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','error'))" 2>/dev/null)"
echo "   outcome: $(echo $AUDIT | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('outcome','error'))" 2>/dev/null)"

# 6 — List Tasks
echo ""
echo "6. GET Task (list agent actions)"
curl -s "$FHIR_BASE/Task?_count=10" \
  -H "Accept: application/fhir+json" \
  -H "$AUTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('   total:', d.get('total', 0))
for e in d.get('entry', []):
    r = e.get('resource', {})
    print('  ', r.get('id','?'), '|', r.get('status','?'), '|', str(r.get('description',''))[:60])
" 2>/dev/null

# 7 — List AuditEvents
echo ""
echo "7. GET AuditEvent (list agent errors)"
curl -s "$FHIR_BASE/AuditEvent?_count=10" \
  -H "Accept: application/fhir+json" \
  -H "$AUTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('   total:', d.get('total', 0))
for e in d.get('entry', []):
    r = e.get('resource', {})
    print('  ', r.get('id','?'), '|', r.get('outcome','?'), '|', str(r.get('outcomeDesc',''))[:60])
" 2>/dev/null

# 8 — raw response check if writes are failing
echo ""
echo "8. Raw POST Patient response (debug)"
curl -s -X POST "$FHIR_BASE/Patient" \
  -H "Content-Type: application/fhir+json" \
  -H "Accept: application/fhir+json" \
  -H "$AUTH" \
  -d "$PATIENT_BODY" | head -c 300

echo ""
echo ""
echo "================================================"
echo " Done"
echo "================================================"
