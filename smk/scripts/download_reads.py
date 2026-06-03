import argparse
import csv
from pathlib import Path
import subprocess


def read_config_read_type(config_path):
    if not config_path.exists():
        return "non-capture"

    with config_path.open() as handle:
        for line in handle:
            key, separator, value = line.partition(":")
            if separator and key.strip() == "read_type":
                return value.strip().strip("\"'")

    return "non-capture"


def sample_file_for_read_type(read_type):
    if read_type == "capture":
        return Path("filtered_capture_samples.tsv")
    if read_type == "non-capture":
        return Path("filtered_non_capture_samples.tsv")

    raise ValueError("read_type must be either 'capture' or 'non-capture'")


def normalize_url(url):
    if url.startswith(("ftp://", "http://", "https://")):
        return url
    return f"ftp://{url}"


def download_if_missing(output_path, url):
    if output_path.exists():
        print(f"{output_path} already exists, skipping")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["wget", "-c", "-O", str(output_path), url], check=True)


def download_samples(samples_file):
    with samples_file.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if not row.get("city") or not row.get("run_accession"):
                continue

            urls = row["fastq_ftp"].split(";")
            if len(urls) != 2:
                raise ValueError(f"Expected paired fastq_ftp URLs for {row['run_accession']}")

            city = row["city"].replace(" ", "")
            run = row["run_accession"]
            read_dir = Path("cities") / city / "reads"

            download_if_missing(read_dir / f"{run}_1.fastq.gz", normalize_url(urls[0]))
            download_if_missing(read_dir / f"{run}_2.fastq.gz", normalize_url(urls[1]))


def main():
    parser = argparse.ArgumentParser(description="Download selected ENA FASTQ read pairs locally.")
    parser.add_argument(
        "--read-type",
        choices=["capture", "non-capture"],
        default=None,
        help="Override read_type from config.yaml.",
    )
    args = parser.parse_args()

    read_type = args.read_type or read_config_read_type(Path("config.yaml"))
    samples_file = sample_file_for_read_type(read_type)
    if not samples_file.exists():
        raise FileNotFoundError(
            f"{samples_file} does not exist. Run the Snakemake city_logic step first "
            "or keep the filtered sample TSV files in the project root."
        )

    download_samples(samples_file)


if __name__ == "__main__":
    main()
