import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

from config import PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DBNAME
def get_db_conn() -> connection:
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=PG_DBNAME
    )


def close_conn(conn: connection | None):
    if conn:
        conn.close()


# 同步包装：自动开连接、提交、回滚、关闭
def with_db(callback):
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        res = callback(cur, conn)
        conn.commit()
        return res
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        close_conn(conn)
