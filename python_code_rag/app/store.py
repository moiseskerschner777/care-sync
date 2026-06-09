import iris, logging
from app.config import IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, IRIS_USERNAME, IRIS_PASSWORD, EMBED_DIM

logger = logging.getLogger(__name__)

def get_connection():
    logger.info("connecting to IRIS at %s:%d/%s as %s", IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, IRIS_USERNAME)
    conn = iris.connect(IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, IRIS_USERNAME, IRIS_PASSWORD)
    logger.info("connected to IRIS successfully")
    return conn


def ensure_table(conn, collection: str):
    logger.info("ensuring table RAG_%s exists", collection)
    cur = conn.cursor()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS RAG_{collection} (
            chunk_id    VARCHAR(40)   NOT NULL,
            file        VARCHAR(500),
            type        VARCHAR(20),
            name        VARCHAR(255),
            decorator   VARCHAR(500),
            start_line  INTEGER,
            end_line    INTEGER,
            "module"    VARCHAR(500),
            text        LONGVARCHAR,
            embedding   VECTOR(DOUBLE, {EMBED_DIM})
        )
    """)

    try:
        cur.execute(f"ALTER TABLE RAG_{collection} ADD COLUMN decorator VARCHAR(500)")
    except Exception as exc:
        logger.debug("decorator column may already exist: %s", exc)

    try:
        cur.execute(f"""
            CREATE INDEX HNSWIdx_{collection}
            ON RAG_{collection} (embedding)
            AS HNSW(Distance='Cosine')
        """)
        logger.info("created HNSW cosine index on RAG_%s", collection)
    except Exception as exc:
        logger.warning("could not create HNSW index on RAG_%s: %s", collection, exc)

    conn.commit()
    logger.info("table RAG_%s ready", collection)


def delete_collection(conn, collection: str):
    cur = conn.cursor()
    cur.execute(f"DELETE FROM RAG_{collection}")
    conn.commit()


def collection_exists(conn, collection: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'RAG_{collection}'")
    return cur.fetchone() is not None


def insert_chunks(conn, collection: str, chunks: list, vectors: list[list[float]]):
    if vectors:
        logger.info("inserting %d chunks into RAG_%s (vector_dim=%d)", len(chunks), collection, len(vectors[0]))
    else:
        logger.info("inserting %d chunks into RAG_%s (no vectors)", len(chunks), collection)
    cur = conn.cursor()
    batch_size = 100
    inserted = 0
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch_vectors = vectors[i:i+batch_size]
        for chunk, vec in zip(batch_chunks, batch_vectors):
            vec_str = ",".join(str(v) for v in vec)
            sql = f"""
                INSERT INTO RAG_{collection}
                (chunk_id, file, type, name, decorator, start_line, end_line, "module", text, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, TO_VECTOR('{vec_str}'))
            """
            try:
                cur.execute(sql, [
                    chunk.id,
                    chunk.file,
                    chunk.type,
                    chunk.name,
                    chunk.decorator,
                    chunk.start_line,
                    chunk.end_line,
                    chunk.module,
                    chunk.text,
                ])
                inserted += 1
            except Exception as exc:
                logger.error("failed to insert chunk %s into RAG_%s: %s", chunk.id, collection, exc)
                logger.error("  vector_dim=%d file=%s type=%s name=%s", len(vec), chunk.file, chunk.type, chunk.name)
    conn.commit()
    if inserted < len(chunks):
        logger.warning("inserted only %d/%d chunks into RAG_%s", inserted, len(chunks), collection)
    else:
        logger.info("inserted %d chunks into RAG_%s successfully", inserted, collection)


def list_collections(conn) -> list[str]:
    cur = conn.cursor()
    cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'RAG_%'")
    rows = cur.fetchall()
    return [row[0][4:] for row in rows]


def search(conn, collection: str, query_vec: list[float], top_k: int) -> list[dict]:
    logger.info("vector search in RAG_%s top_k=%d dim=%d", collection, top_k, len(query_vec))
    cur = conn.cursor()
    vec_str = ",".join(str(v) for v in query_vec)
    sql = f"""
        SELECT TOP ? chunk_id, file, type, name, decorator, start_line, end_line, "module", text,
               VECTOR_COSINE(TO_VECTOR(embedding), TO_VECTOR('{vec_str}')) AS score
        FROM RAG_{collection}
        ORDER BY score DESC
    """
    cur.execute(sql, [top_k])
    rows = cur.fetchall()
    logger.info("vector search returned %d results", len(rows))
    return [
        {
            "chunk_id": row[0],
            "file": row[1],
            "type": row[2],
            "name": row[3],
            "decorator": row[4],
            "start_line": row[5],
            "end_line": row[6],
            "module": row[7],
            "text": row[8],
            "score": float(row[9] or 0),
        }
        for row in rows
    ]
