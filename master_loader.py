import pandas as pd

def load_watchlist(filename):
    df = pd.read_csv(filename, sep="\t", header=None, dtype=str)
    # Only assign as many column names as there are columns
    base_columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
    ]
    # Dynamically assign column names to match the file's actual number of columns
    df.columns = base_columns[:df.shape[1]]
    # Ensure these columns always exist, even if missing in file
    for col in ["segment", "token", "symbol", "instrument"]:
        if col not in df.columns:
            df[col] = ""
    # Return only the columns you need
    return df[["segment", "token", "symbol", "instrument"]]

if __name__ == "__main__":
    df = load_watchlist("watchlist_6.csv")
    print(df.head())
