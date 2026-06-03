import pandas as pd

df1 = pd.read_table(snakemake.input[0], names=(snakemake.wildcards.sample, "count", "spec_count", "rank", "taxid", "name"))
level = snakemake.params.level

df1new = df1.drop(index=[0,1], columns=["count", "spec_count"])

df1new = df1new.loc[df1new["rank"]==level].drop(columns=["rank"])
df = df1new[["name", "taxid", snakemake.wildcards.sample]]


df.to_csv(snakemake.output[0], index=False)
