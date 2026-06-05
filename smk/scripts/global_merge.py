import pandas as pd

set = set(snakemake.input.list)
list = list(set)
# sort the list of cities to ensure consistency in the merged dataframe over different snakemake runs
list.sort()

i = 0
for element in list:
    if element == list[-1]: break
    if element == list[0]:
        df1 = pd.read_csv(element)
        df2 = pd.read_csv(list[i + 1])
        df = df1.merge(df2, on=("taxid", "name"), how="outer")
        i += 1
    else:
        df2 = pd.read_csv(list[i + 1])
        df = df.merge(df2, on=("taxid", "name"), how="outer")
        i += 1

df.to_csv(snakemake.output[0], index=False)