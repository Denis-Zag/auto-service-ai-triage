import argparse
import os
import sqlite3
from pathlib import Path


def get_required_environment(name: str) -> str:
    """Возвращает обязательную переменную окружения или завершает проверку."""

    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Не задана переменная окружения {name}")
    return value


def verify_backup(database_path: Path) -> int:
    """Проверяет целостность копии и возвращает число сохранённых обращений."""

    with sqlite3.connect(database_path) as connection:
        check_result = connection.execute("PRAGMA quick_check").fetchone()
        if check_result != ("ok",):
            raise RuntimeError(f"Проверка SQLite не пройдена: {check_result}")

        table_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'tickets'"
        ).fetchone()
        if table_exists is None:
            raise RuntimeError("В резервной копии отсутствует таблица tickets")

        row_count = connection.execute("SELECT COUNT(*) FROM tickets").fetchone()
        return int(row_count[0])


def create_backup(database_path: Path) -> int:
    """Синхронизирует Turso в локальный SQLite-файл и проверяет копию."""

    import libsql

    database_url = get_required_environment("TURSO_DATABASE_URL")
    auth_token = get_required_environment("TURSO_AUTH_TOKEN")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_path.unlink(missing_ok=True)

    connection = libsql.connect(
        database=str(database_path),
        sync_url=database_url,
        auth_token=auth_token,
    )
    try:
        connection.sync()
    finally:
        connection.close()

    return verify_backup(database_path)


def main() -> None:
    """Создаёт проверенную резервную копию по аргументам командной строки."""

    parser = argparse.ArgumentParser(description="Резервная копия Turso в SQLite")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    row_count = create_backup(arguments.output)
    print(
        f"Резервная копия создана: {arguments.output}; "
        f"таблица tickets содержит записей: {row_count}"
    )


if __name__ == "__main__":
    main()
