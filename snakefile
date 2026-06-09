from snakemake.utils import min_version

min_version("6.0")

configfile: "config.yaml"

KRAKEN_DB = "database/k2_viral_20260226"

module weather_workflow:
	snakefile: "smk/weather.smk"

use rule * from weather_workflow as weather_*

include: "smk/reads.smk"

rule all:
	input:
		"cities/report.txt"

rule kraken_classification:
	input:
		db=KRAKEN_DB,
		read1="cities/{city}/reads/{sample}_1.fastq.gz",
		read2="cities/{city}/reads/{sample}_2.fastq.gz"
	output:
		temp("cities/{city}/smk_output/kraken/{sample}.output"),
		temp("cities/{city}/smk_output/kraken/{sample}.report")
	threads: 8
	shell:
		"""
		kraken2 \
			--db {input.db} \
			--threads {threads} \
			--output cities/{wildcards.city}/smk_output/kraken/{wildcards.sample}.output \
			--report cities/{wildcards.city}/smk_output/kraken/{wildcards.sample}.report \
			--paired {input.read1} {input.read2}
		"""

rule bracken_report:
	input:
		db=KRAKEN_DB,
		kreport="cities/{city}/smk_output/kraken/{sample}.report"
	output:
		brck=temp("cities/{city}/smk_output/bracken/{sample}.bracken"),
		brep=temp("cities/{city}/smk_output/bracken/{sample}.breport")
	params:
		level=config["classification_level"]
	threads: 1
	shell:
		"""
		bracken \
			-d {input.db} \
			-i {input.kreport} \
			-r 100 \
			-l {params.level} \
			-t 10 \
			-o {output.brck} \
			-w {output.brep}
		"""

rule to_csv:
	input:
		"cities/{city}/smk_output/bracken/{sample}.breport"
	output:
		"cities/{city}/smk_output/sample_csv/{sample}.csv"
	params:
		level=config["classification_level"]
	threads: 1
	script:
		"smk/scripts/to_csv.py"

rule merge_csv:
	input:
		csv=sample_csvs
	output:
		"cities/{city}/smk_output/{city}_merged_reads.csv"
	threads: 1
	script:
		"smk/scripts/merge_csv.py"

rule global_merge:
	input:
		list=lambda wildcards: expand(
                        			"cities/{city}/smk_output/{city}_merged_reads.csv",
                        			city=read_cities(wildcards)
        )
	output:
		"cities/global_merge.csv"
	threads: 1
	script:
		"smk/scripts/global_merge.py"

rule create_all:
	input:
		"cities/global_merge.csv",
		list=lambda wildcards: expand(
                			"cities/{city}/smk_output/{city}_merged_reads.csv",
                			city=read_cities(wildcards)
        ),
		weather=lambda wildcards: expand(
			"cities/{city}/smk_output/{city}_weather.csv",
			city=read_cities(wildcards)
		)
	output:
		"cities/report.txt"
	threads: 1
	shell:
		"""
		echo "Matrix of all Runs: cities/global_merge.csv" > {output}
		echo "Generated matrices for each city:" >> {output}
		echo {input.list} >> {output}
		echo "Generated weather data for each city:" >> {output}
		echo {input.weather} >> {output}
		"""
