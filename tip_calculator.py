import streamlit as st
import pandas as pd

# Business data
main_waiters = ["Louis", "Peggy", "Florence", "Mathabo", "Zamo", "Nadia","Nosisi","Tony"]
deli_waiters = ["Nathan", "Ken", "Admire", "Nicole", "Pretty","Cheslin","Lloyd"]
all_waiters = main_waiters + deli_waiters

runners = ["Ayabonga", "Tony", "Lusanda"]
days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

st.title("💰 Tip Calculator App - Whatfood Group")

st.write("## Select 2 Runners per day (Runner's tips come from 5% deduction from main waiters only)")

# Select runners per day
runners_per_day = {}
for day in days:
    runners_selected = st.multiselect(f"Runners working on {day} (Choose exactly 2):", runners, key=day)
    if len(runners_selected) != 2:
        st.warning(f"Please select exactly 2 runners for {day}.")
    runners_per_day[day] = runners_selected

st.write("---")
st.write("## Enter daily tips per waiter (in ZAR)")

# Input daily tips for each waiter, for each day
tips_data = {}
for waiter in all_waiters:
    st.write(f"### {waiter}")
    tips_data[waiter] = []
    for day in days:
        tip = st.number_input(f"Tips for {waiter} on {day} (R):", min_value=0.0, step=0.01, key=f"{waiter}_{day}")
        tips_data[waiter].append(tip)

if st.button("Calculate Summary"):
    # Create DataFrame of tips (waiters x days)
    df = pd.DataFrame(tips_data, index=days).T
    df.index.name = "Waiter"
    
    # Calculate 5% deductions only for main waiters, daily, and distribute among runners working that day
    deductions = pd.DataFrame(0.0, index=all_waiters, columns=days)
    runner_earnings = pd.Series(0.0, index=runners)

    for day in days:
        # Sum 5% of main waiters' tips for that day
        total_deduction = sum(df.at[waiter, day] * 0.05 for waiter in main_waiters)
        # Deduct 5% from each main waiter tip
        for waiter in main_waiters:
            deductions.at[waiter, day] = df.at[waiter, day] * 0.05
        # Distribute equally to the 2 runners on duty
        day_runners = runners_per_day.get(day, [])
        if len(day_runners) == 2:
            share = total_deduction / 2
            for runner in day_runners:
                runner_earnings[runner] += share
        else:
            st.error(f"Error: Exactly 2 runners must be selected for {day}.")

    # Calculate net tips per waiter
    net_tips = df.subtract(deductions)

    # Create runner tips DataFrame with 0s for each day
    runners_df = pd.DataFrame(0.0, index=runners, columns=days)

    # For display, assign each runner their total earnings in one row (weekly total)
    # But for daily breakdown, we keep zeros because runner tips come from daily deductions and are summed
    # So instead, we add a "Weekly Total" column for runners here
    # We'll display weekly totals separately below

    # Combine net tips (waiters) + runners with zeros (daily)
    combined_df = pd.concat([net_tips, runners_df])

    # Display table
    st.write("### Final Tips Summary (after 5% runner deduction from main waiters)")
    st.dataframe(combined_df.style.format("{:.2f}").set_caption("Tips per Waiter and Runner (R)"))

    # Weekly totals per person
    weekly_totals = combined_df.sum(axis=1)
    # Add runner earnings (total weekly)
    for runner in runners:
        weekly_totals[runner] = runner_earnings[runner]

    st.write("### Weekly Total Tips (R)")
    st.dataframe(weekly_totals.to_frame(name="Total Tips (R)").style.format("{:.2f}"))

    # Prepare CSV for download
    # Append weekly totals as a new column to combined_df
    combined_df["Weekly Total (R)"] = combined_df.sum(axis=1)
    # Update runner weekly totals
    for runner in runners:
        combined_df.at[runner, "Weekly Total (R)"] = runner_earnings[runner]

    csv = combined_df.reset_index().to_csv(index=False)

    st.download_button(
        label="Download summary as CSV",
        data=csv,
        file_name="weekly_tip_summary.csv",
        mime="text/csv"
    )
