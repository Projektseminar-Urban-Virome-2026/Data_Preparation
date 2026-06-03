# Projektseminar_Urban_Virome

## Generated test CSV-files

__CSV files with classification matrix and weather data for all 8 cities are available in `generated_files/`__

## Docker 

### Build via Docker-Compose

Compose reads docker-compose.yaml, builds & starts the container and binds `database/` (read only) & `cities/` (read/write) to the container.    
The generated files are written to `cities/{city}/smk_output/`

```bash
docker compose up
```
---

### Alternative Build

### 1. Build the Docker Image

```bash
docker build -t data-preparation .
```

### 2. Start the Container with mounted directories

```bash
docker run -it --mount type=bind,src=./database,dst=/snakemake/database,ro --mount type=bind,src=./cities,dst=/snakemake/cities --name data data-preparation:latest
```

---

### 3. Optional: Remove the Container

```bash
docker rm data
```

## Manual Installation:

### 1. Conda Package Manager

for install using Miniconda see: (https://www.anaconda.com/docs/getting-started/main)

### 2. Snakemake, Kraken2, Bracken

```bash
conda install -c conda-forge -c bioconda snakemake
````

```bash
conda activate snakemake
```

```bash
conda install -c conda-forge -c bioconda kraken2 bracken pandas requests
```


## Required folder structure:

> .../\{project path\}/    
>    |── cities/        
>    |──── Yaounde/     
>    |──────── reads/    
>    |── database/    
>    |── smk/
>    |──── scripts/

**.../\{project path\}/database** contains the (pre-built) Kraken 2 & Bracken databases.   
**.../\{project path\}/cities/.../reads** contains the paired readings of the samples (..._1.fastq.gz & ..._2.fastq.gz)   
**.../\{project path\}/smk/scripts** contains the workflow helper scripts.


## Data preparation
### k-mer Database
Pre-built Kraken2 and Bracken databases can be found [here.](https://benlangmead.github.io/aws-indexes/k2)   
The Database has to be unzipped and stored in an extra directory inside database/   
Example: .../project path/database/k2_viral_20260226

### Input
Sample readings from the Global Urban Virome study are available at the [European Nucleotide Archive.](https://www.ebi.ac.uk/ena/browser/view/PRJEB87273)    
Both paired reads of a sample (..._1.fastq.gz & ..._2.fastq.gz) must be stored inside reads/

## config.yaml

set Classification Level:

`classification_level: G`

Select read type for automatic ENA downloads:

`read_type: non-capture`

Allowed values are `non-capture` and `capture`. The default is `non-capture`.

## Run

The snakemake file has to be run out of {project path}

To generate the assembled matrix for the reads of Ecuador run:

```bash
snakemake --cores 8 cities/Quito/smk_output/Quito_merged_reads.csv
```

Test run:

```bash
snakemake -n cities/Quito/smk_output/Quito_merged_reads.csv
```

To run the pipeline for all cities run:    

```bash
snakemake --cores 8 report.txt
```

The pipeline runs `smk/scripts/city_logic.py`, reads `filtered_capture_samples.tsv` or
`filtered_non_capture_samples.tsv` depending on `config.yaml`, and downloads the
matching paired reads from ENA into `cities/{city}/reads/`.

## Example CSVs

<img width="1950" height="1170" alt="Bildschirmfoto 2026-04-29 um 14 43 08" src="https://github.com/user-attachments/assets/e4255e73-36d7-4fd1-b4d6-15b49b80fa7a" />

<img width="857" height="578" alt="grafik" src="https://github.com/user-attachments/assets/50135a60-3441-4058-9541-5593a15c9fe7" />
