import streamlit as st
import pandas as pd
from datetime import date

# GitHub Button
st.markdown(
    """
    <a href="https://github.com/tpchiripa" target="_blank">
        <button style="background-color:#4CAF50; color:white; border:none; padding:10px 20px; border-radius:10px; cursor:pointer;">
            🌐 Visit My GitHub
        </button>
    </a>
    """, unsafe_allow_html=True
)

# Business data
main_waiters = ["Louis", "Peggy", "Florence", "Mathabo", "Zamo", "Nadia","Nosisi","Tony"]
deli_waiters = ["Nathan", "Ken", "Admire", "Nicole", "Pretty","Cheslin","Lloyd"]
all_waiters = main_waiters + deli_waiters
runners = ["Ayabonga", "Tony", "Lusanda"]

st.title("💰 Interactive Tip Calculator App - Whatfood Group")

# Initialize session state storage
if "all_data" not in st.session_state:
    st.session_state.all_data = pd.DataFrame()

# Select date
selected_date = st.date_input("Select date:", date.today())

# Select runners (allow 1–3)
runners_selected = st.multiselect(f"Runners on {selected_date} (Choose 1 to 3):", runners)
if not (1 <= len(runners_selected) <= 3):
    st.warning("Please select between 1 and 3 runners.")

# Enter tips for each waiter
st.write(f"## Enter tips for {selected_date}")
tips_data = {}
for waiter in all_waiters:
    tips_data[waiter] = st.number_input(
        f"Tips for {waiter} (R):", 
        min_value=0.0, step=0.01, key=f"{waiter}_{selected_date}"
    )

if st.button("💾 Save Day's Tips"):
    df = pd.DataFrame(tips_data, index=[selected_date]).T
    df.index.name = "Waiter"
    
    # Deduct 5% from main waiters only
    deductions = {waiter: df.at[waiter, selected_date]*0.05 for waiter in main_waiters}
    total_deduction = sum(deductions.values())

    # Net tips
    net_tips = df.copy()
    for waiter in main_waiters:
        net_tips.at[waiter, selected_date] -= deductions[waiter]

    # Split runner share
    runner_earnings = {}
    if 1 <= len(runners_selected) <= 3:
        share = total_deduction / len(runners_selected)
        for r in runners_selected:
            runner_earnings[r] = share
    else:
        runner_earnings = {r: 0.0 for r in runners}

    # Combine results
    results = net_tips.copy()
    for r in runners:
        results.loc[r] = [runner_earnings.get(r, 0.0)]

    # Add this day’s data to session state
    results["Date"] = selected_date
    st.session_state.all_data = pd.concat([st.session_state.all_data, results])

    st.success(f"Saved tips for {selected_date} ✅")

# Show all saved data
if not st.session_state.all_data.empty:
    st.write("### 📊 All Saved Tip Records (Daily)")
    st.dataframe(st.session_state.all_data.style.format("{:.2f}"))

    # Export daily records
    csv_daily = st.session_state.all_data.reset_index().to_csv(index=False)
    st.download_button(
        "📥 Download All Daily Records",
        csv_daily,
        file_name="all_tip_records.csv",
        mime="text/csv"
    )

    # ---- WEEKLY SUMMARY VIEW ----
    st.write("### 📈 Weekly Summary of Tips per Waiter/Runner")

    df_all = st.session_state.all_data.copy()
    df_all = df_all.reset_index().rename(columns={"index": "Waiter"})
    df_all["Week"] = pd.to_datetime(df_all["Date"]).dt.isocalendar().week

    # Group by Waiter + Week
    weekly_summary = df_all.groupby(["Waiter", "Week"]).sum(numeric_only=True).drop(columns=["Date"])

    st.dataframe(weekly_summary.style.format("{:.2f}"))

    # Export weekly summary
    csv_summary = weekly_summary.reset_index().to_csv(index=False)
    st.download_button(
        "📥 Download Weekly Summary",
        csv_summary,
        file_name="weekly_summary_tips.csv",
        mime="text/csv"
    )
