from __future__ import annotations

import argparse
from getpass import getpass
import sqlite3
import sys

from .config import load_settings
from .db import get_connection, init_db
from .main import now_utc, utc_iso
from .security import hash_password


def _password_from_args(args: argparse.Namespace) -> str:
    password = getattr(args, "password", None)
    if password:
        return password
    if getattr(args, "prompt_password", False):
        entered = getpass("Password: ")
        confirmed = getpass("Confirm password: ")
        if entered != confirmed:
            raise SystemExit("Passwords did not match.")
        return entered
    raise SystemExit("Pass --password or --prompt-password.")


def _create_user(
    connection: sqlite3.Connection,
    *,
    username: str,
    password: str,
    display_name: str,
    is_admin: bool,
) -> None:
    connection.execute(
        """
        INSERT INTO users (username, display_name, password_hash, is_admin, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            username.strip(),
            display_name.strip(),
            hash_password(password),
            int(is_admin),
            utc_iso(now_utc()),
        ),
    )
    connection.commit()


def command_init_db(_: argparse.Namespace) -> None:
    settings = load_settings()
    init_db(settings)
    print(f"Initialized database at {settings.database_path}")


def command_bootstrap_admin(args: argparse.Namespace) -> None:
    settings = load_settings()
    init_db(settings)
    with get_connection(settings) as connection:
        existing_admin = connection.execute(
            "SELECT 1 FROM users WHERE is_admin = 1 LIMIT 1"
        ).fetchone()
        if existing_admin is not None:
            raise SystemExit("An admin account already exists.")

        _create_user(
            connection,
            username=args.username,
            password=_password_from_args(args),
            display_name=args.display_name or args.username,
            is_admin=True,
        )
    print(f"Created admin user '{args.username}'.")


def command_create_user(args: argparse.Namespace) -> None:
    settings = load_settings()
    init_db(settings)
    with get_connection(settings) as connection:
        _create_user(
            connection,
            username=args.username,
            password=_password_from_args(args),
            display_name=args.display_name or args.username,
            is_admin=args.admin,
        )
    role = "admin" if args.admin else "user"
    print(f"Created {role} '{args.username}'.")


def command_reset_password(args: argparse.Namespace) -> None:
    settings = load_settings()
    init_db(settings)
    with get_connection(settings) as connection:
        row = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (args.username,),
        ).fetchone()
        if row is None:
            raise SystemExit(f"No user found with username '{args.username}'.")

        connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE username = ?
            """,
            (hash_password(_password_from_args(args)), args.username),
        )
        connection.execute("DELETE FROM sessions WHERE user_id = ?", (row["id"],))
        connection.commit()
    print(f"Updated password for '{args.username}'.")


def command_db_summary(_: argparse.Namespace) -> None:
    settings = load_settings()
    init_db(settings)
    with get_connection(settings) as connection:
        users = connection.execute(
            """
            SELECT
              users.username,
              users.display_name,
              users.is_admin,
              COUNT(messages.id) AS message_count
            FROM users
            LEFT JOIN messages ON messages.user_id = users.id
            GROUP BY users.id
            ORDER BY users.created_at ASC
            """
        ).fetchall()
        user_count = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        message_count = connection.execute("SELECT COUNT(*) AS count FROM messages").fetchone()[
            "count"
        ]
        session_count = connection.execute("SELECT COUNT(*) AS count FROM sessions").fetchone()[
            "count"
        ]

    print(f"Database path: {settings.database_path}")
    print(f"Users: {user_count}")
    print(f"Messages: {message_count}")
    print(f"Active sessions: {session_count}")
    print("")
    print("Accounts:")
    for row in users:
        role = "admin" if row["is_admin"] else "user"
        print(
            f"  - {row['username']} ({row['display_name']}) [{role}] "
            f"messages={row['message_count']}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Team Yap operational commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db_parser = subparsers.add_parser("init-db", help="Create the SQLite schema if needed")
    init_db_parser.set_defaults(func=command_init_db)

    bootstrap_parser = subparsers.add_parser(
        "bootstrap-admin", help="Create the first admin account"
    )
    bootstrap_parser.add_argument("--username", required=True)
    bootstrap_parser.add_argument("--display-name")
    bootstrap_parser.add_argument("--password")
    bootstrap_parser.add_argument("--prompt-password", action="store_true")
    bootstrap_parser.set_defaults(func=command_bootstrap_admin)

    create_user_parser = subparsers.add_parser("create-user", help="Create a user account")
    create_user_parser.add_argument("--username", required=True)
    create_user_parser.add_argument("--display-name")
    create_user_parser.add_argument("--password")
    create_user_parser.add_argument("--prompt-password", action="store_true")
    create_user_parser.add_argument("--admin", action="store_true")
    create_user_parser.set_defaults(func=command_create_user)

    reset_password_parser = subparsers.add_parser(
        "reset-password", help="Overwrite an existing user's password"
    )
    reset_password_parser.add_argument("--username", required=True)
    reset_password_parser.add_argument("--password")
    reset_password_parser.add_argument("--prompt-password", action="store_true")
    reset_password_parser.set_defaults(func=command_reset_password)

    db_summary_parser = subparsers.add_parser(
        "db-summary", help="Print a read-only summary of the current database"
    )
    db_summary_parser.set_defaults(func=command_db_summary)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except sqlite3.IntegrityError as error:
        print(f"Database error: {error}", file=sys.stderr)
        return 1
    except SystemExit as error:
        message = str(error)
        if message:
            print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
