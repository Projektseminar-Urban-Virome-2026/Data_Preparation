FROM anaconda/miniconda:latest

# Set working directory
WORKDIR /snakemake

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget

ENV CONDA_PLUGINS_AUTO_ACCEPT_TOS=true

RUN conda install -c conda-forge -c bioconda \
    snakemake \
    kraken2 \
    bracken \
    pandas \
    requests

COPY config.yaml .

COPY snakefile .

COPY /smk smk/

CMD snakemake --cores 10 cities/report.txt
