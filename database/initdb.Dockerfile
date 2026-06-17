FROM python:3.11-slim

WORKDIR /app

COPY /database/init.sql /app/
COPY /database/init_db.py /app/
COPY /database/import_data.py /app/
# COPY /database/data/filtered_non_capture_samples.tsv /app/data/
COPY /database/init_and_fill_db.sh /app/

RUN chmod +x ./init_and_fill_db.sh

RUN apt-get update && apt-get install -y sqlite3 && pip install pandas && rm -rf /var/lib/apt/lists/*

CMD ["./init_and_fill_db.sh"]