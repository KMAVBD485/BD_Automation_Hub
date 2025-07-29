import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="PRT Birthdays Service Awardees Reconciliation Tool", layout="wide")
st.title(':blue[PRT Birthdays Service Awardees Reconciliation Tool]')

### Active Sheets #### > will need to update to include data for consultantse
@st.cache_data
def get_active_ph_employees():
    conn = st.connection("gsheets", type=GSheetsConnection)
    data = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1U7VHmsc3FHPzTHmK4mNTYZZrlLrW6aoTDErrAL6Z_MI/edit#gid=672401421", worksheet="Active-Employees-(PH)-RPT", usecols=list(range(38)))
    active_ph_employees_df = pd.DataFrame(data)
    active_ph_employees_df.dropna(how='all', inplace=True)
    return active_ph_employees_df

active_ph_employees_df = get_active_ph_employees()

@st.cache_data
def get_active_vn_employees():
    conn = st.connection("gsheets", type=GSheetsConnection)
    data = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1U7VHmsc3FHPzTHmK4mNTYZZrlLrW6aoTDErrAL6Z_MI/edit#gid=65589667", worksheet="Active-Employees-(VN)-RPT", usecols=list(range(38)))
    active_vn_employees_df = pd.DataFrame(data)
    active_vn_employees_df.dropna(how='all', inplace=True)
    return active_vn_employees_df

active_vn_employees_df = get_active_vn_employees()

@st.cache_data
def get_active_ph_interns():
    conn = st.connection("gsheets", type=GSheetsConnection)
    data = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1U7VHmsc3FHPzTHmK4mNTYZZrlLrW6aoTDErrAL6Z_MI/edit#gid=1719215400", worksheet="Active-Interns-(PH)-RPT", usecols=list(range(38)))
    active_ph_interns_df = pd.DataFrame(data)
    active_ph_interns_df.dropna(how='all', inplace=True)
    return active_ph_interns_df

active_ph_interns_df = get_active_ph_interns()

months = list(calendar.month_name)[1:]
selected_month = st.selectbox("Select a Month", months)
selected_month_num = list(calendar.month_name).index(selected_month)
current_year = datetime.now().year

def normalize_employees(df, location):
    df = df.copy()
    df["Employment Type"] = "Employee"
    df["Location"] = location
    return df[["Full Name", "Birthday", "Start Date", "Employment Type", "Location"]]

def process_employees(df, location, selected_month_num, current_year):
    df = df.copy()
    df["Birthday"] = pd.to_datetime(df["Birthday"], errors='coerce')
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors='coerce')
    df["Employment Type"] = "Employee"
    df["Location"] = location

    birthday_df = df[df["Birthday"].dt.month == selected_month_num][["Birthday", "Full Name", "Employment Type", "Location"]].rename(columns={"Birthday": "Birth Date"})
    service_df = df[df["Start Date"].dt.month == selected_month_num].copy()
    service_df["Years of Service"] = current_year - service_df["Start Date"].dt.year
    service_df = service_df[service_df["Years of Service"] > 0][["Start Date", "Full Name", "Position", "Years of Service", "Employment Type", "Location"]]
    service_df.rename(columns={"Start Date": "Start Date"}, inplace=True)

    return birthday_df, service_df

ph_birthdays, ph_service = process_employees(active_ph_employees_df, "PH", selected_month_num, current_year)
vn_birthdays, vn_service = process_employees(active_vn_employees_df, "VN", selected_month_num, current_year)

def process_interns(df, selected_month_num, current_year):
    df = df.copy()
    df["Birthday"] = pd.to_datetime(df["Birthday"], errors='coerce')
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors='coerce')
    df["Employment Type"] = "Intern"
    df["Location"] = "PH"

    birthday_df = df[df["Birthday"].dt.month == selected_month_num][["Birthday", "Full Name", "Employment Type", "Location"]].rename(columns={"Birthday": "Birth Date"})
    service_df = df[df["Start Date"].dt.month == selected_month_num].copy()
    service_df["Years of Service"] = current_year - service_df["Start Date"].dt.year
    service_df = service_df[service_df["Years of Service"] > 0][["Start Date", "Full Name", "Position", "Years of Service", "Employment Type", "Location"]]
    service_df.rename(columns={"Start Date": "Start Date"}, inplace=True)

    return birthday_df, service_df

intern_birthdays, intern_service = process_interns(active_ph_interns_df, selected_month_num, current_year)

final_birthday_df = pd.concat([ph_birthdays, vn_birthdays, intern_birthdays], ignore_index=True).sort_values("Birth Date")
final_service_df = pd.concat([ph_service, vn_service, intern_service], ignore_index=True).sort_values("Start Date")
final_birthday_df["Birth Date"] = final_birthday_df["Birth Date"].dt.strftime("%B %d, %Y")
final_service_df["Start Date"] = final_service_df["Start Date"].dt.strftime("%B %d, %Y")

st.subheader("🎉 Birthday Celebrants")
st.dataframe(final_birthday_df, use_container_width=True, hide_index=True)

st.subheader("🏅 Service Awardees")
st.dataframe(final_service_df, use_container_width=True, hide_index=True)
