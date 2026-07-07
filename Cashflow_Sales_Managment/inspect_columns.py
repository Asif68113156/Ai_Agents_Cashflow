import pandas as pd

print("=== SALES COLUMNS ===")
s = pd.read_excel("data/AI_Assignment_Input_1_Sales_SANITIZED.xlsx")
s = s.loc[:, ~s.columns.str.contains("^Unnamed")]
print(list(s.columns))

print()
print("=== CONSTRUCTION COLUMNS ===")
c = pd.read_excel("data/AI_Assignment_Input_2_Construction_Tracking.xlsx", header=1)
c = c.loc[:, ~c.columns.str.contains("^Unnamed")]
print(list(c.columns))

print()
print("=== COLLECTIONS COLUMNS ===")
col = pd.read_excel("data/AI_Assignment_Input_3_Collections_Tracker.xlsx", header=3)
col = col.loc[:, ~col.columns.str.contains("^Unnamed")]
print(list(col.columns))

print()
print("=== AOP SHEETS ===")
aop_file = "data/AI_Assignment_Input_4_AOP_Targets.xlsx"
xl = pd.ExcelFile(aop_file)
print("Sheets:", xl.sheet_names)
for sheet in xl.sheet_names:
    df = pd.read_excel(aop_file, sheet_name=sheet, header=1)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    print(f"\n-- {sheet} --")
    print(list(df.columns))
