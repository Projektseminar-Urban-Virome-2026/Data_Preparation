import pandas as pd
import sqlite3

def runs_table(df, db_connection):
    """
    Liest TSV ein und fügt run_accession, sample_alias, collection_date in runs-Tabelle ein.
    """
    
    # Nur relevante Spalten auswählen
    runs_df = df[['run_accession', 'sample_alias', 'collection_date']].copy()
    
    
    cursor = db_connection.cursor()
    for _, row in runs_df.iterrows():
        cursor.execute("""
            INSERT INTO runs (run_accession, run_alias, collection_date, city_id)
            VALUES (?, ?, ?, ?)
        """, (row['run_accession'], row['sample_alias'], row['collection_date'], 1))  # city_id placeholder
    
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

    #!!!!!!!! virus_table Funktion ist nicht funktional!!!!!!!!
def virus_table(df, db_connection):
    """
    Liest Virusnamen aus TSV ein, entfernt Duplikate und fügt sie in Virus-Tabelle ein.
    """
    virus_df = df[['name', 'taxid']].drop_duplicates().copy()
    
    cursor = db_connection.cursor()
    for _, row in virus_df.iterrows():
        #virus tax id,host tax id,host name,realm,kingdom,phylum,class,order,family,genus,species,baltimore_class
        cursor.execute("""
            insert into Virus (name, tax_id)
            values (?, ?)
        """, (row['name'], row['taxid']))
    
    db_connection.commit()
    print(f"✓ {len(virus_df)} Einträge in Virus-Tabelle eingefügt")

# Verwendung:
if __name__ == "__main__":
    # Verbindung zur SQLite DB
    conn = sqlite3.connect('data/db/database.db')
    
    data = pd.read_csv('cities/filtered_non_capture_samples.tsv', sep='\t')

    global_merge = pd.read_csv('cities/global_merge.csv', sep=',')

    virus_table(global_merge, conn)

    # Zuerst Cities einfügen (wegen Foreign Key!)
    city_table(data, conn)
    
    # Dann Runs einfügen
    runs_table(data, conn)

    conn.close()
