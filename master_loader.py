import pandas as pd

def load_watchlist(filename):
    # All files now have 15 columns; last column ("company") is blank for indices
    columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "company"
    ]
    df = pd.read_csv(filename, sep="\t", header=None, dtype=str)
    df = df.iloc[:, :15]  # Always trim to 15 columns in case of extra
    df.columns = columns
    return df[["segment", "token", "symbol", "instrument", "company"]]

if __name__ == "__main__":
    df = load_watchlist("master.csv")
    print(df.head())
