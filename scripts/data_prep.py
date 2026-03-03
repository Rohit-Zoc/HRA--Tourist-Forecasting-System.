import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_raw_data() -> pd.DataFrame:
    csv_path = DATA_DIR / "entry_data.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {csv_path}")
    df_raw = pd.read_csv(csv_path)
    return df_raw


def clean_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()

    # Type conversions and derived time features
    df["Visit_Date"] = pd.to_datetime(df["Visit_Date"])
    df["Day"] = df["Visit_Date"].dt.day
    df["Day_of_Week"] = df["Visit_Date"].dt.day_name()
    df["Quarter"] = df["Visit_Date"].dt.quarter
    df["Month_Name"] = df["Visit_Date"].dt.month_name()

    # Categorical optimization
    categorical_cols = [
        "Nationality",
        "Purpose_of_Visit",
        "Gender",
        "Day_of_Week",
        "Month_Name",
    ]
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # Logical validations (no mutation here, just checks)
    _validate_data(df)

    # Age groups
    age_bins = [0, 25, 35, 45, 55, 65, 100]
    age_labels = ["18-25", "26-35", "36-45", "46-55", "56-65", "65+"]
    df["Age_Group"] = pd.cut(df["Age"], bins=age_bins, labels=age_labels)

    return df


def _validate_data(df: pd.DataFrame) -> None:
    # Missing values
    missing_count = df.isnull().sum().sum()
    if missing_count > 0:
        print(f"Warning: dataset contains {missing_count} missing values.")

    # Duplicates
    exact_duplicates = df.duplicated().sum()
    id_duplicates = df["Visitor_ID"].duplicated().sum()
    if exact_duplicates or id_duplicates:
        print(
            f"Warning: exact duplicates={exact_duplicates}, "
            f"duplicate Visitor_IDs={id_duplicates}"
        )

    # Logical ranges
    invalid_age = df[(df["Age"] < 10) | (df["Age"] > 80)]
    if len(invalid_age) > 0:
        print(
            f"Warning: {len(invalid_age)} records with unusual age "
            f"({df['Age'].min()}–{df['Age'].max()})."
        )

    invalid_duration = df[
        (df["Expedition_Duration_Days"] < 1)
        | (df["Expedition_Duration_Days"] > 90)
    ]
    if len(invalid_duration) > 0:
        print(
            f"Warning: {len(invalid_duration)} records with unusual duration "
            f"({df['Expedition_Duration_Days'].min()}–"
            f"{df['Expedition_Duration_Days'].max()} days)."
        )

    invalid_fee = df[df["Permit_Fee_USD"] <= 0]
    if len(invalid_fee) > 0:
        print(
            f"Warning: {len(invalid_fee)} records with non‑positive permit fee."
        )


def build_yearly_summary(df: pd.DataFrame) -> pd.DataFrame:
    yearly = (
        df.groupby("Year")
        .agg(
            Total_Visitors=("Visitor_ID", "count"),
            Total_Revenue_USD=("Permit_Fee_USD", "sum"),
            Avg_Duration=("Expedition_Duration_Days", "mean"),
            Avg_Age=("Age", "mean"),
        )
        .reset_index()
    )
    yearly["Total_Revenue_USD"] = yearly["Total_Revenue_USD"].astype(int)
    return yearly


def build_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    country = (
        df.groupby("Nationality")
        .agg(
            Total_Visitors=("Visitor_ID", "count"),
            Total_Revenue=("Permit_Fee_USD", "sum"),
            Avg_Duration=("Expedition_Duration_Days", "mean"),
            Avg_Age=("Age", "mean"),
        )
        .reset_index()
    )
    country = country.rename(columns={"Nationality": "Country"})
    country = country.sort_values("Total_Visitors", ascending=False)
    country["Percentage"] = (
        country["Total_Visitors"] / country["Total_Visitors"].sum() * 100
    ).round(2)
    return country


def main() -> None:
    print("Loading raw data...")
    df_raw = load_raw_data()
    print(f"Raw shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")

    print("Cleaning and enriching data...")
    df = clean_data(df_raw)

    cleaned_path = DATA_DIR / "entry_data_cleaned.csv"
    df.to_csv(cleaned_path, index=False)
    print(f"Saved cleaned data to: {cleaned_path}")

    print("Building yearly summary...")
    yearly = build_yearly_summary(df)
    yearly_path = DATA_DIR / "yearly_summary.csv"
    yearly.to_csv(yearly_path, index=False)
    print(f"Saved yearly summary to: {yearly_path}")

    print("Building country summary...")
    country = build_country_summary(df)
    country_path = DATA_DIR / "country_summary.csv"
    country.to_csv(country_path, index=False)
    print(f"Saved country summary to: {country_path}")

    print("Data preparation complete.")


if __name__ == "__main__":
    main()

