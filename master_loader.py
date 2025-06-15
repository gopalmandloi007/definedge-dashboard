import pandas as pd

def load_watchlist(filename):
    # Read raw lines, ignore empty lines
    with open(filename, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    # Parse each line into fields
    records = [line.strip().split("\t") for line in lines]
    # Ignore rows with fewer than 3 columns
    records = [row for row in records if len(row) >= 3]
    # Convert to DataFrame
    df = pd.DataFrame(records)
    # Assign columns dynamically
    base_columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
    ]
    df.columns = base_columns[:df.shape[1]]
    # Ensure these columns always exist
    for col in ["segment", "token", "symbol", "instrument"]:
        if col not in df.columns:
            df[col] = ""
    # Return only what you need
    return df[["segment", "token", "symbol", "instrument"]]

if __name__ == "__main__":
    df = load_watchlist("watchlist_6.csv")
    print(df.head())
