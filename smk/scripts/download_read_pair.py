import csv
from pathlib import Path
import os
import subprocess

def download_if_missing(output, url):
    output = Path(output)
    if os.path.exists(str(output)):
        print(f"{output} already exists, skipping download")
        return

    subprocess.run(["wget", "-c", "-O", str(output), url], check=True)

def read_urls(samples_file):
    with open(samples_file, newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            city = row["city"].replace(" ", "")
            sample = row["run_accession"]
            output1 = str(f"cities/{city}/reads/{sample}_1.fastq.gz")
            output2 = str(f"cities/{city}/reads/{sample}_2.fastq.gz")
            urls = row["fastq_ftp"].split(";")
            if len(urls) != 2:
                raise ValueError(f"Expected paired fastq_ftp URLs for {run}")

            read1_url = urls[0] if urls[0].startswith(("ftp://", "http://", "https://")) else f"ftp://{urls[0]}"
            read2_url = urls[1] if urls[1].startswith(("ftp://", "http://", "https://")) else f"ftp://{urls[1]}"

            Path(output1).parent.mkdir(parents=True, exist_ok=True)

            download_if_missing(output1, read1_url)
            download_if_missing(output2, read2_url)

read_urls(snakemake.input.samples)

with open(snakemake.output.report, 'w') as f:
    print('download_read_pair.py executed', file=f)