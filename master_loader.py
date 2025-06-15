import pandas as pd

def load_watchlist(filename):
    # Read the file, which now always has 15 columns
    columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2", "company"
    ]
    df = pd.read_csv(filename, sep="\t", header=None, dtype=str)
    # Assign the first 15 columns only (if extra columns, ignore; if less, will error, which is correct for your standard)
    df = df.iloc[:, :15]
    df.columns = columns
    return df[["segment", "token", "symbol", "instrument", "company"]]

if __name__ == "__main__":
    df = load_watchlist("master.csv")
    print(df.head())
