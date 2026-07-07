import pandas as pd


def load_collections_data():
    file_path = "data/AI_Assignment_Input_3_Collections_Tracker.xlsx"

    collections = pd.read_excel(
        file_path,
        header=3
    )

    # Remove completely empty columns
    collections.dropna(axis=1, how="all", inplace=True)

    # Remove unnamed columns
    collections = collections.loc[
        :, ~collections.columns.str.contains("^Unnamed")
    ]

    # Remove duplicate rows
    collections.drop_duplicates(inplace=True)

    return collections