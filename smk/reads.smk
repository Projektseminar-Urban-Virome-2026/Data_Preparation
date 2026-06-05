import csv

READ_TYPE = config.get("read_type", "non-capture")
if READ_TYPE not in ["capture", "non-capture"]:
	raise ValueError("config.yaml read_type must be either 'capture' or 'non-capture'")

def selected_samples():
	output = checkpoints.city_logic.get().output
	return str(output.capture if READ_TYPE == "capture" else output.non_capture)

def samples_by_city(samples_file):
	result = {}
	with open(samples_file, newline="") as handle:
		for row in csv.DictReader(handle, delimiter="\t"):
			if not row.get("city"):
				continue
			city = row["city"].replace(" ", "")
			result.setdefault(city, []).append(row["run_accession"])
	return result

def read_cities(wildcards):
	return sorted(samples_by_city(selected_samples()))

def sample_csvs(wildcards):
	samples = samples_by_city(selected_samples())
	return expand(
		"cities/{city}/smk_output/sample_csv/{sample}.csv",
		city=wildcards.city,
		sample=sorted(samples[wildcards.city]),
	)

def read_fastqs(wildcards):
	samples = samples_by_city(selected_samples())
	return [
		read
		for city, city_samples in samples.items()
		for sample in sorted(city_samples)
		for read in [
			f"cities/{city}/reads/{sample}_1.fastq.gz",
			f"cities/{city}/reads/{sample}_2.fastq.gz",
		]
	]

checkpoint city_logic:
	input:
		script="smk/scripts/city_logic.py"
	output:
		raw="cities/PRJEB87273_runs_samples.tsv",
		capture="cities/filtered_capture_samples.tsv",
		non_capture="cities/filtered_non_capture_samples.tsv"
	threads: 1
	shell:
		"python {input.script}"

rule download_read_pair:
	priority: 10
	input:
		samples=lambda wildcards: selected_samples()
	output:
		read1="cities/{city}/reads/{sample}_1.fastq.gz",
		read2="cities/{city}/reads/{sample}_2.fastq.gz"
	threads: 1
	script:
		"scripts/download_read_pair.py"

rule download_reads:
	input:
		read_fastqs
