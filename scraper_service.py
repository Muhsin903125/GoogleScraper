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

    def search_businesses(self, query, location, max_pages=3, filter_no_website=True, filter_has_phone=False, filter_has_whatsapp=False, filter_operational=True, min_rating=0.0, min_reviews=0, max_reviews=10000, progress_callback=None):
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
                business_status = place.get('business_status')

                # Filter: Operational
                if filter_operational and business_status != 'OPERATIONAL':
                    continue

                # Early filter for rating and reviews (available in search results)
                if rating < min_rating or user_ratings_total < min_reviews or user_ratings_total > max_reviews:
                    continue
                
                try:
                    # Fetch details for website and phone
                    details = self.gmaps.place(
                        place_id=place_id, 
                        fields=['name', 'formatted_address', 'formatted_phone_number', 'website', 'url', 'international_phone_number', 'rating', 'user_ratings_total', 'business_status']
                    )
                    
                    result = details.get('result', {})
                    website = result.get('website')
                    phone = result.get('formatted_phone_number')
                    intl_phone = result.get('international_phone_number')
                    
                    # Filter: No Website logic
                    if filter_no_website and website:
                        continue

                    # Filter: Has Phone
                    if filter_has_phone and not phone:
                        continue

                    # WhatsApp Logic & Filter
                    wa_link = "N/A"
                    is_whatsapp_mobile = False
                    if intl_phone:
                        # Clean phone for link
                        clean_phone = ''.join(filter(str.isdigit, intl_phone))
                        # Identify UAE mobile (+971 5x)
                        # intl_phone format is usually +971 5x xxx xxxx
                        if intl_phone.startswith('+971 5') or intl_phone.startswith('+9715'):
                            is_whatsapp_mobile = True
                            wa_link = f"https://wa.me/{clean_phone}"
                        else:
                            # Still create link if it looks like a mobile number from other regions or if user just wants the link
                            wa_link = f"https://wa.me/{clean_phone}"

                    if filter_has_whatsapp and not is_whatsapp_mobile:
                        continue

                    if progress_callback:
                        match_msg = f"[MATCH] {name}" + (" (No Website)" if not website else "") + (" (WhatsApp)" if is_whatsapp_mobile else "")
                        progress_callback(match_msg)

                    leads.append({
                        'Company Name': result.get('name'),
                        'Address': result.get('formatted_address'),
                        'Phone': phone,
                        'Intl Phone': intl_phone,
                        'WhatsApp': wa_link,
                        'Website': website if website else "None",
                        'Rating': result.get('rating'),
                        'Reviews': result.get('user_ratings_total'),
                        'Status': result.get('business_status'),
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

