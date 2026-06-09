#docker compose exec iris iris session IRIS -U USER <<'EOF'
#&sql(DELETE FROM labcore.service_request_item)
#&sql(DELETE FROM labcore.service_request)
#&sql(DELETE FROM labcore.exam_catalog)
#&sql(DELETE FROM labcore.practitioner)
#&sql(DELETE FROM labcore.patient)
#&sql(DELETE FROM SQLUser.agent_knowledge_base)
#&sql(DELETE FROM SQLUser.agent_mapping_cache)
#&sql(DELETE FROM SQLUser.RAG_core_lab)
#halt
#EOF
#
#docker compose down --remove-orphans
#docker network prune -f
#docker compose up


docker compose down -v --remove-orphans
docker network prune -f
docker compose up --build
