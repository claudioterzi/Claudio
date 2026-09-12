"""Consistent SQLite backup before deployment. Never prints personal records."""
import argparse
import sqlite3
from pathlib import Path


def backup(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file() or destination.exists() or source == destination:
        raise ValueError("Serve un database esistente e una destinazione nuova.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Create with owner-only permissions before SQLite opens it.
    descriptor = destination.open("xb")
    descriptor.close()
    destination.chmod(0o600)
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as src, sqlite3.connect(destination) as dest:
        src.backup(dest)
        if dest.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Verifica del backup non riuscita.")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup consistente dei registri del bot")
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()
    backup(args.source, args.destination)
    print("Backup creato e integrità verificata.")
