# Datensatz-Quelle: https://www.genome.jp/ftp/db/virushostdb/

import csv
from pathlib import Path
import pandas as pd
import requests


SOURCE_URL = "https://www.genome.jp/ftp/db/virushostdb/virushostdb.tsv"
DOWNLOAD_CHUNK_SIZE = 1024 * 1024
CSV_SEPARATOR = ","

script_dir = Path(__file__).resolve().parent
tsv_file = script_dir / "virushostdb.tsv"
csv_file = script_dir / "virushostdb.csv"


def download_tsv(url, destination):
    temporary_destination = destination.with_suffix(".tsv.part")
    print(f"Lade TSV von: {url}")

    try:
        with requests.get(
            url,
            stream=True,
            timeout=(10, 120)
        ) as response:
            response.raise_for_status()

            with open(temporary_destination, "wb") as output:
                downloaded_bytes = 0
                next_report_at = DOWNLOAD_CHUNK_SIZE
                for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    if not chunk:
                        continue
                    output.write(chunk)
                    downloaded_bytes += len(chunk)
                    if downloaded_bytes >= next_report_at:
                        print(f"{downloaded_bytes:,} Bytes heruntergeladen.")
                        next_report_at += DOWNLOAD_CHUNK_SIZE
                print(f"Insgesamt {downloaded_bytes:,} Bytes heruntergeladen.")
    except Exception:
        temporary_destination.unlink(missing_ok=True)
        raise

    if temporary_destination.stat().st_size == 0:
        temporary_destination.unlink(missing_ok=True)
        raise ValueError("Download fehlgeschlagen: Die TSV-Datei ist leer.")

    temporary_destination.replace(destination)
    print(f"TSV gespeichert: {destination}")


def convert_tsv_to_csv(source, destination):
    df = pd.read_csv(source, sep="\t")
    # Taxonomie-Linien enthalten Semikolons; sie bleiben innerhalb eines
    # quotierten Feldes und werden nicht als CSV-Spaltentrenner verwendet.
    df.to_csv(destination, sep=CSV_SEPARATOR, index=False, quoting=csv.QUOTE_ALL)
    print(f"CSV gespeichert: {destination}")


download_tsv(SOURCE_URL, tsv_file)
convert_tsv_to_csv(tsv_file, csv_file)
