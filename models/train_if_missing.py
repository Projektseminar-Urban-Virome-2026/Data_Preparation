from argparse import ArgumentParser
from pathlib import Path
import os

import joblib
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml


staedte_nach_klima = {
    "Gemäßigt": ["Copenhagen", "Regina", "Seattle", "Melbourne"],
    "Subtropisch": ["Guangzhou"],
    "Tropisch": ["Kuala Lumpur", "Quito", "Yaounde"],
}

wetter_spalten = {
    "temperature_2m_mean (°C)": "Temp",
    "rain_sum (mm)": "Regen",
    "relative_humidity_2m_mean (%)": "Luftfeuchtigkeit",
}

staedte = {
    "Copenhagen": ("Copenhagen_merged_reads.csv", "Copenhagen_weather.csv"),
    "Guangzhou": ("Guangzhou_merged_reads.csv", "Guangzhou_weather.csv"),
    "Kuala Lumpur": ("KualaLumpur_merged_reads.csv", "KualaLumpur_weather.csv"),
    "Melbourne": ("Melbourne_merged_reads.csv", "Melbourne_weather.csv"),
    "Quito": ("Quito_merged_reads.csv", "Quito_weather.csv"),
    "Regina": ("Regina_merged_reads.csv", "Regina_weather.csv"),
    "Seattle": ("Seattle_merged_reads.csv", "Seattle_weather.csv"),
    "Yaounde": ("Yaounde_merged_reads.csv", "Yaounde_weather.csv"),
}


def stadt_ordner_name(stadt):
    return stadt.replace(" ", "")


def stadt_datei(data_dir, stadt, dateiname):
    return Path(data_dir) / stadt_ordner_name(stadt) / "smk_output" / dateiname


def shannon(counts, base=None, exp=False):
    counts = np.asarray(counts, dtype=float)
    counts = counts[counts > 0]
    if counts.size == 0:
        return 0.0

    proportions = counts / counts.sum()
    value = -(proportions * np.log(proportions)).sum()
    if base is not None:
        value = value / np.log(base)
    if exp:
        value = np.exp(value)
    return float(value)


def lade_stadt(stadt, virus_datei, wetter_datei, ena_data, wetter_spalten):
    # Virus-Tabelle laden + aufbereiten
    virus_df = pd.read_csv(virus_datei, index_col=0).fillna(1e-6).T
    virus_df.columns = virus_df.columns.str.strip()
    virus_df = virus_df.drop("taxid", errors="ignore")

    # Shannon-Index pro Sample
    shannon_werte = []
    for sample_id in virus_df.index:
        counts = virus_df.loc[sample_id].values
        s = shannon(counts, base=None, exp=False)
        shannon_werte.append({"run_accession": sample_id, "shannon_index": s})
    alpha_div = pd.DataFrame(shannon_werte)

    # collection_date aus ena_data holen
    ena_stadt = (
        ena_data[ena_data["run_accession"].isin(alpha_div["run_accession"])]
        [["run_accession", "collection_date"]]
        .copy()
    )
    ena_stadt["collection_date"] = pd.to_datetime(ena_stadt["collection_date"])
    data = alpha_div.merge(ena_stadt, on="run_accession")

    # Wetterdaten laden + 5-Tage-Mittelwert berechnen
    weather_df = pd.read_csv(wetter_datei)
    weather_df["time"] = pd.to_datetime(weather_df["time"])

    for csv_spalte, col_name in wetter_spalten.items():
        data[col_name] = np.nan
        for i, row in data.iterrows():
            start = row["collection_date"] - pd.Timedelta(days=4)
            maske = (weather_df["time"] >= start) & (weather_df["time"] <= row["collection_date"])
            data.at[i, col_name] = weather_df.loc[maske, csv_spalte].mean()

    # NaN-Zeilen droppen -> data_clean
    data_clean = data.dropna(subset=list(wetter_spalten.values()) + ["shannon_index"])

    return data_clean, virus_df


def modelle_vorhanden(model_dir, required_models):
    return all((Path(model_dir) / model_name).exists() for model_name in required_models)


def trainiere_modelle(config):
    data_dir = Path(config["data_dir"])
    ena_data = pd.read_csv(config["ena_file"], sep="\t")
    print(f"ENA-Daten: {len(ena_data)} Einträge")

    alle_daten = {}
    alle_virus = {}

    for stadt, (virus_datei, wetter_datei) in staedte.items():
        data_clean, virus_df = lade_stadt(
            stadt,
            stadt_datei(data_dir, stadt, virus_datei),
            stadt_datei(data_dir, stadt, wetter_datei),
            ena_data,
            wetter_spalten,
        )
        alle_daten[stadt] = data_clean
        alle_virus[stadt] = virus_df

    teile_dfs = []
    for klimazone, staedte_liste in staedte_nach_klima.items():
        for stadt in staedte_liste:
            df = alle_daten[stadt].copy()
            df["Stadt"] = stadt
            df["Klimazone"] = klimazone
            teile_dfs.append(df)

    modell_df = pd.concat(teile_dfs, ignore_index=True)
    print(modell_df.shape)

    # Baseline: Median-Shannon-Index pro Stadt
    median_pro_stadt = {}
    for stadt, daten in alle_daten.items():
        median_pro_stadt[stadt] = daten["shannon_index"].median()

    modell_df["Baseline"] = modell_df["Stadt"].map(median_pro_stadt)

    # Mixed Model: Shannon-Index
    mixed_modell = smf.mixedlm(
        "shannon_index ~ Klimazone * Temp + Regen + Luftfeuchtigkeit",
        data=modell_df,
        groups="Stadt",
    )
    ergebnis = mixed_modell.fit()

    # Tobamovirus-Anteil pro Probe
    tobamo_anteil = {}
    for stadt, virus_df in alle_virus.items():
        anteil = virus_df["Tobamovirus"]
        tobamo_anteil.update(anteil.to_dict())

    modell_df["Tobamo_Anteil"] = modell_df["run_accession"].map(tobamo_anteil)
    modell_df_tobamo = modell_df.dropna(subset=["Tobamo_Anteil"]).reset_index(drop=True)

    # Mixed Model: Tobamovirus-Anteil ~ Wetter
    tobamo_modell = smf.mixedlm(
        "Tobamo_Anteil ~ Klimazone * Temp + Regen + Luftfeuchtigkeit",
        data=modell_df_tobamo,
        groups="Stadt",
    )
    ergebnis_tobamo = tobamo_modell.fit()

    modelle_ordner = Path(config["model_dir"])
    os.makedirs(modelle_ordner, exist_ok=True)

    joblib.dump(ergebnis, modelle_ordner / "shannon_mixed_modell.pkl")
    joblib.dump(median_pro_stadt, modelle_ordner / "shannon_baseline_mediane.pkl")
    joblib.dump(ergebnis_tobamo, modelle_ordner / "tobamo_mixed_modell.pkl")

    tobamo_baseline_mediane = {}
    for stadt in modell_df_tobamo["Stadt"].unique():
        tobamo_baseline_mediane[stadt] = modell_df_tobamo[
            modell_df_tobamo["Stadt"] == stadt
        ]["Tobamo_Anteil"].median()

    joblib.dump(tobamo_baseline_mediane, modelle_ordner / "tobamo_baseline_mediane.pkl")
    print(f"Alle 4 Modelle in '{modelle_ordner}/' gespeichert")


def main():
    parser = ArgumentParser()
    parser.add_argument("--config", default="model_training/config.yaml")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    model_dir = Path(config["model_dir"])
    required_models = config["required_models"]

    if modelle_vorhanden(model_dir, required_models):
        print(f"Modelle in '{model_dir}' bereits vorhanden. Kein Training nötig.")
        return

    print(f"Modelle in '{model_dir}' fehlen. Starte Training.")
    trainiere_modelle(config)


if __name__ == "__main__":
    main()
