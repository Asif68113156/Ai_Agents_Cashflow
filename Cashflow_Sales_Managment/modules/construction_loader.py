import pandas as pd


def load_construction_data():
    file_path = "data/AI_Assignment_Input_2_Construction_Tracking.xlsx"

    construction = pd.read_excel(
        file_path,
        header=1
    )

    # Remove empty columns
    construction.dropna(axis=1, how="all", inplace=True)

    # Remove unnamed columns
    construction = construction.loc[
        :, ~construction.columns.str.contains("^Unnamed")
    ]

    # Remove duplicate rows
    construction.drop_duplicates(inplace=True)

    return construction