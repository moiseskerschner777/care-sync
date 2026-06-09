import iris
from app.config import IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, IRIS_USERNAME, IRIS_PASSWORD

def get_connection():
    return iris.connect(IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, IRIS_USERNAME, IRIS_PASSWORD)


def ensure_table(conn, collection: str):
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
            embedding   VECTOR(DOUBLE, 1024)
        )
    """)

    try:
        cur.execute(f"ALTER TABLE RAG_{collection} ADD COLUMN decorator VARCHAR(500)")
    except Exception:
        pass

    try:
        cur.execute(f"""
            CREATE INDEX HNSWIdx_{collection}
            ON RAG_{collection} (embedding)
            AS HNSW(Distance='Cosine')
        """)
    except Exception:
        pass

    conn.commit()


def delete_collection(conn, collection: str):
    cur = conn.cursor()
    cur.execute(f"DELETE FROM RAG_{collection}")
    conn.commit()


def collection_exists(conn, collection: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'RAG_{collection}'")
    return cur.fetchone() is not None


def insert_chunks(conn, collection: str, chunks: list, vectors: list[list[float]]):
    cur = conn.cursor()
    batch_size = 100
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
    conn.commit()


def list_collections(conn) -> list[str]:
    cur = conn.cursor()
    cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'RAG_%'")
    rows = cur.fetchall()
    return [row[0][4:] for row in rows]


def search(conn, collection: str, query_vec: list[float], top_k: int) -> list[dict]:
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
