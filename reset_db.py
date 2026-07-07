"""reset_db.py -- Reinitialisation complete de la base PostgreSQL.

Ce script :

1. Supprime le schema sge (CASCADE) pour tout nettoyer.
2. Re-cree le schema et charge les fichiers *.sql* dans l'ordre.
3. Resynchronise les sequences afin que les INSERT explicites ne
   desynchronisent plus la generation d'ID.

Usage :
    .venv\\Scripts\\python.exe reset_db.py
"""

from pathlib import Path
import psycopg2
from config import DATABASE

# ---------------------------------------------------------------------------
# Repertoire contenant les scripts SQL
# ---------------------------------------------------------------------------
SQL_DIR = Path(__file__).resolve().parent / "base de donnee"

SQL_FILES = [
    "SGE_cre.sql",
    "SGE_inv.sql",
    "SGE_imm.sql",
    "SGE_req.sql",
    "SGE_tra.sql",
    "SGE_jdd_01.sql",
]


# ---------------------------------------------------------------------------
# Connexion PostgreSQL
# ---------------------------------------------------------------------------
def connect():
    """Ouvre une connexion a la base de donnees PostgreSQL."""
    return psycopg2.connect(
        host=DATABASE["host"],
        port=DATABASE["port"],
        dbname=DATABASE["dbname"],
        user=DATABASE["user"],
        password=DATABASE["password"],
        options="-c search_path=public",
    )


# ---------------------------------------------------------------------------
# Fonctions utilitaires
# ---------------------------------------------------------------------------
def exec_sql(conn, sql_text: str):
    """Execute un bloc SQL sur la connexion fournie."""
    with conn.cursor() as cur:
        cur.execute(sql_text)


def load_sql_file(conn, path: Path):
    """Lit un fichier *.sql* et l'execute."""
    print(f"  \u25b6 Chargement : {path.name}")
    sql_text = path.read_text(encoding="utf-8")
    exec_sql(conn, sql_text)


# ---------------------------------------------------------------------------
# Reinitialisation du schema
# ---------------------------------------------------------------------------
def drop_schema(conn):
    """Supprime le schema sge s'il existe, puis le recree."""
    print("\n\U0001f5d1\ufe0f  Suppression du schema sge ...")
    exec_sql(conn, "DROP SCHEMA IF EXISTS sge CASCADE;")
    exec_sql(conn, "CREATE SCHEMA sge;")
    exec_sql(conn, "SET search_path TO sge, public;")
    print("  Schema sge recree (vide).\n")


# ---------------------------------------------------------------------------
# Chargement des fichiers SQL
# ---------------------------------------------------------------------------
def populate_schema(conn):
    """Charge les scripts SQL dans l'ordre defini."""
    print("\U0001f4e5  Chargement des fichiers SQL :")
    for filename in SQL_FILES:
        sql_path = SQL_DIR / filename
        if not sql_path.is_file():
            raise FileNotFoundError(f"Fichier SQL introuvable : {sql_path}")
        load_sql_file(conn, sql_path)
    print()


# ---------------------------------------------------------------------------
# Resynchronisation des sequences
# ---------------------------------------------------------------------------
def sync_sequences(conn):
    """Remet a jour les sequences apres les INSERT avec IDs explicites."""
    print("\U0001f504  Resynchronisation des sequences ...")
    seq_query = """
        SELECT 'SELECT setval(' || quote_literal(
                   pg_get_serial_sequence(
                       t.table_schema || '.' || t.table_name, c.column_name
                   )
               ) || ', COALESCE((SELECT MAX(' || quote_ident(c.column_name)
               || ') FROM ' || quote_ident(t.table_schema) || '.'
               || quote_ident(t.table_name) || '), 1))' AS cmd
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON t.table_name  = c.table_name
         AND t.table_schema = c.table_schema
        WHERE t.table_schema = 'sge'
          AND c.column_default LIKE 'nextval%';
    """
    with conn.cursor() as cur:
        cur.execute(seq_query)
        for row in cur.fetchall():
            try:
                cur.execute(row[0])
            except Exception:
                pass
    print("  Sequences synchronisees.\n")


# ---------------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------------
def main():
    """Execute la reinitialisation complete."""
    if not SQL_DIR.is_dir():
        raise FileNotFoundError(f"Repertoire SQL introuvable : {SQL_DIR}")

    print("=" * 50)
    print("  REINITIALISATION DE LA BASE DE DONNEES")
    print("  WMS-CLAM-PRO  |  SAC LOGISTICS")
    print("=" * 50)

    with connect() as conn:
        conn.autocommit = True
        drop_schema(conn)
        populate_schema(conn)
        sync_sequences(conn)

    print("\u2705  Reinitialisation terminee avec succes.")
    print("   Vous pouvez maintenant relancer l'application.\n")


if __name__ == "__main__":
    main()
