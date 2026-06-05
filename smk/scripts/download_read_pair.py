import csv
from pathlib import Path
import os
import subprocess

def read_urls(samples_file, city, run):
    with open(samples_file, newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            row_city = row["city"].replace(" ", "")
            if row_city != city or row["run_accession"] != run:
                continue

            urls = row["fastq_ftp"].split(";")
            if len(urls) != 2:
                raise ValueError(f"Expected paired fastq_ftp URLs for {run}")

            return [
                url if url.startswith(("ftp://", "http://", "https://")) else f"ftp://{url}"
                for url in urls
            ]

    raise ValueError(f"Could not find {city}/{run} in {samples_file}")

read1_url, read2_url = read_urls(
    snakemake.input.samples,
    snakemake.wildcards.city,
    snakemake.wildcards.sample,
)

Path(snakemake.output.read1).parent.mkdir(parents=True, exist_ok=True)

def download_if_missing(output, url):
    output = Path(output)
    if os.path.exists(str(output)):
        print(f"{output} already exists, skipping download")
        return

    subprocess.run(["wget", "-c", "-O", str(output), url], check=True)

download_if_missing(snakemake.output.read1, read1_url)
download_if_missing(snakemake.output.read2, read2_url)
