import streamlit as st
import sys

# Compatibility shim for Python 3.13 (imghdr was removed)
try:
    import imghdr
except ImportError:
    import types
    m = types.ModuleType("imghdr")
    m.what = lambda filename, h=None: None
    sys.modules["imghdr"] = m

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
    "Dubai": [
        "Dubai Marina", "Deira", "Bur Dubai", "Jumeirah", "Downtown Dubai", 
        "Al Quoz", "Business Bay", "Al Barsha", "JLT", "Sheikh Zayed Road",
        "Mirdif", "Silicon Oasis", "Dubai Investment Park", "Discovery Gardens", 
        "JVC (Jumeirah Village Circle)", "International City", "Al Nahda", 
        "Karama", "Palm Jumeirah", "Satwa", "DIFC", "City Walk", "Damac Hills", 
        "Arabian Ranches", "Dubai South", "Al Qusais", "Al Rashidiya",
        "Al Safa", "Al Wasl", "Al Manara", "Umm Suqeim", "Al Bada'a", 
        "Al Garhoud", "Al Twar", "Al Mizhar", "Al Warqaa", "Nad Al Sheba", 
        "Meydan", "Dubai Hills Estate", "Town Square", "Remraam", "Mudon", 
        "Al Furjan", "Jebel Ali Village", "Dubai Production City (IMPZ)", 
        "Dubai Studio City", "Motor City", "Sports City", "Barsha Heights (Tecom)",
        "Blue Waters Island", "Dubai Maritime City", "Nad Al Hammar"
    ],
    "Abu Dhabi": [
        "Al Reem Island", "Khalifa City", "Yas Island", "Corniche", 
        "Al Maryah Island", "Mussafah", "Saadiyat Island", "Al Zahiyah", 
        "Al Khalidiyah", "Al Muroor", "Mohamed Bin Zayed City", "Al Samha", 
        "Al Shamkha", "Masdar City", "Shakhbout City", "Baniyas",
        "Al Mushrif", "Al Bateen", "Al Rowdah", "Al Wahda", "Al Karama", 
        "Al Danah", "Al Raha Beach", "Al Reef", "Hydra Village", "Ghantoot", 
        "Ruwais", "Madinat Zayed", "Al Maryah Island Area", "Officer's City"
    ],
    "Sharjah": [
        "Al Majaz", "Al Nahda", "Al Qasimia", "Al Khan", "Muwaileh",
        "Al Taawun", "Al Jaddaf", "Al Mamzar", "Sharjah Sustainable City", 
        "Aljada", "University City", "Al Rahmaniya", "Al Suyoh",
        "Al Jubail", "Al Layyeh", "Al Sharq", "Al Fisht", "Al Mirgab", 
        "Al Heera", "Al Azra", "Al Goaz", "Al Ramaqiya", "Al Khezamia", 
        "Al Tala'a", "Al Darari", "Al Shahba", "Al Khuzama", "Al Khaledia"
    ],
    "Ajman": [
        "Al Nuaimia", "Al Rashidiya", "Al Jurf", "Al Mowaihat", 
        "Ajman Downtown", "Hamidiya", "Al Rawda", "Garden City", 
        "Emirates City", "Ajman Uptown", "Al Helio", "Al Tallah",
        "Industrial Area 1", "Industrial Area 2", "Al Bustan"
    ],
    "Ras Al Khaimah": [
        "Al Hamra Village", "Mina Al Arab", "Al Nakheel", 
        "Al Dhait", "Al Jazirah Al Hamra", "Julphar", "Khor Khwair"
    ],
    "Fujairah": [
        "Al Faseel", "Dibba", "Fujairah City Center", "Al Aqah", "Mirbah"
    ],
    "Umm Al Quwain": [
        "Al Salamah", "Umm Al Quwain Marina", "Al Raudah", "Al Haweerah"
    ]
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
    no_website_only = st.checkbox("No Website Set", value=True, help="Match only businesses without a website")
    has_phone_only = st.checkbox("Only with Phone Number", value=False)
    has_whatsapp_only = st.checkbox("Has WhatsApp (Mobile)", value=False, help="Filters for UAE mobile numbers (+971 5x)")
    operational_only = st.checkbox("Operational Only", value=True, help="Filter out closed businesses")
    
    min_rating = st.slider("Minimum Rating", 0.0, 5.0, 0.0, 0.1)
    review_range = st.slider("Review Count Range", 0, 1000, (0, 500))

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
    
    col_area1, col_area2 = st.columns([1, 1])
    with col_area1:
        selected_areas = st.multiselect("Areas (Optional - searches entire Emirate if empty)", options=sorted(available_areas))
    with col_area2:
        custom_area_input = st.text_input("Additional Areas (Optional)", placeholder="e.g. Al Warqa 1")

max_pages = st.number_input("Max Pages per combined search", min_value=1, max_value=50, value=2)

# Search Button
if st.button("🚀 Start Search", type="primary"):
    # Combine categories and custom query
    queries = selected_categories.copy()
    if custom_query:
        # Split by comma if user enters multiple formatted like "gym, cafe"
        custom_queries = [x.strip() for x in custom_query.split(',') if x.strip()]
        queries.extend(custom_queries)

    if not api_key:
        st.error("Please provide an API Key.")
    elif not queries:
        st.error("Please select at least one category or enter a keyword.")
    elif not selected_emirates:
        st.error("Please select at least one Emirate.")
    else:
        # Construct search tasks
        search_locations = []
        
        # Combine selected areas and custom areas
        all_selected_areas = selected_areas.copy()
        if custom_area_input:
             custom_areas = [x.strip() for x in custom_area_input.split(',') if x.strip()]
             all_selected_areas.extend(custom_areas)
             
        if all_selected_areas:
            # Search each area with its Emirate for context
            for area in all_selected_areas:
                # Try to find which emirate this area belongs to for better context
                # If custom area, we might just append the first selected emirate or just the area itself
                found_emirate = False
                for emirate, areas in UAE_LOCATIONS.items():
                    if area in areas:
                        search_locations.append(f"{area}, {emirate}")
                        found_emirate = True
                        break
                
                if not found_emirate:
                    # If it's a custom area or not found in our list, append with the first selected emirate
                    # This is a best-effort guess for context
                    search_locations.append(f"{area}, {selected_emirates[0]}")
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
                            filter_has_phone=has_phone_only,
                            filter_has_whatsapp=has_whatsapp_only,
                            filter_operational=operational_only,
                            min_rating=min_rating,
                            min_reviews=review_range[0],
                            max_reviews=review_range[1],
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
