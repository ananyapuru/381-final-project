# sanitize.py

import os
import re
import datetime
import requests
import pandas as pd
from glob import glob
from dotenv import load_dotenv

load_dotenv()   # Loading all my API keys

# ─── PATHS, CONSTANTS & OUR CONFIG STUFF ─────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
DATA_DIR     = os.path.join(PROJECT_ROOT, "Datasets")
OUTPUT       = os.path.join(PROJECT_ROOT, "combined_dataset.csv")

# Proxy: assume data was collected OFFSET_YEARS before publication
# Since we don't actually know when all this data was collected and what time period it corresponds to, 
# we are proxying by using the dataset publication date - OFFSET_YEARS as the date of collection.
OFFSET_YEARS = 2

CITY_CUR    = {
    "kingcounty": "USD",
    "london":     "GBP",
    "melbourne":  "AUD",
    "new york":   "USD",
    "perth":      "AUD",
}

DATA_DATES  = {
    "kingcounty": datetime.date(2017, 1, 1),
    "london":     datetime.date(2020, 9, 1),
    "melbourne":  datetime.date(2018, 6, 5),
    "new york":   datetime.date(2024, 1, 6),
    "perth":      datetime.date(2021, 1, 1),
}

REFERENCE_DATE = datetime.date(2025, 5, 1)

# ─── API KEYS ───────────────────────────────────────────────────────────────────
FRED_API_KEY     = os.getenv("FRED_API_KEY")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")

if not FRED_API_KEY:
    raise RuntimeError("Please set FRED_API_KEY in your environment (.env)")

if not EXCHANGE_API_KEY:
    print("⚠️ Warning: EXCHANGE_API_KEY not set; FX lookups will default to 1.0")

# ─── COLUMN ALIASES & POSTCODE PATTERNS ─────────────────────────────────────────
ALIASES = {
    "sale_price":  ["saleprice", "sale_price", "price", "sold_price"],
    "bedrooms":    ["bedrooms", "bedroom2", "beds", "rooms", "no._of_bedrooms", "no. of bedrooms"],
    "bathrooms":   ["bathrooms", "bathroom", "bath", "no._of_bathrooms", "no. of bathrooms"],
    "living_area": ["sqft_living", "sqft_tot_living", "sqfttotliving", "propertysqft",
                    "area in sq ft", "landsize", "buildingarea", "floor_area", "livingarea"],
    "postcode":    ["postcode", "postal_code", "postal code", "zip", "zipcode", "zip_code"],
}

US5_AFTER_NY = re.compile(r"NY\s+(\d{5})")
GENERIC_5    = re.compile(r"(\d{5})")
UK_PC        = re.compile(r"([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})", re.I)

CITY_COUNTRY = {
    "kingcounty": ("King County", "USA"),
    "london":     ("London",      "UK"),
    "melbourne":  ("Melbourne",   "Australia"),
    "new york":   ("New York",    "USA"),
    "perth":      ("Perth",       "Australia"),
}

# ─── LOADING CPI SERIES FROM FRED ─────────────────────────────────────────────────
def load_cpi():
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id":        "CPIAUCSL",
        "api_key":          FRED_API_KEY,
        "file_type":        "json",
        "observation_start":"2015-01-01",
        "observation_end":  REFERENCE_DATE.isoformat(),
    }
    resp = requests.get(url, params=params).json().get("observations", [])
    records = []
    for o in resp:
        if o["value"] != ".":
            dt = datetime.datetime.strptime(o["date"], "%Y-%m-%d").date()
            records.append((dt, float(o["value"])))
    return pd.Series({d: v for d, v in records}).sort_index()

CPI_SERIES = load_cpi()

def inflation_factor(base_date):
    sub = CPI_SERIES[CPI_SERIES.index <= base_date]
    c0  = sub.iloc[-1]
    c1  = CPI_SERIES.iloc[-1]
    return c1 / c0

# ─── FX LOOKUP (with amount=1) ─────────────────────────────────────────────────
FX_CACHE = {}
def get_fx_rate(date_str, base_ccy):
    if base_ccy.upper() == "USD":
        return 1.0
    key = (date_str, base_ccy)
    if key in FX_CACHE:
        return FX_CACHE[key]
    if not EXCHANGE_API_KEY:
        rate = 1.0
    else:
        try:
            r = requests.get(
                "https://api.exchangerate.host/convert",
                params={
                    "access_key": EXCHANGE_API_KEY,
                    "from":       base_ccy,
                    "to":         "USD",
                    "date":       date_str,
                    "amount":     1
                }
            ).json()
            # prefer top-level result, then info.rate
            rate = r.get("result") or r.get("info", {}).get("rate")
            if rate is None:
                raise ValueError(f"No rate in response: {r}")
        except Exception as e:
            print(f"⚠️ FX lookup failed for {base_ccy} on {date_str}: {e}")
            rate = 1.0
    FX_CACHE[key] = rate
    return rate

# ─── SANITIZE A SINGLE CSV FILE ────────────────────────────────────────────────
def find_col(df, aliases):
    lc = {c.lower(): c for c in df.columns}
    for a in aliases:
        if a in lc:
            return lc[a]
    return None

def extract_ny_zip(df, col):
    return df[col].astype(str).str.extract(US5_AFTER_NY, expand=False).fillna("")

def generic_pc(df):
    for c in df.select_dtypes(include="object"):
        s = df[c].astype(str)
        z = s.str.extract(GENERIC_5, expand=False).fillna("")
        if z.str.len().gt(0).any():
            return z
        u = s.str.extract(UK_PC, expand=False).fillna("")
        if u.str.len().gt(0).any():
            return u
    return pd.Series([""] * len(df))

def sanitize_file(path):
    df   = pd.read_csv(path)
    name = os.path.splitext(os.path.basename(path))[0].lower()
    df.columns = df.columns.str.strip()

    # map required columns
    colmap = {}
    for key, aliases in ALIASES.items():
        col = find_col(df, aliases)
        if col:
            colmap[key] = col

    # New York postcode from formatted_address
    if name == "new york":
        fa = find_col(df, ["formatted_address"])
        if fa:
            df["__pc__"] = extract_ny_zip(df, fa)
            colmap["postcode"] = "__pc__"

    # generic postcode fallback
    if "postcode" not in colmap:
        df["__pc__"] = generic_pc(df)
        colmap["postcode"] = "__pc__"

    missing = [k for k in ALIASES if k not in colmap]
    if missing:
        print(f"⚠️ SKIP {name}.csv – missing: {missing}")
        return None

    sub = df[[colmap[k] for k in ALIASES]].copy()
    sub.columns = list(ALIASES.keys())
    for num in ["sale_price", "bedrooms", "bathrooms", "living_area"]:
        sub[num] = pd.to_numeric(sub[num], errors="coerce")

    city, country = CITY_COUNTRY[name]
    sub["city"]         = city
    sub["country"]      = country

    # proxy collection date
    pub  = DATA_DATES[name]
    base = pub - datetime.timedelta(days=OFFSET_YEARS * 365)
    sub["dataset_date"] = base
    sub["currency"]     = CITY_CUR[name]

    return sub

# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    dfs = []
    for p in glob(os.path.join(DATA_DIR, "*.csv")):
        sf = sanitize_file(p)
        if sf is not None:
            dfs.append(sf)
    if not dfs:
        raise RuntimeError("No CSVs sanitized – check your column names!")

    combined = pd.concat(dfs, ignore_index=True)

    # convert & inflation adjustment
    def convert(row):
        ds  = row["dataset_date"].isoformat()
        fx  = get_fx_rate(ds, row["currency"])
        usd = row["sale_price"] * fx
        inf = inflation_factor(row["dataset_date"])
        return pd.Series({
            "sale_price_usd":                    usd,
            "sale_price_usd_inflation_adjusted": usd * inf
        })

    conv        = combined.apply(convert, axis=1)
    combined    = pd.concat([combined, conv], axis=1)

    combined.to_csv(OUTPUT, index=False)
    print(f"✅ Wrote {len(combined)} rows × {combined.shape[1]} cols → {OUTPUT}")

if __name__ == "__main__":
    main()
