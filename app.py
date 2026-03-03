import base64
import calendar
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"


@st.cache_data
def load_clean_data() -> pd.DataFrame:
    path = DATA_DIR / "entry_data_cleaned.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Cleaned data not found at {path}. "
            f"Run scripts/data_prep.py first."
        )
    df = pd.read_csv(path, parse_dates=["Visit_Date"])
    cat_cols = [
        "Nationality",
        "Purpose_of_Visit",
        "Gender",
        "Day_of_Week",
        "Month_Name",
        "Age_Group",
    ]
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")
    return df


@st.cache_data
def build_forecasts(df: pd.DataFrame) -> dict:
    """
    Build 2026 monthly forecasts using historical averages from non-crisis years.

    Crisis years excluded: 2015 (Nepal Earthquake), 2020 & 2021 (COVID-19).
    For each month, the forecast total = average visitors in that month across
    normal years. Segment breakdowns use each category's historical share of
    that monthly total.
    """
    crisis_years = {2015, 2020, 2021}
    normal_mask = ~df["Year"].isin(crisis_years)
    df_normal = df.loc[normal_mask].copy()

    monthly_totals = (
        df_normal.groupby("Month")["Visitor_ID"].count().rename("Total_Visitors")
    )

    def monthly_share(group_cols):
        counts = (
            df_normal.groupby(["Month"] + group_cols)["Visitor_ID"]
            .count()
            .reset_index(name="Count")
        )
        merged = counts.merge(monthly_totals.reset_index(), on="Month", how="left")
        merged["Share"] = merged["Count"] / merged["Total_Visitors"]
        return merged

    gender_share = monthly_share(["Gender"])
    country_share = monthly_share(["Nationality"])
    age_share = monthly_share(["Age_Group"])
    purpose_share = monthly_share(["Purpose_of_Visit"])

    base_rows = []
    for m in range(1, 13):
        total_vis = monthly_totals.get(m, 0)
        base_rows.append(
            {
                "Year": 2026,
                "Month": m,
                "Month_Name": calendar.month_name[m],
                "Total_Visitors": int(total_vis),
            }
        )
    base = pd.DataFrame(base_rows)

    def expand_segment(base_df, share_df, seg_col, seg_label):
        seg_2026 = (
            base_df[["Year", "Month", "Month_Name", "Total_Visitors"]]
            .merge(share_df, on="Month", how="left")
            .drop(columns=["Total_Visitors_y"], errors="ignore")
        )
        seg_2026 = seg_2026.rename(columns={"Total_Visitors_x": "Total_Visitors"})
        seg_2026[seg_label] = seg_2026[seg_col]
        seg_2026["Forecast_Visitors"] = (
            seg_2026["Total_Visitors"] * seg_2026["Share"].fillna(0.0)
        ).round().astype(int)
        return seg_2026

    return {
        "base": base,
        "gender": expand_segment(base, gender_share, "Gender", "Gender"),
        "country": expand_segment(base, country_share, "Nationality", "Country"),
        "age": expand_segment(base, age_share, "Age_Group", "Age_Group"),
        "purpose": expand_segment(
            base, purpose_share, "Purpose_of_Visit", "Purpose_of_Visit"
        ),
    }


def make_horizontal_bar_chart(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    title: str,
    height: int = 300,
    color: str = "#2E86AB",
) -> alt.Chart:
    """Horizontal bar chart with category labels shown horizontally."""
    return (
        alt.Chart(df)
        .mark_bar(size=28, cornerRadiusEnd=4, color=color)
        .encode(
            x=alt.X(
                value_col,
                title="Forecasted Visitors",
                axis=alt.Axis(format=","),
            ),
            y=alt.Y(
                category_col,
                sort="-x",
                title=None,
                axis=alt.Axis(
                    labelAngle=0,
                    labelAlign="right",
                    labelLimit=200,
                ),
            ),
            tooltip=[
                alt.Tooltip(category_col, title="Category"),
                alt.Tooltip(value_col, title="Visitors", format=","),
            ],
        )
        .properties(height=height, title=title)
        .configure_axis(labelFontSize=12, titleFontSize=13)
        .configure_title(fontSize=15, font="sans-serif")
    )


def get_background_css() -> str:
    """Load local Everest image as base64 for CSS background, fallback to URL."""
    img_path = DATA_DIR / "everest.jpeg"
    if not img_path.exists():
        img_path = DATA_DIR / "Everest.jpeg"

    if img_path.exists():
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        img_src = f"data:image/jpeg;base64,{b64}"
    else:
        img_src = (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/"
            "Mt_Everest_from_Gokyo_Ri_November_5%2C_2012.jpg/"
            "1920px-Mt_Everest_from_Gokyo_Ri_November_5%2C_2012.jpg"
        )

    return f"""
    <style>
    .stApp {{
        background-image: linear-gradient(
                rgba(255, 255, 255, 0.92),
                rgba(255, 255, 255, 0.94)
            ),
            url("{img_src}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}
    </style>
    """


def main() -> None:
    st.set_page_config(
        page_title="Everest Region Tourism Forecast Dashboard",
        layout="wide",
    )

    st.markdown(get_background_css(), unsafe_allow_html=True)

    st.title("Everest Region Tourism Dashboard")
    st.markdown(
        "Analysis and **2026 monthly forecasts** for visitors to the "
        "Everest region (Namche Bazar area)."
    )

    df = load_clean_data()
    forecasts = build_forecasts(df)

    month_names = [calendar.month_name[i] for i in range(1, 13)]
    selected_month_name = st.selectbox(
        "**Select month in 2026**",
        options=month_names,
        index=3,
        help="Choose the month to view 2026 forecasts.",
    )
    month_slider = month_names.index(selected_month_name) + 1

    base = forecasts["base"]
    row = base[base["Month"] == month_slider].iloc[0]

    st.subheader(f"2026 Forecast – {selected_month_name}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Forecasted Visitors", f"{int(row['Total_Visitors']):,}")
    with col2:
        st.metric(
            "Historical Avg (normal years)",
            f"{int(row['Total_Visitors']):,}",
            help="Average visitors for this month across non-crisis years.",
        )
    with col3:
        st.metric("Forecast Year", "2026")

    st.markdown("---")
    st.subheader(f"Segment Breakdown – {selected_month_name} 2026")

    # Gender
    gender_df = forecasts["gender"]
    gender_month = (
        gender_df[gender_df["Month"] == month_slider][["Gender", "Forecast_Visitors"]]
        .sort_values("Forecast_Visitors", ascending=False)
        .reset_index(drop=True)
    )
    st.markdown("#### Gender-wise Forecast")
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        st.altair_chart(
            make_horizontal_bar_chart(gender_month, "Gender", "Forecast_Visitors", "", height=180),
            use_container_width=True,
        )
    with col_g2:
        st.dataframe(
            gender_month.style.format({"Forecast_Visitors": "{:,.0f}"}),
            use_container_width=True,
            hide_index=True,
        )

    # Country
    country_df = forecasts["country"]
    country_month = (
        country_df[country_df["Month"] == month_slider][["Country", "Forecast_Visitors"]]
        .groupby("Country", as_index=False)["Forecast_Visitors"]
        .sum()
        .sort_values("Forecast_Visitors", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    st.markdown("#### Country-wise Forecast (Top 10)")
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        st.altair_chart(
            make_horizontal_bar_chart(
                country_month, "Country", "Forecast_Visitors", "", height=480, color="#28A745"
            ),
            use_container_width=True,
        )
    with col_c2:
        st.dataframe(
            country_month.style.format({"Forecast_Visitors": "{:,.0f}"}),
            use_container_width=True,
            hide_index=True,
        )

    # Age
    age_df = forecasts["age"]
    age_month = (
        age_df[age_df["Month"] == month_slider][["Age_Group", "Forecast_Visitors"]]
        .groupby("Age_Group", as_index=False)["Forecast_Visitors"]
        .sum()
        .sort_values("Age_Group")
        .reset_index(drop=True)
    )
    age_month["Age_Group"] = age_month["Age_Group"].astype(str)
    st.markdown("#### Age Group Forecast")
    col_a1, col_a2 = st.columns([2, 1])
    with col_a1:
        st.altair_chart(
            make_horizontal_bar_chart(
                age_month, "Age_Group", "Forecast_Visitors", "", height=260, color="#6F42C1"
            ),
            use_container_width=True,
        )
    with col_a2:
        st.dataframe(
            age_month.style.format({"Forecast_Visitors": "{:,.0f}"}),
            use_container_width=True,
            hide_index=True,
        )

    # Purpose
    purpose_df = forecasts["purpose"]
    purpose_month = (
        purpose_df[purpose_df["Month"] == month_slider][
            ["Purpose_of_Visit", "Forecast_Visitors"]
        ]
        .groupby("Purpose_of_Visit", as_index=False)["Forecast_Visitors"]
        .sum()
        .sort_values("Forecast_Visitors", ascending=False)
        .reset_index(drop=True)
        .rename(columns={"Purpose_of_Visit": "Purpose of Visit"})
    )
    st.markdown("#### Purpose of Visit Forecast")
    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        st.altair_chart(
            make_horizontal_bar_chart(
                purpose_month,
                "Purpose of Visit",
                "Forecast_Visitors",
                "",
                height=280,
                color="#FD7E14",
            ),
            use_container_width=True,
        )
    with col_p2:
        st.dataframe(
            purpose_month.style.format({"Forecast_Visitors": "{:,.0f}"}),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")
    with st.expander("Methodology"):
        st.write(
            "Forecasts are based on historical averages from **non-crisis years** "
            "(excluding 2015, 2020, 2021). For each month, we use the average total "
            "visitors as the 2026 forecast, and allocate that total to gender, country, "
            "age group, and purpose segments according to their historical shares for "
            "that month."
        )


if __name__ == "__main__":
    main()
