"""
DB factory: retourne SGEDatabase (PostgreSQL).
"""

from config import DATABASE


def get_database():
    """Retourne une instance de SGEDatabase connectée à PostgreSQL."""
    from db.connection import init_pool
    from db.sge_database import SGEDatabase

    init_pool(DATABASE)
    return SGEDatabase()
