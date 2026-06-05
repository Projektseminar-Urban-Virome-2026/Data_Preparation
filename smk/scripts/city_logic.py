import pandas as pd
import requests
from io import StringIO

def fetch_ena_data()-> pd.DataFrame:

    url = "https://www.ebi.ac.uk/ena/portal/api/search"

    params = {
        "result": "read_run",
        "query": "study_accession=PRJEB87273",
        "fields": "run_accession,sample_accession,country,collection_date,sample_alias,fastq_ftp,scientific_name,submitted_aspera,submitted_bytes",
        "format": "tsv"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text), sep="\t")
    df.to_csv("cities/PRJEB87273_runs_samples.tsv", sep="\t", index=False)

    return df

def split_capture_non_capture(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:


    df["submitted_bytes_sum"] = df["submitted_bytes"].fillna("0").apply(lambda x: sum(map(int, str(x).split(";"))))

# Typ bestimmen
    def get_type(x):
        x = str(x)
        if "/capture" in x:
            return "capture"
        elif "/non-capture" in x:
            return "non-capture"
        else:
            return None

    df["type"] = df["submitted_aspera"].apply(get_type)

    # Nur relevante Zeilen
    df_filtered = df[df["type"].notna()]

    # nur die Zeile mit der höchsten Byte-Summe bei gleicher sample_accession und type behalten
    df_max = df_filtered.loc[
        df_filtered.groupby(["sample_accession", "type"])["submitted_bytes_sum"].idxmax()
    ]

    # Aufteilen in capture und non-capture
    df_capture = df_max[df_max["type"] == "capture"].drop(columns=["submitted_bytes_sum", "type", "submitted_bytes", "submitted_aspera"])
    df_non_capture = df_max[df_max["type"] == "non-capture"].drop(columns=["submitted_bytes_sum", "type", "submitted_bytes", "submitted_aspera"])
    return df_capture, df_non_capture

def add_cities(df: pd.DataFrame)-> pd.DataFrame:


    filtered = df[
        df["sample_alias"].str.contains(r"AU-ME-|US_SE|MG_US1|MY_KL|AU_ME|AU1|CA-RE|CA1|CA-1|RD-|MY1", case=False, na=False)
        | df["country"].str.contains(r"China|Cameroon|Ecuador", case=False, na=False)
    ].copy()

    filtered["city"] = "Unknown"

    filtered.loc[filtered["country"].str.contains("China", case=False, na=False), "city"] = "Guangzhou"
    filtered.loc[filtered["country"].str.contains("Cameroon", case=False, na=False), "city"] = "Yaounde"
    filtered.loc[filtered["country"].str.contains("Ecuador", case=False, na=False), "city"] = "Quito"


    filtered.loc[filtered["sample_alias"].str.contains("MG_US1", case=False, na=False), "city"] = "Seattle"
    filtered.loc[filtered["sample_alias"].str.contains("US_SE", case=False, na=False), "city"] = "Seattle"
    filtered.loc[filtered["sample_alias"].str.contains("MY1", case=False, na=False), "city"] = "Kuala Lumpur"
    filtered.loc[filtered["sample_alias"].str.contains("MY_KL", case=False, na=False), "city"] = "Kuala Lumpur"
    filtered.loc[filtered["sample_alias"].str.contains("AU_ME", case=False, na=False), "city"] = "Melbourne"
    filtered.loc[filtered["sample_alias"].str.contains("AU1", case=False, na=False), "city"] = "Melbourne"
    filtered.loc[filtered["sample_alias"].str.contains("AU-ME-", case=False, na=False), "city"] = "Melbourne"
    filtered.loc[filtered["sample_alias"].str.contains("CA-RE", case=False, na=False), "city"] = "Regina"
    filtered.loc[filtered["sample_alias"].str.contains("CA1", case=False, na=False), "city"] = "Regina"
    filtered.loc[filtered["sample_alias"].str.contains("CA-1", case=False, na=False), "city"] = "Regina"
    filtered.loc[filtered["sample_alias"].str.contains("RD-", case=False, na=False), "city"] = "Copenhagen"


    return filtered

def main() -> None:
    df_capture, df_non_capture = split_capture_non_capture(fetch_ena_data())
    filtered_capture_df = add_cities(df_capture)
    filtered_non_capture_df = add_cities(df_non_capture)

    filtered_capture_df.to_csv("cities/filtered_capture_samples.tsv", sep="\t", index=False)
    filtered_non_capture_df.to_csv("cities/filtered_non_capture_samples.tsv", sep="\t", index=False)


if __name__ == "__main__":
    main()
