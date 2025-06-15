import pandas as pd

def load_watchlist(filename):
    df = pd.read_csv(filename, sep="\t", header=None)
    # Always assign exactly as many column names as the file has
    all_columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
    ]
    df.columns = all_columns[:df.shape[1]]
    # Ensure required columns are present (add as empty string if missing)
    for col in ["segment", "token", "symbol", "instrument"]:
        if col not in df.columns:
            df[col] = ""
    # Always return the required columns for your scanner
    return df[["segment", "token", "symbol", "instrument"]]

if __name__ == "__main__":
    df = load_watchlist("master.csv")
    print(df.head())
