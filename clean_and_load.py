import pandas as pd
import numpy as np
import re
import os
from sqlalchemy import create_engine, text


# ─── CONFIG ───────────────────────────────────────────────────────────────────
CSV_PATH = "Luxury_Housing_Bangalore.csv"
DB_PATH  = "luxury_housing.db"
TABLE    = "luxury_housing_sales"


# ─── 1. LOAD ──────────────────────────────────────────────────────────────────
def load_raw_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    print(f"[LOAD] Raw shape       : {df.shape}")
    print(f"[LOAD] Columns         : {list(df.columns)}")
    return df


# ─── 2. CLEAN ─────────────────────────────────────────────────────────────────
def clean_ticket_price(val) -> float:
    """Convert Ticket_Price_Cr to float. Handles mixed string/float formats."""
    if pd.isna(val):
        return np.nan
    cleaned = re.sub(r'[^\d.]', '', str(val).strip())
    try:
        return round(float(cleaned), 4)
    except ValueError:
        return np.nan


def normalize_text(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.title()


def extract_quarter_label(date_str: str) -> str:
    """
    Convert date string to Indian fiscal quarter label.
    Indian FY: Apr-Jun = Q1, Jul-Sep = Q2, Oct-Dec = Q3, Jan-Mar = Q4
    e.g. '2024-06-30' -> 'Q1 FY25'
    """
    try:
        dt = pd.to_datetime(date_str)
        month = dt.month
        year  = dt.year
        if month <= 3:
            q = 4; fy = year
        elif month <= 6:
            q = 1; fy = year + 1
        elif month <= 9:
            q = 2; fy = year + 1
        else:
            q = 3; fy = year + 1
        return f"Q{q} FY{str(fy)[-2:]}"
    except Exception:
        return "Unknown"


def derive_booking_status(transaction_type: str) -> str:
    """
    Map Transaction_Type to a Booking_Status label.
    Primary = new direct booking = 'Booked'
    Secondary = resale transaction = 'Not Booked' (from builder perspective)
    """
    if str(transaction_type).strip().lower() == 'primary':
        return 'Booked'
    return 'Not Booked'


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    # 2a. Drop exact duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f"[CLEAN] Duplicate rows removed          : {before - len(df)}")

    # 2b. Fix Ticket_Price_Cr (stored as string in raw data)
    df['Ticket_Price_Cr'] = df['Ticket_Price_Cr'].apply(clean_ticket_price)

    # 2c. Replace invalid numeric values (-1) with NaN before filling
    df['Unit_Size_Sqft'] = df['Unit_Size_Sqft'].where(df['Unit_Size_Sqft'] > 0, np.nan)
    df['Ticket_Price_Cr'] = df['Ticket_Price_Cr'].where(df['Ticket_Price_Cr'] > 0, np.nan)

    # 2d. Normalize text fields
    for col in ['Micro_Market', 'Developer_Name', 'Configuration',
                'Possession_Status', 'Buyer_Type', 'Sales_Channel',
                'Transaction_Type', 'NRI_Buyer']:
        df[col] = normalize_text(df[col])

    # 2e. Standardize Configuration values → 3BHK / 4BHK / 5BHK+
    df['Configuration'] = df['Configuration'].str.upper().str.strip()

    # 2f. Derive Booking_Status column (required by project spec)
    df['Booking_Status'] = df['Transaction_Type'].apply(derive_booking_status)

    # 2g. Handle nulls
    #   Amenity_Score → median fill
    median_amenity = df['Amenity_Score'].median()
    df['Amenity_Score'] = df['Amenity_Score'].fillna(median_amenity).round(2)
    print(f"[CLEAN] Amenity_Score nulls filled with median : {median_amenity:.2f}")

    #   Unit_Size_Sqft → median fill per Configuration group
    df['Unit_Size_Sqft'] = df.groupby('Configuration')['Unit_Size_Sqft']\
        .transform(lambda x: x.fillna(x.median()))
    df['Unit_Size_Sqft'] = df['Unit_Size_Sqft'].fillna(df['Unit_Size_Sqft'].median())

    #   Ticket_Price_Cr → median fill per Developer group
    df['Ticket_Price_Cr'] = df.groupby('Developer_Name')['Ticket_Price_Cr']\
        .transform(lambda x: x.fillna(x.median()))
    df['Ticket_Price_Cr'] = df['Ticket_Price_Cr'].fillna(df['Ticket_Price_Cr'].median())

    #   Buyer_Comments → fill with empty string (optional free-text field)
    df['Buyer_Comments'] = df['Buyer_Comments'].fillna('')

    # 2h. Drop rows with no Property_ID (primary key)
    before = len(df)
    df = df.dropna(subset=['Property_ID'])
    print(f"[CLEAN] Rows dropped (no Property_ID)   : {before - len(df)}")

    print(f"[CLEAN] Final clean shape               : {df.shape}")
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    print(f"[CLEAN] Remaining nulls: {'None' if len(nulls)==0 else nulls.to_dict()}")
    return df


# ─── 3. FEATURE ENGINEERING ───────────────────────────────────────────────────
def derive_sentiment(comment: str) -> str:
    """
    Rule-based sentiment from Buyer_Comments.
    Positive / Negative / Neutral
    """
    positive_kw = ['loved', 'excellent', 'great', 'good', 'amazing',
                   'wonderful', 'perfect', 'best', 'happy', 'underpriced']
    negative_kw = ['not responsive', 'poor', 'far', 'bad', 'slow',
                   'disappointed', 'overpriced', 'issue', 'problem']
    c = str(comment).lower()
    if any(k in c for k in positive_kw):
        return 'Positive'
    elif any(k in c for k in negative_kw):
        return 'Negative'
    return 'Neutral'


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    # Booking_Flag: 1 = Primary booking, 0 = Secondary resale
    df['Booking_Flag'] = (df['Transaction_Type'].str.lower() == 'primary').astype(int)

    # Purchase_Quarter_Label: human-readable Indian fiscal quarter
    df['Purchase_Quarter_Label'] = df['Purchase_Quarter'].apply(extract_quarter_label)

    # Quarter_Number: numeric 1-4 for sorting and analysis
    df['Quarter_Number'] = df['Purchase_Quarter_Label']\
        .str.extract(r'Q(\d)').astype(float)

    # Fiscal_Year: e.g. 'FY24'
    df['Fiscal_Year'] = df['Purchase_Quarter_Label'].str.extract(r'(FY\d+)')

    # Price_per_Sqft: ticket price in rupees divided by area
    df['Price_per_Sqft'] = (
        (df['Ticket_Price_Cr'] * 1e7) / df['Unit_Size_Sqft']
    ).round(2)

    # Amenity_Band: bucket scores into meaningful tiers
    df['Amenity_Band'] = pd.cut(
        df['Amenity_Score'],
        bins=[0, 4, 6, 8, 10],
        labels=['Low', 'Medium', 'High', 'Premium'],
        right=True
    ).astype(str)

    # NRI_Flag: binary integer version of NRI_Buyer
    df['NRI_Flag'] = (df['NRI_Buyer'].str.lower() == 'yes').astype(int)

    # Comment_Sentiment: Positive / Negative / Neutral
    df['Comment_Sentiment'] = df['Buyer_Comments'].apply(derive_sentiment)

    print("[FEAT] Engineered columns: Booking_Status, Booking_Flag, "
          "Purchase_Quarter_Label, Quarter_Number, Fiscal_Year, "
          "Price_per_Sqft, Amenity_Band, NRI_Flag, Comment_Sentiment")
    return df


# ─── 4. LOAD INTO SQLITE VIA SQLALCHEMY ──────────────────────────────────────
def load_to_db(df: pd.DataFrame, db_path: str, table: str):
    # Remove old DB for a clean load
    if os.path.exists(db_path):
        os.remove(db_path)

    # SQLAlchemy engine for SQLite
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    # Load DataFrame into SQL table
    df.to_sql(table, con=engine, if_exists='replace', index=False)
    print(f"\n[DB] Loaded {len(df):,} rows into '{table}' via SQLAlchemy")

    # Validation queries via SQLAlchemy
    print("\n─── SQL VALIDATION ───────────────────────────────────")
    with engine.connect() as conn:

        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
        print(f"[SQL] Total rows loaded               : {count:,}")

        print("\n[SQL] Booking_Status breakdown (GROUP BY):")
        rows = conn.execute(text(
            f"SELECT Booking_Status, COUNT(*) as cnt FROM {table} "
            f"GROUP BY Booking_Status ORDER BY cnt DESC"
        )).fetchall()
        for row in rows:
            print(f"       {row[0]:<15} {row[1]:>7,}")

        print("\n[SQL] AVG ticket price by top 5 developers:")
        rows = conn.execute(text(f"""
            SELECT Developer_Name,
                   ROUND(AVG(Ticket_Price_Cr),2) as avg_price,
                   COUNT(*) as units
            FROM {table}
            GROUP BY Developer_Name
            ORDER BY avg_price DESC
            LIMIT 5
        """)).fetchall()
        for row in rows:
            print(f"       {row[0]:<22} Rs.{row[1]} Cr   ({row[2]:,} units)")

        print("\n[SQL] Units by fiscal quarter:")
        rows = conn.execute(text(f"""
            SELECT Purchase_Quarter_Label, COUNT(*) as cnt,
                   ROUND(AVG(Ticket_Price_Cr),2) as avg_cr
            FROM {table}
            GROUP BY Purchase_Quarter_Label
            ORDER BY 1
        """)).fetchall()
        for row in rows:
            print(f"       {row[0]:<12}  {row[1]:>7,} units   avg Rs.{row[2]} Cr")

        print("\n[SQL] Top 5 micro-markets by volume:")
        rows = conn.execute(text(f"""
            SELECT Micro_Market, COUNT(*) as cnt,
                   ROUND(AVG(Price_per_Sqft),0) as avg_psf
            FROM {table}
            GROUP BY Micro_Market
            ORDER BY cnt DESC
            LIMIT 5
        """)).fetchall()
        for row in rows:
            print(f"       {row[0]:<25} {row[1]:>7,} units   Rs.{row[2]:,.0f}/sqft")

        print("\n[SQL] Booking conversion by sales channel:")
        rows = conn.execute(text(f"""
            SELECT Sales_Channel, COUNT(*) as total,
                   SUM(Booking_Flag) as bookings,
                   ROUND(100.0*SUM(Booking_Flag)/COUNT(*),1) as pct
            FROM {table}
            GROUP BY Sales_Channel
            ORDER BY pct DESC
        """)).fetchall()
        for row in rows:
            print(f"       {row[0]:<12}  {row[1]:>6,} inquiries  "
                  f"{row[2]:>6,} booked  {row[3]}%")

    print(f"\n[DB] Database saved to '{db_path}'  |  Table: '{table}'")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df_raw   = load_raw_data(CSV_PATH)
    df_clean = clean_data(df_raw)
    df_final = engineer_features(df_clean)
    load_to_db(df_final, DB_PATH, TABLE)

    # Export clean CSV as well (Power BI / Streamlit fallback)
    df_final.to_csv("luxury_housing_clean.csv", index=False)
    print(f"\n[OUT] Clean CSV exported.")
    print(f"[OUT] Final dataset: {len(df_final):,} rows | {len(df_final.columns)} columns")
