import streamlit as st
import pandas as pd
import pdfplumber
import re
from datetime import date

# -----------------------------
# INITIALIZE STAFF DATABASE
# -----------------------------
if "staff_roles" not in st.session_state:
    st.session_state.staff_roles = {
        "Louis": "Main Waiter",
        "Peggy": "Main Waiter",
        "Florence": "Main Waiter",
        "Nadia": "Main Waiter",
        "Zamo": "Main Waiter",
        "Nicole": "Deli Waiter",
        "Ken": "Deli Waiter",
        "Ayabonga": "Runner",
        "Tony": "Runner"
    }

roles_list = [
    "Main Waiter",
    "Deli Waiter",
    "Runner",
    "Cleaner",
    "Night Barista",
    "Night Doorman"
]

# -----------------------------
# STAFF MANAGEMENT UI
# -----------------------------
st.sidebar.header("👥 Staff Management")

new_name = st.sidebar.text_input("Add Staff Name")
new_role = st.sidebar.selectbox("Select Role", roles_list)

if st.sidebar.button("➕ Add Staff"):
    if new_name:
        st.session_state.staff_roles[new_name] = new_role
        st.sidebar.success(f"{new_name} added as {new_role}")

# Remove staff
remove_name = st.sidebar.selectbox("Remove Staff", list(st.session_state.staff_roles.keys()))
if st.sidebar.button("❌ Remove Staff"):
    del st.session_state.staff_roles[remove_name]
    st.sidebar.success(f"{remove_name} removed")

st.sidebar.write("### Current Staff")
st.sidebar.dataframe(
    pd.DataFrame.from_dict(st.session_state.staff_roles, orient="index", columns=["Role"])
)

# -----------------------------
# FUNCTIONS
# -----------------------------
def extract_tips_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()

    sections = text.split("Report for:")
    data = []

    for section in sections[1:]:
        try:
            name = section.split("\n")[0].strip()

            net_match = re.search(r"Net result \(Takings\).*?ZAR([\d,]+\.\d+)", section, re.DOTALL)
            net = float(net_match.group(1).replace(",", "")) if net_match else 0

            grat_match = re.search(r"Net result \(Takings\).*?Plus\s+gratuity\s+([\d,]+\.\d+)", section, re.DOTALL)
            gratuity = float(grat_match.group(1).replace(",", "")) if grat_match else 0

            total = net + gratuity

            data.append({
                "Waiter": name,
                "Total_Tips": total
            })

        except:
            continue

    return pd.DataFrame(data)


def apply_tip_logic(df, runners_selected):
    df = df.copy()
    staff_roles = st.session_state.staff_roles

    df = df.set_index("Waiter")

    # Ensure all staff are included
    for name in staff_roles:
        if name not in df.index:
            df.loc[name] = 0

    df["Role"] = df.index.map(staff_roles)

    # Deduct 5% only from Main Waiters
    df["Deduction"] = df.apply(
        lambda x: x["Total_Tips"] * 0.05 if x["Role"] == "Main Waiter" else 0,
        axis=1
    )

    total_pool = df["Deduction"].sum()

    df["Final_Tips"] = df["Total_Tips"] - df["Deduction"]

    # Runner allocation
    runner_df = pd.DataFrame(index=runners_selected, columns=["Final_Tips"])
    runner_df["Final_Tips"] = 0.0

    if len(runners_selected) > 0:
        share = total_pool / len(runners_selected)
        runner_df["Final_Tips"] = share

    final_df = pd.concat([df[["Final_Tips"]], runner_df])

    return final_df


# -----------------------------
# MAIN UI
# -----------------------------
st.title("💰 Automated Tip System – Whatfood Group")

uploaded_file = st.file_uploader("📥 Upload Lightspeed PDF", type="pdf")
selected_date = st.date_input("Select date:", date.today())

# Get runners dynamically
runners_list = [name for name, role in st.session_state.staff_roles.items() if role == "Runner"]

runners_selected = st.multiselect("Select runners:", runners_list)

if uploaded_file and st.button("🚀 Process Tips"):

    extracted_df = extract_tips_from_pdf(uploaded_file)

    st.write("### 🔍 Extracted Data")
    st.dataframe(extracted_df)

    final_df = apply_tip_logic(extracted_df, runners_selected)

    final_df["Date"] = selected_date

    st.write("### 💸 Final Distribution")
    st.dataframe(final_df.style.format("{:.2f}"))

    csv = final_df.reset_index().to_csv(index=False)
    st.download_button(
        "📥 Download Results",
        csv,
        file_name=f"tips_{selected_date}.csv",
        mime="text/csv"
    )
