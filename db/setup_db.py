"""Script d'initialisation de la base PostgreSQL à partir des fichiers SQL fournis."""

from pathlib import Path
import psycopg2
from psycopg2 import sql
from config import DATABASE

SQL_FILES = [
    "SGE_cre.sql",
    "SGE_inv.sql",
    "SGE_imm.sql",
    "SGE_req.sql",
    "SGE_tra.sql",
    "SGE_jdd_01.sql",
]


def get_sql_directory() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "base de donnee"


def execute_sql_file(connection, path: Path):
    print(f"Chargement du fichier SQL : {path.name}")
    with path.open("r", encoding="utf-8") as handle:
        sql_text = handle.read()
    with connection.cursor() as cursor:
        cursor.execute(sql_text)
    connection.commit()


def connect():
    return psycopg2.connect(
        host=DATABASE["host"],
        port=DATABASE["port"],
        dbname=DATABASE["dbname"],
        user=DATABASE["user"],
        password=DATABASE["password"],
        options=DATABASE.get("options", "-c search_path=sge,public"),
    )


def main():
    sql_dir = get_sql_directory()
    if not sql_dir.exists():
        raise FileNotFoundError(f"Répertoire SQL introuvable : {sql_dir}")

    with connect() as conn:
        conn.autocommit = True
        for filename in SQL_FILES:
            path = sql_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"Fichier SQL introuvable : {path}")
            execute_sql_file(conn, path)

        # Resynchroniser toutes les séquences après le chargement du jeu de données
        # (les INSERT avec IDs explicites dans SGE_jdd_01.sql désynchronisent les séquences)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 'SELECT setval(' || quote_literal(pg_get_serial_sequence(t.table_schema||'.'||t.table_name, c.column_name))
                       || ', COALESCE((SELECT MAX(' || quote_ident(c.column_name) || ') FROM '
                       || quote_ident(t.table_schema) || '.' || quote_ident(t.table_name) || '), 1))' AS cmd
                FROM information_schema.columns c
                JOIN information_schema.tables t ON t.table_name = c.table_name AND t.table_schema = c.table_schema
                WHERE t.table_schema = 'sge'
                  AND c.column_default LIKE 'nextval%'
            """)
            for row in cur.fetchall():
                try:
                    cur.execute(row[0])
                except Exception:
                    pass

    print("Initialisation de la base PostgreSQL terminée.")


if __name__ == "__main__":
    main()
