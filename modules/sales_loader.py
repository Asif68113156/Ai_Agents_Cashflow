import pandas as pd

def load_sales_data():
    file_path = "data/AI_Assignment_Input_1_Sales_SANITIZED.xlsx"

    sales = pd.read_excel(file_path)

    # Remove completely empty columns
    sales.dropna(axis=1, how="all", inplace=True)

    # Remove unnamed columns
    sales = sales.loc[:, ~sales.columns.str.contains("^Unnamed")]

    # Remove duplicate rows
    sales.drop_duplicates(inplace=True)

    return sales