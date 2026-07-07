import pandas as pd


def detect_risk(final_dataset):

    df = final_dataset.copy()

    risk_levels = []

    for _, row in df.iterrows():

        rule = str(row.get("Business Rule", ""))

        if (
            "High Outstanding" in rule
            and "Overdue Collection" in rule
            and "Construction Delay" in rule
        ):
            risk_levels.append("Critical")

        elif (
            "High Outstanding" in rule
            and "Overdue Collection" in rule
        ):
            risk_levels.append("High")

        elif (
            "High Outstanding" in rule
            or "Construction Delay" in rule
            or "Overdue Collection" in rule
        ):
            risk_levels.append("Medium")

        else:
            risk_levels.append("Low")

    df["Risk Level"] = risk_levels

    return df