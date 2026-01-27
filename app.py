import streamlit as st
import pandas as pd
from scraper_service import ScraperService
import os
from datetime import datetime

# Page Config
st.set_page_config(page_title="Dubai Business No-Website Scraper", page_icon="🏢", layout="wide")

# Title
st.title("🏢 Dubai Business No-Website Scraper")
st.markdown("Find businesses in Dubai that **do not have a website**.")

# Sidebar for Config
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Google Places API Key", type="password", value="AIzaSyDiClPAo5OQ5cOLWDjTfxJPiVLzc--Kfis") # Pre-filled for convenience
    st.info("Ensure the 'Places API' (Legacy) or 'Places API (New)' is enabled in Google Cloud.")

# Main Input
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    query = st.text_input("Keywords", placeholder="e.g. Gyms, Cafes, Mechanics")

with col2:
    location = st.text_input("Location", value="Dubai")

with col3:
    max_pages = st.number_input("Max Pages", min_value=1, max_value=10, value=3)

# Search Button
if st.button("Start Search", type="primary"):
    if not api_key:
        st.error("Please provide an API Key.")
    elif not query:
        st.error("Please enter a keyword.")
    else:
        # Logs Container
        log_container = st.empty()
        logs = []

        def log_callback(msg):
            logs.append(f"{datetime.now().strftime('%H:%M:%S')} - {msg}")
            # Join logs with line breaks for a terminal look
            log_container.code("\n".join(logs[-10:]), language="bash") # Show last 10 lines

        result_placeholder = st.empty()
        
        try:
            scraper = ScraperService(api_key)
            
            with st.spinner("Scraping in progress..."):
                df = scraper.search_no_website_businesses(
                    query=query, 
                    location=location, 
                    max_pages=max_pages, 
                    progress_callback=log_callback
                )

            if not df.empty:
                st.success(f"Search Complete! Found {len(df)} leads.")
                st.dataframe(df)
                
                # Export
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
                
                # Excel
                # Need openpyxl
                output_file = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                df.to_excel(output_file, index=False)
                with open(output_file, "rb") as f:
                    st.download_button(
                        label="Download Excel",
                        data=f,
                        file_name=output_file,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.warning("No leads found matching criteria.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.code(str(e))
