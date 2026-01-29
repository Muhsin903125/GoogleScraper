import streamlit as st
import pandas as pd
from scraper_service import ScraperService
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(page_title="Dubai Business No-Website Scraper", page_icon="🏢", layout="wide")

# Constants
UAE_LOCATIONS = {
    "Dubai": ["Dubai Marina", "Deira", "Bur Dubai", "Jumeirah", "Downtown Dubai", "Al Quoz", "Business Bay", "Al Barsha", "JLT", "Sheikh Zayed Road"],
    "Abu Dhabi": ["Al Reem Island", "Khalifa City", "Yas Island", "Corniche", "Al Maryah Island", "Mussafah", "Saadiyat Island"],
    "Sharjah": ["Al Majaz", "Al Nahda", "Al Qasimia", "Al Khan", "Muwaileh"],
    "Ajman": ["Al Nuaimia", "Al Rashidiya", "Al Jurf"],
    "Ras Al Khaimah": ["Al Hamra Village", "Mina Al Arab"],
    "Fujairah": ["Al Faseel", "Dibba"],
    "Umm Al Quwain": ["Al Salamah"]
}

BUSINESS_CATEGORIES = [
    "Gyms", "Cafes", "Mechanics", "Dentists", "Real Estate Agencies", "Beauty Salons", 
    "Cleaning Services", "Restaurants", "Pharmacies", "Supermarkets", "Carpentry", 
    "Interior Design", "Flower Shops", "Pet Shops", "Yoga Studios", "Nurseries", 
    "Tailors", "Laundry Services", "Car Rentals", "Plumbers", "Electricians", 
    "Printing Services", "Optical Shops", "Medical Centers", "Vet Clinics", 
    "Gifting Shops", "Bakeries", "Barbershops", "Jewelry Stores", "IT Support",
    "Legal Services", "Marketing Agencies", "Accounting Firms"
]

# Sidebar for Config
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Google Places API Key", type="password", value=os.getenv("GOOGLE_PLACES_API_KEY", ""))
    st.info("Ensure the 'Places API' (Legacy) or 'Places API (New)' is enabled in Google Cloud.")
    
    st.header("🔍 Filters")
    no_website_only = st.checkbox("No Website Set (Match only businesses without a website)", value=True)
    min_rating = st.slider("Minimum Rating", 0.0, 5.0, 0.0, 0.1)
    min_reviews = st.number_input("Minimum Review Count", min_value=0, value=0)

# Main Input
col1, col2 = st.columns([1, 1])

with col1:
    selected_categories = st.multiselect(
        "Business Categories", 
        options=BUSINESS_CATEGORIES,
        placeholder="Select or type categories..."
    )
    custom_query = st.text_input("Additional Keywords (Optional)", placeholder="e.g. specialized niches")

with col2:
    selected_emirates = st.multiselect("Emirates", options=list(UAE_LOCATIONS.keys()), default=["Dubai"])
    
    available_areas = []
    for emirate in selected_emirates:
        available_areas.extend(UAE_LOCATIONS.get(emirate, []))
    
    selected_areas = st.multiselect("Areas (Optional - searches entire Emirate if empty)", options=sorted(available_areas))

max_pages = st.number_input("Max Pages per combined search", min_value=1, max_value=50, value=2)

# Search Button
if st.button("🚀 Start Search", type="primary"):
    # Combine categories and custom query
    queries = selected_categories.copy()
    if custom_query:
        queries.append(custom_query)

    if not api_key:
        st.error("Please provide an API Key.")
    elif not queries:
        st.error("Please select at least one category or enter a keyword.")
    elif not selected_emirates:
        st.error("Please select at least one Emirate.")
    else:
        # Construct search tasks
        search_locations = []
        if selected_areas:
            # Search each area with its Emirate for context
            for area in selected_areas:
                # Find which emirate this area belongs to
                for emirate, areas in UAE_LOCATIONS.items():
                    if area in areas:
                        search_locations.append(f"{area}, {emirate}")
                        break
        else:
            # Search entire Emirates
            search_locations = selected_emirates

        # Logs Container
        log_container = st.empty()
        logs = []

        def log_callback(msg):
            logs.append(f"{datetime.now().strftime('%H:%M:%S')} - {msg}")
            log_container.code("\n".join(logs[-10:]), language="bash")

        all_leads = []
        
        try:
            scraper = ScraperService(api_key)
            
            total_tasks = len(queries) * len(search_locations)
            task_progress = st.progress(0)
            current_task = 0

            with st.spinner("Scraping in progress..."):
                for q in queries:
                    for loc in search_locations:
                        current_task += 1
                        log_callback(f"Task {current_task}/{total_tasks}: Searching {q} in {loc}...")
                        
                        df = scraper.search_businesses(
                            query=q, 
                            location=loc, 
                            max_pages=max_pages, 
                            filter_no_website=no_website_only,
                            min_rating=min_rating,
                            min_reviews=min_reviews,
                            progress_callback=log_callback
                        )
                        if not df.empty:
                            all_leads.append(df)
                        
                        task_progress.progress(current_task / total_tasks)

            if all_leads:
                final_df = pd.concat(all_leads).drop_duplicates(subset=['Place ID'])
                st.success(f"Search Complete! Found {len(final_df)} unique leads across {total_tasks} search tasks.")
                st.dataframe(final_df)

                
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
