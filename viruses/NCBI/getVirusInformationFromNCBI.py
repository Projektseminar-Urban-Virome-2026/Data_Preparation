# Datenquelle: https://www.ncbi.nlm.nih.gov/labs/virus/vssi/#/virus?SeqType_s=Genome&VirusLineage_ss=Viruses,%20taxid:10239&HostLineage_ss=humans,%20taxid:9605
# Quelle für die API-Code-Erstellung: https://github.com/misialq/ncbi-datasets-pyclient/blob/main/docs/VirusApi.md#virus_genome_table


# Zunächst per Bash:
# pip install ncbi-datasets-pyclient

import ncbi.datasets.openapi
from ncbi.datasets.openapi.models.v2_viral_sequence_type import V2ViralSequenceType
from ncbi.datasets.openapi.models.v2_virus_dataset_report_type import V2VirusDatasetReportType
from ncbi.datasets.openapi.rest import ApiException
from pprint import pprint
import pandas as pd
import requests
from pathlib import Path
from time import sleep

BASE_URL = "https://api.ncbi.nlm.nih.gov/datasets/v2/virus/taxon/10239/genome/table"
DOWNLOAD_CHUNK_SIZE = 1024 * 1024 # 1 MB; bei großen Antworten wird der Download in 1-MB-Chunks durchgeführt, um die Speichernutzung zu optimieren und die Fortschrittsanzeige zu ermöglichen.
MAX_DOWNLOAD_ATTEMPTS = 4 # Bei Verbindungsabbrüchen wird der Download bis zu 4 Mal mit exponentiellem Backoff neu versucht, bevor eine Fehlermeldung ausgegeben wird.

TABLE_FIELDS = [
    # "nucleotide_accession", # enthält die eindeutige Kennnummer für eine Nukleinsäure-Sequenz in einer biologischen Datenbank, die verwendet wird, um Informationen über die Sequenz zu identifizieren und abzurufen.
    "species_tax_id", # enthält die Taxonomie-ID der Spezies, zu der das Virus gehört. Diese ID kann verwendet werden, um weitere Informationen über die Spezies in biologischen Datenbanken abzurufen.
    "species_name", # enthält den wissenschaftlichen Namen der Spezies, zu der das Virus gehört. Dieser Name wird in der biologischen Nomenklatur verwendet, um die Spezies eindeutig zu identifizieren.
    "genus", # enthält den Gattungsnamen des Virus, der eine taxonomische Kategorie ist, die eine Gruppe von Arten umfasst, die gemeinsame Merkmale aufweisen. Der Gattungsname wird in der biologischen Nomenklatur verwendet, um die Gattung eines Organismus zu identifizieren.
    "family", # enthält den Familiennamen des Virus, der eine taxonomische Kategorie ist, die eine Gruppe von Gattungen umfasst, die gemeinsame Merkmale aufweisen.
    # "nucleotide_length", # enthält die Länge der Nukleinsäure-Sequenz des Virus in Basenpaaren (bp) oder Nukleotiden (nt). Diese Information gibt an, wie viele Basen oder Nukleotide in der Sequenz enthalten sind.
    # "isolate_name", # enthält den Namen der Virusisolate, die in der Datenbank erfasst sind. Ein Isolat ist eine spezifische Probe eines Virus, die aus einer bestimmten Quelle (z.B. einem Patienten, einem Tier oder einer Umweltprobe) stammt und in der Datenbank als eigenständige Einheit erfasst wird.
    "sequence_type", # enthält den Typ der Nukleinsäure-Sequenz des Virus, z.B. "genome" für das gesamte Genom oder "cds" für die codierende Sequenz eines bestimmten Gens.
    # "nuc_completeness", # beschreibt bei Viren-Genomen meist, wie vollständig die rekonstruierte Nukleinsäure-Sequenz (DNA oder RNA) im Vergleich zu einem erwarteten Referenzgenom ist.
    # "geo_location", # enthält Informationen über den geografischen Standort, an dem die Virusprobe gesammelt wurde.
    # "us_state", # enthält den Namen des US-Bundesstaates, aus dem die Virusprobe stammt, falls die Probe aus den USA stammt.
    # "host_name", # enthält den Namen des Landes, aus dem die Virusprobe stammt.
    # "host_tax_id", # enthält die Taxonomie-ID des Landes, von dem die Virusprobe stammt.
    # "collection_date", # enthält das Datum, an dem die Virusprobe gesammelt wurde. Dieses Datum kann in verschiedenen Formaten vorliegen, z.B. als Jahr, Monat und Tag (YYYY-MM-DD) oder als Jahr und Monat (YYYY-MM).
    # "bioproject", # enthält die eindeutige Kennnummer für ein biologisches Projekt in einer biologischen Datenbank, die verwendet wird, um Informationen über das Projekt zu identifizieren und abzurufen.
    # "biosample", # enthält die eindeutige Kennnummer für eine biologische Probe in einer biologischen Datenbank, die verwendet wird, um Informationen über die Probe zu identifizieren und abzurufen.
    # "polyprotein_name", # enthält den Namen des Polyproteins, das die Virusproteine kodiert.
    # "protein_name", # enthält den Namen des Proteins, das von der Virusnukleinsäure kodiert wird.
    # "protein_accession", # eine eindeutige Kennnummer für ein Protein in einer biologischen Datenbank, die verwendet wird, um Informationen über das Protein zu identifizieren und abzurufen.
    # "protein_synonym", # enthält alternative Namen oder Bezeichnungen für das Protein, die in verschiedenen wissenschaftlichen Veröffentlichungen oder Datenbanken Verwendung finden.
    # "cds_span" # enthält den Bereich der codierenden Sequenz (CDS) der Nukleinsäure, der tatsächlich in ein Protein übersetzt wird
]

headers = {
    "Accept": "text/tab-separated-values"
}

data_dir = Path(__file__).resolve().parent  # Speichere Ausgabedateien im NCBI-Ordner.
tsv_path = data_dir / "virus_data.tsv"
csv_path = data_dir / "virus_data.csv"
temporary_tsv_path = tsv_path.with_suffix(".tsv.part")

params = [("host", "9606")]  # 9606 ist die Taxid für Menschen

# Es werden alle gewünschten Felder als Parameter übergeben, damit die API nur die benötigten Daten zurückliefert
for field in TABLE_FIELDS:
    params.append(("table_fields", field))

print(f"Lade TSV zunaechst nach: {temporary_tsv_path}")

def download_tsv():
    # Ein Stream kann bei grossen Antworten vorzeitig abbrechen; dann beginnt
    # der naechste Versuch bewusst mit einer neuen temporaeren Datei.
    for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
        try:
            print(f"Downloadversuch {attempt}/{MAX_DOWNLOAD_ATTEMPTS}")
            with requests.get(
                BASE_URL,
                params=params,
                headers=headers,
                stream=True,
                timeout=(10, 120) # 10 Sekunden für die Verbindung, 120 Sekunden für den Download eines Chunks
            ) as response:
                response.raise_for_status()

                with open(temporary_tsv_path, "wb") as out:
                    downloaded_bytes = 0

                    for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                        if not chunk:
                            continue
                        out.write(chunk)
                        downloaded_bytes += len(chunk)
                        print(f"{downloaded_bytes:,} Bytes heruntergeladen.")
            return
        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as error:
            temporary_tsv_path.unlink(missing_ok=True)
            if attempt == MAX_DOWNLOAD_ATTEMPTS:
                raise RuntimeError(
                    "NCBI-Download nach mehreren Verbindungsabbruechen fehlgeschlagen; "
                    "die TSV wurde nicht ersetzt."
                ) from error

            wait_seconds = 2 ** (attempt - 1)
            print(
                f"Verbindung beim Download abgebrochen. "
                f"Neuer Versuch in {wait_seconds} Sekunden."
            )
            sleep(wait_seconds)
        except Exception as error:
            temporary_tsv_path.unlink(missing_ok=True)
            raise RuntimeError(
                "NCBI-Download fehlgeschlagen; die TSV wurde nicht ersetzt."
            ) from error


download_tsv()

if temporary_tsv_path.stat().st_size == 0:
    temporary_tsv_path.unlink(missing_ok=True)
    raise ValueError("NCBI hat keine Tabellendaten geliefert; keine CSV erstellt.")

# Sobald der Download erfolgreich abgeschlossen ist, wird die temporäre TSV-Datei auf die endgültige TSV-Datei umbenannt, um die Integrität der Daten zu gewährleisten.
temporary_tsv_path.replace(tsv_path)
print("TSV-Datei vollständig gespeichert.")


# TSV -> CSV
def convert_tsv_to_csv(tsv_file, csv_file):
    df = pd.read_csv(tsv_file, sep="\t")
    df.to_csv(csv_file, index=False)
    print(f"CSV gespeichert: {csv_file}")

convert_tsv_to_csv(tsv_path, csv_path)
