import pandas as pd


def load_aop_data():

    file_path = "data/AI_Assignment_Input_4_AOP_Targets.xlsx"

    aop = {
        "summary": pd.read_excel(
            file_path,
            sheet_name="Summary Targets",
            header=1
        ),

        "sales": pd.read_excel(
            file_path,
            sheet_name="Sales Targets",
            header=1
        ),

        "collections": pd.read_excel(
            file_path,
            sheet_name="Collections Targets",
            header=1
        ),

        "construction": pd.read_excel(
            file_path,
            sheet_name="Construction CoC Targets",
            header=1
        ),

        "ncf": pd.read_excel(
            file_path,
            sheet_name="NCF Details Target",
            header=1
        ),

        "decision": pd.read_excel(
            file_path,
            sheet_name="Decision Items",
            header=1
        )
    }

  
    for key in aop:

        aop[key].dropna(axis=1, how="all", inplace=True)
        aop[key].dropna(how="all", inplace=True)
        aop[key].columns = aop[key].columns.str.strip()

    return aop