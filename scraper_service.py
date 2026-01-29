import googlemaps
import time
import pandas as pd
from datetime import datetime

class ScraperService:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.gmaps = googlemaps.Client(key=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Google Maps Client: {e}")

    def search_businesses(self, query, location, max_pages=3, filter_no_website=True, min_rating=0.0, min_reviews=0, progress_callback=None):
        """
        Searches for businesses and filters based on provided criteria.
        """
        search_query = f"{query} in {location}"
        if progress_callback:
            progress_callback(f"Starting search for: {search_query}")
        
        leads = []
        next_page_token = None
        page_count = 0

        while page_count < max_pages:
            page_count += 1
            if progress_callback:
                progress_callback(f"Fetching page {page_count}...")

            try:
                results = self.gmaps.places(
                    query=search_query, 
                    page_token=next_page_token
                )
            except googlemaps.exceptions.ApiError as e:
                if "LegacyApiNotActivatedMapError" in str(e):
                    if progress_callback:
                        progress_callback("ERROR: 'Places API' (Legacy) is not enabled. Please enable it in Google Cloud Console.")
                    raise Exception("Legacy Places API not enabled. Enable 'Places API' service.")
                
                if progress_callback:
                    progress_callback(f"API Error: {e}")
                break
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Unexpected Error: {e}")
                break

            status = results.get('status')
            if status == 'REQUEST_DENIED':
                 msg = results.get('error_message', 'Unknown Error')
                 if progress_callback:
                     progress_callback(f"API DENIED: {msg}")
                 break

            places = results.get('results', [])
            if progress_callback:
                progress_callback(f"Found {len(places)} candidates. Checking details...")

            for place in places:
                place_id = place.get('place_id')
                name = place.get('name')
                rating = place.get('rating', 0)
                user_ratings_total = place.get('user_ratings_total', 0)

                # Early filter for rating and reviews (available in search results)
                if rating < min_rating or user_ratings_total < min_reviews:
                    continue
                
                try:
                    # Fetch details for website
                    details = self.gmaps.place(
                        place_id=place_id, 
                        fields=['name', 'formatted_address', 'formatted_phone_number', 'website', 'url', 'international_phone_number', 'rating', 'user_ratings_total']
                    )
                    
                    result = details.get('result', {})
                    website = result.get('website')
                    
                    # Filter: No Website logic
                    if filter_no_website and website:
                        continue # Skip if it has a website but we want none

                    if progress_callback:
                        match_msg = f"[MATCH] {name}" + (" (No Website)" if not website else "")
                        progress_callback(match_msg)
                    
                    # WhatsApp Logic
                    intl_phone = result.get('international_phone_number')
                    wa_link = "N/A"
                    if intl_phone:
                        clean_phone = ''.join(filter(str.isdigit, intl_phone))
                        wa_link = f"https://wa.me/{clean_phone}"

                    leads.append({
                        'Company Name': result.get('name'),
                        'Address': result.get('formatted_address'),
                        'Phone': result.get('formatted_phone_number'),
                        'Intl Phone': intl_phone,
                        'WhatsApp': wa_link,
                        'Website': website if website else "None",
                        'Rating': result.get('rating'),
                        'Reviews': result.get('user_ratings_total'),
                        'Google Maps URL': result.get('url'),
                        'Place ID': place_id
                    })

                    
                    # Rate limit slight delay
                    time.sleep(0.1)

                except Exception as e:
                    if progress_callback:
                        progress_callback(f"Error checking {name}: {e}")

            next_page_token = results.get('next_page_token')
            
            if not next_page_token:
                break
            
            if progress_callback:
                progress_callback("Waiting for next page token...")
            time.sleep(2) # Required by Google API

        return pd.DataFrame(leads)

