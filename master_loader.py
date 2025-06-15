import pandas as pd

def load_watchlist(filename):
    df = pd.read_csv(filename, sep="\t", header=None)
    # Use maximum columns supported by the file
    columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
    ]
    df.columns = columns[:df.shape[1]]
    # Fill missing columns with empty string
    for col in ["segment", "token", "symbol", "instrument"]:
        if col not in df.columns:
            df[col] = ""
    return df[["segment", "token", "symbol", "instrument"]]

if __name__ == "__main__":
    df = load_watchlist("master.csv")
    print(df.head())
