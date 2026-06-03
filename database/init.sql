CREATE TABLE Cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(255) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL
);

CREATE TABLE runs (
    run_accession VARCHAR(255) PRIMARY KEY,
    run_alias VARCHAR(255),
    collection_date DATE NOT NULL,
    city_id INTEGER NOT NULL,
    SampleID VARCHAR(255),
    FOREIGN KEY (city_id) REFERENCES Cities(id)
);

CREATE TABLE Weather (
    run_accession VARCHAR(255) PRIMARY KEY,
    temperature FLOAT,
    humidity FLOAT,
    wind_speed FLOAT,
    FOREIGN KEY (run_accession) REFERENCES runs(run_accession)
);

CREATE TABLE Virus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    family VARCHAR(255) NOT NULL,
    species VARCHAR(255) NOT NULL,
    Boltimore_type VARCHAR(255) NOT NULL 
);

CREATE TABLE Virus_Hosts (
    virus_id INTEGER NOT NULL,
    host_tax_id INTEGER NOT NULL,
    PRIMARY KEY (virus_id, host_tax_id),
    FOREIGN KEY (virus_id) REFERENCES Virus(id),
    FOREIGN KEY (host_tax_id) REFERENCES Host(Host_tax_id)
);

CREATE TABLE Host (
    Host_tax_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE Virus_in_Runs (
    run_accession VARCHAR(255) NOT NULL,
    virus_id INTEGER NOT NULL,
    amount_in_sample_as_percent FLOAT,
    PRIMARY KEY (run_accession, virus_id),
    FOREIGN KEY (run_accession) REFERENCES runs(run_accession),
    FOREIGN KEY (virus_id) REFERENCES Virus(id)
);
