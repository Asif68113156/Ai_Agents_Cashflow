
import pandas as pd

def clean_dataframe(df):

   
    df = df.drop_duplicates()


    df = df.dropna(how="all")

    
    df = df.dropna(axis=1, how="all")

    df.columns = df.columns.str.strip()

    return df