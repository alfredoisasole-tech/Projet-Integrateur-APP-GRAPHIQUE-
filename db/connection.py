"""
SGE — Pool de connexions PostgreSQL (thread-safe)

Utilise psycopg2.pool.ThreadedConnectionPool pour supporter
le contexte multi-thread Flask (daemon thread) + Tkinter.
"""

import psycopg2
from psycopg2 import pool

_pool = None


def init_pool(db_config):
    """Initialise le pool de connexions PostgreSQL.

    Args:
        db_config: dict avec host, port, dbname, user, password, options.
    """
    global _pool
    if _pool is not None:
        return

    _pool = pool.ThreadedConnectionPool(
        minconn=2,
        maxconn=10,
        host=db_config["host"],
        port=db_config["port"],
        dbname=db_config["dbname"],
        user=db_config["user"],
        password=db_config["password"],
        options=db_config.get("options", "-c search_path=sge,public"),
    )


def get_conn():
    """Emprunte une connexion depuis le pool."""
    if _pool is None:
        raise RuntimeError(
            "Pool de connexions non initialisé. Appelez init_pool() d'abord."
        )
    return _pool.getconn()


def release_conn(conn):
    """Rend une connexion au pool."""
    if _pool is not None and conn is not None:
        _pool.putconn(conn)


def close_pool():
    """Ferme toutes les connexions du pool."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
