CREATE TABLE IF NOT EXISTS Cities (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(255) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_accession VARCHAR(255) PRIMARY KEY,
    run_alias VARCHAR(255),
    collection_date DATE NOT NULL,
    city_id INTEGER NOT NULL,
    SampleID VARCHAR(255),
    FOREIGN KEY (city_id) REFERENCES Cities(id)
);

CREATE TABLE IF NOT EXISTS Weather (
    run_accession VARCHAR(255) PRIMARY KEY,
    temperature FLOAT,
    humidity FLOAT,
    rainfall FLOAT,
    wind_speed FLOAT,
    FOREIGN KEY (run_accession) REFERENCES runs(run_accession)
);


CREATE TABLE IF NOT EXISTS Virus (
    tax_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    realm VARCHAR(255),
    kingdom VARCHAR(255),
    phylum VARCHAR(255),
    class VARCHAR(255),
    taxonomic_order VARCHAR(255),
    family VARCHAR(255),
    genus VARCHAR(255),
    species VARCHAR(255),
    baltimore_class VARCHAR(255) 
);

CREATE TABLE IF NOT EXISTS Virus_Hosts (
    virus_tax_id INTEGER NOT NULL,
    host_tax_id INTEGER NOT NULL,
    PRIMARY KEY (virus_tax_id, host_tax_id),
    FOREIGN KEY (virus_tax_id) REFERENCES Virus(tax_id),
    FOREIGN KEY (host_tax_id) REFERENCES Host(Host_tax_id)
);

CREATE TABLE IF NOT EXISTS Host (
    Host_tax_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Virus_in_Runs (
    run_accession VARCHAR(255) NOT NULL,
    virus_tax_id INTEGER NOT NULL,
    amount_in_sample_as_percentage FLOAT,
    PRIMARY KEY (run_accession, virus_tax_id),
    FOREIGN KEY (run_accession) REFERENCES runs(run_accession),
    FOREIGN KEY (virus_tax_id) REFERENCES Virus(tax_id)
);
