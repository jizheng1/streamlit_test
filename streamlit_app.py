import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

CSV_FILE = "ca_population_by_race_annual_cdph.csv"

# ---- Load & clean ----
df = pd.read_csv(CSV_FILE, engine="python")
df = df.loc[:, ~df.columns.str.contains(r"^Unnamed", na=False)]
df.columns = df.columns.str.strip()

# Coerce numeric for safety
num_cols = [c for c in df.columns if c != "Year"]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Ensure year order
df = df.sort_values("Year").reset_index(drop=True)

st.title("California Population by Race (Annual – CDPH)")

with st.expander("See full data table"):
    st.write(df)

# ---- UI ----
min_year = int(df["Year"].min())
max_year = int(df["Year"].max())

with st.form("population-form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("Choose a starting year")
        start_year = st.slider("Start Year", min_value=min_year, max_value=max_year, value=max(min_year, 2017), step=1)

    with col2:
        st.write("Choose an end year")
        end_year = st.slider("End Year", min_value=min_year, max_value=max_year, value=max_year, step=1)

    with col3:
        st.write("Choose a population")
        selectable_single = [c for c in df.columns if c != "Year"]
        default_idx = selectable_single.index("Total") if "Total" in selectable_single else 0
        target = st.selectbox("Population", options=selectable_single, index=default_idx)

    submit_btn = st.form_submit_button("Analyze", type="primary")

# ---- Validate ----
if start_year > end_year:
    st.error("Dates don't work. Start year must be <= end year.")
else:
    mask = (df["Year"] >= start_year) & (df["Year"] <= end_year)
    filtered_df = df.loc[mask].reset_index(drop=True)

    if filtered_df.empty:
        st.error("No data available for the selected year range.")
    else:
        tab1, tab2 = st.tabs(["Population change", "Compare"])

        # ---- Tab 1 ----
        with tab1:
            st.subheader(f"Population change from {start_year} to {end_year}")

            col1, col2 = st.columns(2)

            with col1:
                initial_val = df.loc[df["Year"] == start_year, target]
                final_val = df.loc[df["Year"] == end_year, target]

                if initial_val.empty or final_val.empty:
                    st.error("Selected year(s) not found in the data.")
                else:
                    initial = int(initial_val.iloc[0])
                    final = int(final_val.iloc[0])
                    pct = round((final - initial) / initial * 100, 2) if initial != 0 else 0.0
                    st.metric(label=f"{target} – {start_year}", value=f"{initial:,}")
                    st.metric(label=f"{target} – {end_year}", value=f"{final:,}", delta=f"{pct}%")

            with col2:
                fig, ax = plt.subplots()
                ax.plot(filtered_df["Year"], filtered_df[target], marker="o")
                ax.set_title(f"{target} population over time (CA)")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                st.pyplot(fig)

            # % of Total chart (y-axis 0–100)
            if "Total" in filtered_df.columns and target != "Total":
                pct_series = (filtered_df[target] / filtered_df["Total"]) * 100.0
                fig2, ax2 = plt.subplots()
                ax2.plot(filtered_df["Year"], pct_series, color="#6a5acd", marker="o")
                ax2.set_title(f"{target} as % of Total (CA)")
                ax2.set_xlabel("Year")
                ax2.set_ylabel("Percent of total (%)")
                ax2.set_ylim(0, 100)
                st.pyplot(fig2)
            elif target == "Total":
                st.info("Percentage chart not shown for 'Total'.")

        # ---- Tab 2 ----
        with tab2:
            st.subheader("Compare with other populations")

            # Exclude 'Year' and 'Total'
            compare_options = [c for c in df.columns if c not in ("Year", "Total")]
            default_sel = [target] if target in compare_options else compare_options[:1]
            compare_targets = st.multiselect("Choose populations", options=compare_options, default=default_sel)

            if compare_targets:
                # Absolute comparison
                fig, ax = plt.subplots()
                for each in compare_targets:
                    ax.plot(filtered_df["Year"], filtered_df[each], marker="o", label=each)
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                ax.legend()
                st.pyplot(fig)

                # % of Total comparison (y-axis 0–100)
                if "Total" in filtered_df.columns:
                    figp, axp = plt.subplots()
                    for each in compare_targets:
                        pct_series = (filtered_df[each] / filtered_df["Total"]) * 100.0
                        axp.plot(filtered_df["Year"], pct_series, marker="o", label=each)
                    axp.set_xlabel("Year")
                    axp.set_ylabel("Percent of total (%)")
                    axp.set_title("Selected populations as % of Total (CA)")
                    axp.set_ylim(0, 100)
                    axp.legend()
                    st.pyplot(figp)
                else:
                    st.warning("Cannot compute percentages: 'Total' column is missing.")
            else:
                st.info("Select at least one series to compare.")
