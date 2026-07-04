import pandas as pd
import sqlite3

def runs_table(df, db_connection):
    """
    Liest TSV ein und fügt run_accession, sample_alias, collection_date in runs-Tabelle ein.
    """
    
    # Nur relevante Spalten auswählen
    runs_df = df[['run_accession', 'sample_alias', 'collection_date', 'city']].copy()
    
    city_to_id = db_connection.execute("SELECT id, name FROM Cities").fetchall()
    city_to_id_dict = {name: id for id, name in city_to_id}
    
    cursor = db_connection.cursor()
    for _, row in runs_df.iterrows():
        cursor.execute("""
            INSERT INTO runs (run_accession, run_alias, collection_date, city_id)
            VALUES (?, ?, ?, ?)
        """, (row['run_accession'], row['sample_alias'], row['collection_date'], city_to_id_dict.get(row['city'], None)))  # city_id placeholder
    
    db_connection.commit()
    print(f"✓ {len(runs_df)} Einträge in runs_table eingefügt")


def city_table(df, db_connection):
    """
    Liest Cities aus TSV ein, entfernt Duplikate und fügt lat/lon hinzu.
    """

    # Unique cities extrahieren
    cities_df = df[['city', 'country']].drop_duplicates().copy()
    cities_df.columns = ['name', 'country']
    
    # Koordinaten-Mapping
    city_coords = {
        # Quelle für Koordinaten: https://maps.apple.com
        'Melbourne': {'lat': -37.81503, 'lon': 144.96634},
        'Guangzhou': {'lat': 23.13422, 'lon': 113.26098},
        'Kuala Lumpur': {'lat': 3.16000, 'lon': 101.71000},
        'Regina': {'lat': 50.44886, 'lon': -104.61091},
        'Copenhagen': {'lat': 55.66235, 'lon': 12.61593},
        'Quito': {'lat': -0.22011, 'lon': -78.51150},
        'Seattle': {'lat': 47.60387, 'lon': -122.33077},
        'Yaounde': {'lat': 3.85495, 'lon': 11.50270},
    }
    
    # Lat/Lon hinzufügen
    cities_df['latitude'] = cities_df['name'].apply(
        lambda x: city_coords.get(x, {}).get('lat', 0.0)
    )
    cities_df['longitude'] = cities_df['name'].apply(
        lambda x: city_coords.get(x, {}).get('lon', 0.0)
    )
    if cities_df['latitude'].eq(0.0).any() or cities_df['longitude'].eq(0.0).any():
        print("Warnung: Folgende Staedte haben keine Koordinaten." + str(cities_df[cities_df['latitude'].eq(0.0) | cities_df['longitude'].eq(0.0)]) + " und werden mit 0.0 eingefügt.")
       
    
    # In DB einfügen
    cursor = db_connection.cursor()
    id_counter = 1
    for _, row in cities_df.iterrows():
        cursor.execute("""
                       INSERT INTO Cities (id, name, country, latitude, longitude)
            VALUES (?, ?, ?, ?, ?)
        """, (id_counter, row['name'], row['country'], row['latitude'], row['longitude']))
        id_counter += 1
    
    db_connection.commit()
    print(f"✓ {len(cities_df)} Einträge in Cities-Tabelle eingefügt")

    
def virus_table(df, df_antributes, db_connection):
    """
    Liest Virusnamen aus TSV ein, entfernt Duplikate und fügt sie in Virus-Tabelle ein.
    """
    virus_df = df[['name', 'taxid']].copy()
    # Remove leading/trailing whitespace from 'name' before deduplication
    virus_df['name'] = virus_df['name'].astype(str).str.strip()
    virus_df = virus_df.drop_duplicates()
    Attribute_df = (
        df_antributes[
            ['taxid', 'realm', 'kingdom', 'phylum', 'class', 'order', 'family', 'species', 'baltimore_class', 'host tax id', 'host name']
        ]
        .loc[
            df_antributes['host tax id'].isna() | df_antributes['host name'].isna()
        ]
        .drop_duplicates()
        .copy()
    )
    '''Attribute_df = df_antributes[['taxid', 'realm', 'kingdom', 'phylum', 'class', 'order', 'family', 'species', 'baltimore_class']].drop_duplicates().copy()

    virus_df = virus_df.merge(Attribute_df, on='taxid', how='left')
    
    cursor = db_connection.cursor()
     for _, row in virus_df.iterrows():
        #virus tax id,host tax id,host name,realm,kingdom,phylum,class,order,family,genus,species,baltimore_class
        cursor.execute("""
            insert into Virus (name, tax_id, realm, kingdom, phylum, class, taxonomic_order, family, species, baltimore_class)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (row['name'], row['taxid'], row['realm'], row['kingdom'], row['phylum'], row['class'], row['order'], row['family'], row['species'], row['baltimore_class']))
    '''
    cursor = db_connection.cursor()
    for _, row in virus_df.iterrows():
        cursor.execute("""
            insert into Virus (name, tax_id)
            values (?, ?)
        """, (row['name'], row['taxid']))    
    db_connection.commit()
    print(f"✓ {len(virus_df)} Einträge in Virus-Tabelle eingefügt")

def virus_in_runs_table(df, db_connection):
    """
    Liest global_merge.csv ein und verknüpft Virus mit Runs über die taxid und run_accession.
    Speichert Zellen mit Inhalt in einem neuen DataFrame: run_accession, taxid, value
    """
    # Read global_merge.csv
    #df = pd.read_csv('cities/global_merge.csv', sep=',')
    
    cursor = db_connection.cursor()
    
    # Get run_accession and taxid column names (erste und zweite Spalte)
    taxid_col = df.columns[1]
    
    # Skip first 2 columns and iterate through remaining rows
    df_filtered = df.iloc[:, 2:]
    
    # Create result dataframe
    result_df = pd.DataFrame(columns=['run_accession', 'taxid', 'value'])
    
    for row_idx, row in df_filtered.iterrows():
        # Get taxid for this row from the second column
        taxid_value = df.loc[row_idx, taxid_col]
        
        # Iterate through all columns in each row
        for col_name, value in row.items():
            # Check if value is not empty/null
            if pd.notna(value) and value != '':
                new_row = pd.DataFrame({
                    'run_accession': [col_name],
                    'taxid': [taxid_value],
                    'value': [value]
                })
                result_df = pd.concat([result_df, new_row], ignore_index=True)
    
    # Insert into database
    for _, row in result_df.iterrows():
        cursor.execute("""
            INSERT INTO Virus_in_Runs (run_accession, virus_tax_id, amount_in_sample_as_percentage)
            VALUES (?, ?, ?)
        """, (row['run_accession'], row['taxid'], row['value']))
    db_connection.commit()
    print(f"✓ {len(result_df)} Einträge in Virus_in_Runs-Tabelle eingefügt")

def host_table(df, db_connection):
    
    host_df = df[['host name', 'host tax id']].copy()
    host_df = host_df.drop_duplicates().dropna(subset=['host name', 'host tax id'])
    host_df['host tax id'] = pd.to_numeric(host_df['host tax id'], errors='coerce')
    host_df = host_df.dropna(subset=['host tax id'])
    host_df['host tax id'] = host_df['host tax id'].astype(int)
    
    cursor = db_connection.cursor()
    for _, row in host_df.iterrows():
        cursor.execute("""
            INSERT INTO Host (name, host_tax_id)
            VALUES (?, ?)
        """, (row['host name'], int(row['host tax id'])))
    
    db_connection.commit()
    print(f"✓ {len(host_df)} Einträge in Host-Tabelle eingefügt")

def virus_host_table(df, db_connection):
    """
    Kombiniert die Virus-Tax-IDs aus dem DataFrame mit den Host-Tax-IDs und
    schreibt die Paare in die Verknüpfungstabelle.
    """
    if {'taxid', 'host tax id'}.issubset(df.columns):
        virus_host_df = (
            df[['taxid', 'host tax id']]
            .rename(columns={'taxid': 'virus_tax_id', 'host tax id': 'host_tax_id'})
            .copy()
        )
    else:
        raise ValueError("Das DataFrame muss die Spalten 'taxid' und 'host tax id' enthalten")

    virus_host_df = virus_host_df.dropna().drop_duplicates()
    virus_host_df['virus_tax_id'] = pd.to_numeric(virus_host_df['virus_tax_id'], errors='coerce')
    virus_host_df['host_tax_id'] = pd.to_numeric(virus_host_df['host_tax_id'], errors='coerce')
    virus_host_df = virus_host_df.dropna(subset=['virus_tax_id', 'host_tax_id'])
    virus_host_df['virus_tax_id'] = virus_host_df['virus_tax_id'].astype(int)
    virus_host_df['host_tax_id'] = virus_host_df['host_tax_id'].astype(int)

    cursor = db_connection.cursor()

    existing_viruses = {row[0] for row in cursor.execute("SELECT tax_id FROM Virus").fetchall()}
    existing_hosts = {row[0] for row in cursor.execute("SELECT host_tax_id FROM Host").fetchall()}

    inserted = 0
    for _, row in virus_host_df.iterrows():
        virus_tax_id = int(row['virus_tax_id'])
        host_tax_id = int(row['host_tax_id'])

        if virus_tax_id in existing_viruses and host_tax_id in existing_hosts:
            cursor.execute(
                "INSERT OR IGNORE INTO Virus_Hosts (virus_tax_id, host_tax_id) VALUES (?, ?)",
                (virus_tax_id, host_tax_id)
            )
            if cursor.rowcount > 0:
                inserted += 1

    db_connection.commit()
    print(f"✓ {inserted} Einträge in Virus_Hosts-Tabelle eingefügt")

def weather_table(db_connection):
    cursor = db_connection.cursor()
    runs = db_connection.execute("""
        SELECT r.run_accession, r.collection_date, c.name AS city
        FROM runs r
        JOIN Cities c ON c.id = r.city_id
    """).fetchall()

    for run_accession, collection_date, city in runs:
        city_name = city.replace(" ", "")
        weather = pd.read_csv(f"cities/{city_name}/smk_output/{city_name}_weather.csv")
        row = weather[weather["time"] == collection_date].iloc[0]
        cursor.execute("""
            INSERT INTO Weather (run_accession, temperature, humidity, rainfall, wind_speed)
            VALUES (?, ?, ?, ?, ?)
        """, (
            run_accession,
            row["temperature_2m_mean (°C)"],
            row["relative_humidity_2m_mean (%)"],
            row["rain_sum (mm)"],
            None,
        ))

    db_connection.commit()
    print(f"✓ {len(runs)} Einträge in Weather-Tabelle eingefügt")




# Verwendung:
if __name__ == "__main__":
    # Verbindung zur SQLite DB
    conn = sqlite3.connect('data/db/database.db')
    
    data = pd.read_csv('cities/filtered_non_capture_samples.tsv', sep='\t')

    global_merge = pd.read_csv('cities/global_merge.csv', sep=',')

    attributes = pd.read_csv('cities/viruses/viruses_contained_with_hostid.csv', sep=',')

    # Virus- und Host-Einträge werden nicht neu aus dem DataFrame eingefügt.
    # Stattdessen werden nur die Verknüpfungen in Virus_Hosts erzeugt.

    # Zuerst Cities einfügen (wegen Foreign Key!)
    city_table(data, conn)
    
    # Dann Runs einfügen
    runs_table(data, conn)

    weather_table(conn)
    
    virus_in_runs_table(global_merge, conn)

    virus_table(global_merge, attributes, conn)

    host_table(attributes, conn)

    virus_host_table(attributes, conn)

    conn.close()
