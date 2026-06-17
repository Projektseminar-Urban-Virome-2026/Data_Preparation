import sqlite3
import os

# Erstelle das data-Verzeichnis, falls es nicht existiert
#os.makedirs('data', exist_ok=True)

# Verbinde mit SQLite-Datenbank (oder erstelle sie)
conn = sqlite3.connect('data/db/database.db')
cursor = conn.cursor()

# Lese die init.sql Datei
with open('init.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

# Führe alle SQL-Befehle aus
cursor.executescript(sql_script)

# Speichere die Änderungen
conn.commit()
conn.close()

print("✓ Datenbank erfolgreich erstellt: data/db/database.db")
