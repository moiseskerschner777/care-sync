# 1. clear vitacare knowledge base
docker compose exec agents python -c "
from database import SessionLocal
from models.knowledge_base import KnowledgeBase
db = SessionLocal()
db.query(KnowledgeBase).filter(KnowledgeBase.system_target == 'vitacare').delete()
db.commit()
db.close()
print('cleared')
"

# 2. clear vitacare cache so Doc Reader runs again
docker compose exec agents python -c "
from database import SessionLocal
from models.mapping_cache import MappingCache
db = SessionLocal()
db.query(MappingCache).filter(MappingCache.system_target == 'vitacare').delete()
db.commit()
db.close()
print('cleared')
"

# 3. send the CAT4 request
curl -X POST http://localhost:8003/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "validate_coverage",
    "system_target": "vitacare",
    "payload": {
      "covenant_id": "ERR-EXPIRED",
      "patient_id": "PAC-001",
      "exam_code": "HEM001",
      "practitioner_id": "DR-001",
      "cid_code": "Z00.0"
    }
  }'
