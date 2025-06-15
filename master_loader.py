import pandas as pd

def load_watchlist(filename):
    # Read raw data
    df = pd.read_csv(filename, sep="\t", header=None, dtype=str)
    # Provide column names exactly matching the number of columns in file
    base_columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
    ]
    # Only assign as many columns as present in the data
    df.columns = base_columns[:df.shape[1]]
    # Guarantee all required columns exist
    for col in ["segment", "token", "symbol", "instrument"]:
        if col not in df.columns:
            df[col] = ""
    # Return only the required columns
    return df[["segment", "token", "symbol", "instrument"]]

if __name__ == "__main__":
    df = load_watchlist("master.csv")
    print(df.head())
