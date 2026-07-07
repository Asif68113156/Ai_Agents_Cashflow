def validate(df, name):

    print("=" * 60)
    print(name)
    print("=" * 60)

    print("Shape:", df.shape)
    print()

    print("Missing Values")
    print(df.isnull().sum())

    print()

    print("Duplicate Rows")
    print(df.duplicated().sum())