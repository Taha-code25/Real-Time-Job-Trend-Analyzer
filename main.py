import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
from streamlit_autorefresh import st_autorefresh
import time
from job_api import scrape_rozee_jobs, scrape_glassdoor_jobs
@st.cache_data(ttl=300) 
def load_data():
    file_path = "combined_jobs.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if "date_posted" in df.columns:
            df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce")
        return df.dropna(subset=["date_posted"])
    return pd.DataFrame()
st.title("📊 Job Market Insights Dashboard")

interval_ms = st.sidebar.number_input("⏱ Auto-refresh (ms)", value=300000)
st_autorefresh(interval=interval_ms, key="job_dashboard_refresh")

refresh_key = st.empty()

df = load_data()

if os.path.exists("combined_jobs.csv"):
    last_modified = datetime.fromtimestamp(os.path.getmtime("combined_jobs.csv"))
    st.sidebar.caption(f"Last updated: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")

if df.empty:
    st.warning("No data available. Please scrape job data.")
else:
    st.subheader("🔥 Top 5 In-Demand Job Titles")
    top_titles = df['title'].value_counts().nlargest(5)
    st.plotly_chart(px.bar(top_titles, x=top_titles.index, y=top_titles.values,
                       labels={"x": "Job Title", "y": "Count"}))
    st.subheader("📍 Cities with Most Job Openings")
    df_pakistan = df[df['location'].str.contains(', Pakistan', case=False, na=False)]
    df_pakistan['city'] = df_pakistan["location"].str.split(',').str[0].str.strip().replace('',pd.NA)
    df_pakistan = df_pakistan.dropna(subset=['city'])
    city_counts = df_pakistan['city'].value_counts().reset_index()
    city_counts.columns = ['City', 'Openings']
    fig = px.bar(city_counts.head(10), 
             x='City',
             y='Openings',
             title='Top Cities with Job Openings in Pakistan',
             color='Openings',
             labels={'City': 'City', 'Openings': 'Number of Openings'})
    st.plotly_chart(fig)
    st.subheader("📅 Job Posting Trends Over Time")
    trends = df.groupby(df["date_posted"].dt.date).size()
    st.plotly_chart(px.line(trends, x=trends.index, y=trends.values,
                        labels={"x": "Date", "y": "Job Postings"}))


st.subheader("🕵️ Run Scraper")
job_input = st.text_input("Job title", value="data analyst")
pages_input = st.slider("Pages to scrape", min_value=1, max_value=5, value=2)

if st.button("🔁 Scrape Now"):
    with st.spinner("Scraping in progress..."):
        df1 = scrape_rozee_jobs(job_input, pages_input)
        df2 = scrape_glassdoor_jobs(job_input, 1)
        combined_df = pd.concat([df1, df2])
        combined_df.to_csv("combined_jobs.csv", index=False)
        st.success(f"Scraped {len(combined_df)} jobs and saved to combined_jobs.csv.")
        st.cache_data.clear()
        refresh_key.markdown(f"Last scrape at: {datetime.now().strftime('%H:%M:%S')}", help="This forces a refresh")
        time.sleep(1)  
        st.rerun()  
