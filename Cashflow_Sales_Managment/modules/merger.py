import pandas as pd


def merge_sales_collections(sales, collections):

    merged = pd.merge(
        sales,
        collections,
        on="Unit Number",
        how="left",
        suffixes=("_Sales", "_Collections")
    )

    return merged


def merge_with_construction(merged_data, construction):

    # Keep only one record for each milestone
    construction = construction.drop_duplicates(
        subset=["Linked Collection Milestone"]
    )

    merged = pd.merge(
        merged_data,
        construction,
        left_on="Milestone Linked",
        right_on="Linked Collection Milestone",
        how="left"
    )

    return merged