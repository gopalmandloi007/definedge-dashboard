import os
import requests
from logging import INFO, basicConfig, info, warning
from dotenv import load_dotenv, set_key
from integrate import ConnectToIntegrate, IntegrateOrders
from tabulate import tabulate
from datetime import datetime, timedelta

basicConfig(level=INFO)
dotenv_file = '/content/.env'
load_dotenv(dotenv_file)

def update_env_session_keys(uid, actid, api_session_key, ws_session_key):
    os.environ["INTEGRATE_UID"] = uid
    os.environ["INTEGRATE_ACTID"] = actid
    os.environ["INTEGRATE_API_SESSION_KEY"] = api_session_key
    os.environ["INTEGRATE_WS_SESSION_KEY"] = ws_session_key
    set_key(dotenv_file, "INTEGRATE_UID", uid)
    set_key(dotenv_file, "INTEGRATE_ACTID", actid)
    set_key(dotenv_file, "INTEGRATE_API_SESSION_KEY", api_session_key)
    set_key(dotenv_file, "INTEGRATE_WS_SESSION_KEY", ws_session_key)

def ensure_active_session(conn):
    try:
        io = IntegrateOrders(conn)
        test = io.holdings()
        if (
            isinstance(test, dict)
            and str(test.get("status", "")).upper() in ["FAILED", "FAIL", "ERROR"]
            and "session" in str(test.get("message", "")).lower()
        ):
            warning("Session expired, re-logging in.")
            raise Exception("Session expired")
        return io
    except Exception:
        api_token = os.environ["INTEGRATE_API_TOKEN"]
        api_secret = os.environ["INTEGRATE_API_SECRET"]
        conn.login(api_token=api_token, api_secret=api_secret)
        uid, actid, api_session_key, ws_session_key = conn.get_session_keys()
        update_env_session_keys(uid, actid, api_session_key, ws_session_key)
        info("Session refreshed successfully.")
        return IntegrateOrders(conn)

def get_definedge_ltp_and_yclose(segment, token, session_key, max_days_lookback=10):
    headers = {'Authorization': session_key}
    ltp = None
    try:
        url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{segment}/{token}"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            ltp = float(data.get('ltp')) if data.get('ltp') not in (None, "null", "") else None
    except Exception:
        pass

    yclose = None
    closes = []
    for offset in range(1, max_days_lookback+1):
        dt = datetime.now() - timedelta(days=offset-1)
        date_str = dt.strftime('%d%m%Y')
        from_time = f"{date_str}0000"
        to_time = f"{date_str}1530"
        url = f"https://data.definedgesecurities.com/sds/history/{segment}/{token}/day/{from_time}/{to_time}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().splitlines()
                for line in lines:
                    fields = line.split(',')
                    if len(fields) >= 5:
                        closes.append(float(fields[4]))
                if len(closes) >= 2:
                    break
        except Exception:
            pass
        if len(closes) >= 2:
            break
    closes = list(dict.fromkeys(closes))
    if len(closes) >= 2:
        yclose = closes[-2]
    return ltp, yclose

def build_master_mapping_from_holdings(holdings_book):
    mapping = {}
    raw = holdings_book.get('data', [])
    if not isinstance(raw, list):
        return mapping
    for h in raw:
        tradingsymbols = h.get("tradingsymbol")
        if isinstance(tradingsymbols, list):
            for ts in tradingsymbols:
                exch = ts.get("exchange", "NSE")
                tsym = ts.get("tradingsymbol", "")
                token = ts.get("token", "")
                if exch and tsym and token:
                    mapping[(exch, tsym)] = {'segment': exch, 'token': token}
    return mapping

def print_summary_table(today_pnl, overall_pnl, total_invested, total_current):
    print("\nSummary         Amount         Total Invested value       Total current value")
    print("-----------  ---------        ----------------------     ----------------------")
    print(f"Today P&L    {today_pnl:10.2f}        {total_invested:22.2f}     {total_current:22.2f}")
    print(f"Overall P&L  {overall_pnl:10.2f}")

def print_holdings_tabular(holdings_book, master_mapping, session_key):
    raw = holdings_book.get('data', [])
    if not isinstance(raw, list) or not raw:
        print("No holdings found. RAW RESPONSE:")
        print(holdings_book)
        return

    table = []
    total_today_pnl = 0
    total_overall_pnl = 0
    total_invested = 0
    total_current = 0
    total_realized_today = 0
    total_realized_overall = 0
    headers = [
        "Symbol", "LTP", "Avg Buy", "Qty", "P.Close", "%Chg", "Today P&L", "Overall P&L",
        "Realized P&L", "%Chg Avg", "Invested", "Current", "Exchange", "ISIN", "T1", "Haircut", "Coll Qty", "Sell Amt", "Trade Qty"
    ]

    for h in raw:
        dp_qty = float(h.get("dp_qty", 0) or 0)
        avg_buy_price = float(h.get("avg_buy_price", 0) or 0)
        t1_qty = h.get("t1_qty", "N/A")
        haircut = h.get("haircut", "N/A")
        collateral_qty = h.get("collateral_qty", "N/A")
        sell_amt = float(h.get("sell_amt", 0) or 0)
        trade_qty = float(h.get("trade_qty", 0) or 0)
        tradingsymbols = h.get("tradingsymbol")
        realized_pnl = 0.0

        if isinstance(tradingsymbols, list) and tradingsymbols:
            for ts in tradingsymbols:
                exch = ts.get("exchange", "NSE")
                if exch != "NSE":
                    continue
                tsym = ts.get("tradingsymbol", "N/A")
                isin = ts.get("isin", "N/A")
                key = (exch, tsym)
                segment_token = master_mapping.get(key)
                if not segment_token:
                    ltp, yest_close = None, None
                else:
                    ltp, yest_close = get_definedge_ltp_and_yclose(segment_token['segment'], segment_token['token'], session_key)
                exited = (sell_amt > 0 and trade_qty > 0)
                holding_qty = dp_qty if dp_qty > 0 else 0
                exited_qty = trade_qty if exited else 0

                if exited and exited_qty > 0:
                    sell_price = sell_amt / exited_qty if exited_qty else 0
                    realized_pnl = (sell_price - avg_buy_price) * exited_qty
                    total_realized_today += realized_pnl
                    total_realized_overall += realized_pnl
                else:
                    realized_pnl = 0

                if holding_qty > 0:
                    invested = avg_buy_price * holding_qty
                    current = (ltp or 0) * holding_qty if ltp is not None else 0
                    today_pnl = (ltp - yest_close) * holding_qty if ltp is not None and yest_close is not None else 0
                    overall_pnl = (ltp - avg_buy_price) * holding_qty if ltp is not None else 0
                    pct_change = ((ltp - yest_close) / yest_close * 100) if ltp is not None and yest_close not in (None, 0) else "N/A"
                    pct_change_avg = ((ltp - avg_buy_price) / avg_buy_price * 100) if ltp is not None and avg_buy_price not in (None, 0) else "N/A"
                else:
                    invested = 0
                    current = 0
                    today_pnl = 0
                    overall_pnl = 0
                    pct_change = "N/A"
                    pct_change_avg = "N/A"

                total_today_pnl += today_pnl
                total_overall_pnl += overall_pnl
                total_invested += invested
                total_current += current

                table.append([
                    tsym,
                    f"{ltp:.2f}" if ltp is not None else "N/A",
                    f"{avg_buy_price:.2f}",
                    int(holding_qty),
                    f"{yest_close:.2f}" if yest_close is not None else "N/A",
                    f"{pct_change:.2f}" if isinstance(pct_change, float) else pct_change,
                    f"{today_pnl:.2f}" if isinstance(today_pnl, float) else today_pnl,
                    f"{overall_pnl:.2f}" if isinstance(overall_pnl, float) else overall_pnl,
                    f"{realized_pnl:.2f}" if realized_pnl else "",
                    f"{pct_change_avg:.2f}" if isinstance(pct_change_avg, float) else pct_change_avg,
                    f"{invested:.2f}",
                    f"{current:.2f}",
                    exch,
                    isin,
                    t1_qty,
                    haircut,
                    collateral_qty,
                    f"{sell_amt:.2f}",
                    int(trade_qty)
                ])

    total_today_pnl += total_realized_today
    total_overall_pnl += total_realized_overall

    if not table:
        print("No NSE holdings found after filtering for exchange = 'NSE'")
        return

    print("\n=========== Holdings ===========\n")
    print_summary_table(total_today_pnl, total_overall_pnl, total_invested, total_current)
    print(f"\nTotal NSE Holdings: {len(table)}\n")
    print(tabulate(table, headers=headers, tablefmt="simple", floatfmt=".2f"))

def print_positions_tabular(positions_book):
    raw = positions_book.get('positions', [])
    if not isinstance(raw, list) or not raw:
        print("\nNo positions found. RAW RESPONSE:")
        print(positions_book)
        return

    important_cols = [
        ("tradingsymbol", "Symbol"),
        ("net_averageprice", "Avg. Buy"),
        ("net_quantity", "Qty"),
        ("unrealized_pnl", "Unrealised P&L"),
        ("realized_pnl", "Realized P&L"),
        ("percent_change", "% Change"),
        ("product_type", "Product Type"),
    ]
    all_keys = list(raw[0].keys()) if raw else []
    rest_keys = [k for k in all_keys if k not in [col[0] for col in important_cols]]
    headers = [col[1] for col in important_cols] + rest_keys
    table = []
    total_unrealized = 0.0
    total_realized = 0.0
    for p in raw:
        try:
            last_price = float(p.get("lastPrice", 0))
            avg_price = float(p.get("net_averageprice", 0))
            if avg_price:
                percent_change = round((last_price - avg_price) / avg_price * 100, 2)
            else:
                percent_change = "N/A"
        except Exception:
            percent_change = "N/A"
        row = [p.get(col[0], "") for col in important_cols[:-2]]
        row.append(percent_change)
        row.append(p.get("product_type", ""))
        row += [p.get(k, "") for k in rest_keys]
        table.append(row)
        try:
            total_unrealized += float(p.get("unrealized_pnl", 0) or 0)
        except Exception:
            pass
        try:
            total_realized += float(p.get("realized_pnl", 0) or 0)
        except Exception:
            pass

    summary_table = [
        ["Total Realized P&L", round(total_realized, 2)],
        ["Total Unrealized P&L", round(total_unrealized, 2)],
        ["Total Net P&L", round(total_realized + total_unrealized, 2)]
    ]
    print("\n=========== Positions ===========\n")
    print(tabulate(summary_table, headers=["Summary", "Amount"], tablefmt="simple", floatfmt=".2f"))
    print(f"\nTotal NSE Positions: {len(table)}\n")
    print(tabulate(table, headers=headers, tablefmt="simple"))

def main():
    try:
        api_token = os.environ["INTEGRATE_API_TOKEN"]
        api_secret = os.environ["INTEGRATE_API_SECRET"]
    except KeyError:
        raise KeyError("Please set INTEGRATE_API_TOKEN and INTEGRATE_API_SECRET in /content/.env file.")
    conn = ConnectToIntegrate()
    try:
        uid = os.environ["INTEGRATE_UID"]
        actid = os.environ["INTEGRATE_ACTID"]
        api_session_key = os.environ["INTEGRATE_API_SESSION_KEY"]
        ws_session_key = os.environ["INTEGRATE_WS_SESSION_KEY"]
        conn.set_session_keys(uid, actid, api_session_key, ws_session_key)
    except KeyError:
        pass

    io = ensure_active_session(conn)
    session_key = os.environ.get("INTEGRATE_API_SESSION_KEY")
    try:
        holdings_book = io.holdings()
        master_mapping = build_master_mapping_from_holdings(holdings_book)
        print_holdings_tabular(holdings_book, master_mapping, session_key)
    except Exception as e:
        import traceback
        print("Failed to get holdings:", e)
        traceback.print_exc()

    try:
        positions_book = io.positions()
        print_positions_tabular(positions_book)
    except Exception as e:
        print(f"Failed to get positions: {e}")

if __name__ == "__main__":
    main()
