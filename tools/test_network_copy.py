import argparse
import csv
import os
import sys
import tempfile
import shutil
import time
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from services.router import move_file  # noqa: E402


def _create_dummy_file(size_mb: int) -> str:
    """Create a temporary test file with the desired size."""
    size_mb = max(1, size_mb)
    tmp = tempfile.NamedTemporaryFile(prefix="werkstatt_network_test_", suffix=".bin", delete=False)
    chunk = b"\0" * (1024 * 1024)
    for _ in range(size_mb):
        tmp.write(chunk)
    tmp.flush()
    tmp.close()
    return tmp.name


def _copy_source(source_path: str) -> str:
    tmp = tempfile.NamedTemporaryFile(prefix="werkstatt_network_source_", suffix=os.path.splitext(source_path)[1] or ".bin", delete=False)
    tmp.close()
    shutil.copy2(source_path, tmp.name)
    return tmp.name


def _format_size(num_bytes: int) -> str:
    mb = num_bytes / (1024 * 1024)
    return f"{mb:.2f} MB"


def _append_log(log_file: str, row: dict) -> None:
    """Append a row to the CSV log, creating header on first write."""
    log_dir = os.path.dirname(os.path.abspath(log_file))
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    file_exists = os.path.exists(log_file)
    fieldnames = [
        "timestamp",
        "target_dir",
        "target_file",
        "size_bytes",
        "duration_seconds",
        "throughput_mb_s",
        "source_mode",
        "cleanup",
    ]
    with open(log_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def run_test(target_dir: str, size_mb: int, source: str | None, cleanup: bool, log_file: str | None) -> None:
    os.makedirs(target_dir, exist_ok=True)

    if source:
        if not os.path.exists(source):
            raise FileNotFoundError(f"Quelle nicht gefunden: {source}")
        temp_source = _copy_source(source)
        source_mode = "custom"
    else:
        temp_source = _create_dummy_file(size_mb)
        source_mode = "dummy"

    target_filename = f"network_move_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}{os.path.splitext(temp_source)[1]}"
    target_path = os.path.join(target_dir, target_filename)

    try:
        start = time.perf_counter()
        final_path = move_file(temp_source, target_path)
        duration = time.perf_counter() - start

        size_bytes = os.path.getsize(final_path)
        throughput = (size_bytes / (1024 * 1024)) / duration if duration > 0 else 0

        print("=== Netzwerk-Kopiertest ===")
        print(f"Zielordner: {target_dir}")
        print(f"Zieldatei: {final_path}")
        print(f"Dateigroesse: {_format_size(size_bytes)}")
        print(f"Dauer: {duration:.2f} s")
        print(f"Durchsatz: {throughput:.2f} MB/s")

        if log_file:
            _append_log(
                log_file,
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "target_dir": os.path.abspath(target_dir),
                    "target_file": os.path.abspath(final_path),
                    "size_bytes": size_bytes,
                    "duration_seconds": round(duration, 4),
                    "throughput_mb_s": round(throughput, 2),
                    "source_mode": source_mode,
                    "cleanup": bool(cleanup),
                },
            )
            print(f"Log erweitert: {os.path.abspath(log_file)}")

        if cleanup:
            os.remove(final_path)
            print("Hinweis: Testdatei im Ziel wurde wieder geloescht.")
    finally:
        if os.path.exists(temp_source):
            try:
                os.remove(temp_source)
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Testet den Netzwerk-optimierten Datei-Transfer.")
    parser.add_argument("--target", required=True, help="Zielordner (z. B. Netzlaufwerk)")
    parser.add_argument("--size-mb", type=int, default=5, help="Groesse der Dummy-Datei in MB")
    parser.add_argument("--source", help="Optionaler Pfad zu einer vorhandenen Testdatei (Original bleibt erhalten)")
    parser.add_argument("--cleanup", action="store_true", help="Testdatei nach dem Lauf im Zielordner loeschen")
    parser.add_argument("--log-file", help="Optionaler Pfad zu einer CSV-Datei fuer Messwerte")
    args = parser.parse_args()

    try:
        run_test(args.target, args.size_mb, args.source, args.cleanup, args.log_file)
        return 0
    except Exception as exc:
        print(f"Fehler: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
