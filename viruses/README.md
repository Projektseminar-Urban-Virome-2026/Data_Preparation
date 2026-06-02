# Laden der Virus-Informationen

In diesem Ordner werden Virus-Informationen aus zwei Datenquellen geladen und
als TSV- sowie CSV-Dateien für die weitere Analyse gespeichert:

- `ECDC/`: Virus-Host-Datenbank von GenomeNet/KEGG
- `NCBI/`: Virus-Metadaten aus der NCBI Datasets API

## Voraussetzungen

Die Skripte benötigen Python sowie die folgenden Pakete:

```bash
python3 -m venv .venv
source .venv/bin/activate
python conda install -c pandas requests
```

Die Befehle in dieser Dokumentation werden aus dem Projektordner `Analysis`
ausgeführt.

## ECDC / Virus-Host-Datenbank

### Datenquelle

Das Skript
[getVirusInformationFromECDC.py](ECDC/getVirusInformationFromECDC.py) lädt die
Virus-Host-Datenbank von:

<https://www.genome.jp/ftp/db/virushostdb/virushostdb.tsv>

Die Tabelle enthält unter anderem Informationen zu Viren, Wirten,
Taxonomie-Linien, RefSeq-IDs und Evidenzquellen.

### Ausführung

```bash
python virus_information/ECDC/getVirusInformationFromECDC.py
```

### Ausgaben

Die heruntergeladene TSV-Datei und die daraus erzeugte CSV-Datei werden im
Ordner `virus_information/ECDC/` gespeichert:

- `virushostdb.tsv`
- `virushostdb.csv`

Die CSV-Datei verwendet ein Komma als Spaltentrenner. Semikolons in den
Taxonomie-Linien sind Bestandteil der Daten und werden nicht zur Trennung von
Spalten verwendet.

Während des Downloads wird zunächst die temporäre Datei
`virushostdb.tsv.part` geschrieben. Erst nach einem erfolgreichen Download
wird sie als `virushostdb.tsv` gespeichert.

## NCBI

### Datenquelle und Filter

Das Skript
[getVirusInformationFromNCBI.py](NCBI/getVirusInformationFromNCBI.py) fragt
die NCBI Datasets API ab:

<https://api.ncbi.nlm.nih.gov/datasets/v2/virus/taxon/10239/genome/table>

Die Anfrage beschränkt sich auf Viren (`taxon/10239`) mit Menschen als Wirt
(`host=9606`). Die abzurufenden Tabellenspalten werden im Skript in
`TABLE_FIELDS` festgelegt.

### Ausführung

```bash
python virus_information/NCBI/getVirusInformationFromNCBI.py
```

### Ausgaben

Die NCBI-Daten werden im Ordner `virus_information/NCBI/` gespeichert:

- `virus_data.tsv`
- `virus_data.csv`

Der Download wird zunächst nach `virus_data.tsv.part` geschrieben. Die
vorhandene TSV-Datei wird nur nach einem vollständigen Download ersetzt;
anschließend wird daraus die CSV-Datei erzeugt.

Bei einem temporären Verbindungsabbruch während eines großen NCBI-Downloads
startet das Skript den Download automatisch erneut. Nach vier
fehlgeschlagenen Versuchen wird die vorhandene TSV-Datei nicht überschrieben.

## Aktualisierung der Daten

Zum Aktualisieren der lokalen Datenbestände werden die jeweiligen Skripte
erneut ausgeführt. Dabei werden die bestehenden Ausgabe-Dateien nach einem
erfolgreichen Download durch den aktuellen Stand der Quelle ersetzt.
