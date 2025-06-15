import pandas as pd

def load_watchlist(filename):
    df = pd.read_csv(filename, sep="\t", header=None)
    # Assign as many columns as present in the file (up to 15)
    columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
    ]
    df.columns = columns[:df.shape[1]]
    # Ensure required columns exist
    for col in ["segment", "token", "symbol", "instrument"]:
        if col not in df.columns:
            df[col] = ""
    return df[["segment", "token", "symbol", "instrument"]]

if __name__ == "__main__":
    df = load_watchlist("master.csv")
    print(df.head())
