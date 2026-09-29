# 🏢 Dubai Business No-Website Scraper

A Streamlit-based lead generation tool designed to identify businesses in Dubai that do not currently have a website listed on Google Places. This tool is ideal for digital marketing agencies and freelancers offering web development services.

## 🚀 Key Features

- **Google Places API Integration**: Real-time business search using the robust Google Maps database.
- **Smart Filtering**: Automatically identifies and isolates businesses without a website.
- **WhatsApp Integration**: Generates direct `wa.me` links for international phone numbers for instant outreach.
- **Lead Export**: Download results directly in **CSV** or **Excel (.xlsx)** format.
- **Real-time Logs**: Visual feedback during the scraping process to monitor progress.

## 🛠️ Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Muhsin903125/GoogleScraper.git
   cd GoogleScraper
   ```

2. **Install dependencies**:
   Make sure you have Python 3.8+ installed.
   ```bash
   pip install streamlit googlemaps pandas openpyxl python-dotenv
   ```

## ⚙️ Configuration

The application uses a `.env` file for configuration. Create a file named `.env` in the root directory and add your Google Places API Key:

```env
GOOGLE_PLACES_API_KEY=your_api_key_here
```

## 📋 Usage

1. **Get a Google Places API Key**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the **Places API** (Legacy) or **Places API (New)**.
   - Generate an API Key.

2. **Launch the App**:

   ```bash
   streamlit run app.py
   ```

3. **Scrape Leads**:
   - Enter your **Google Places API Key** in the sidebar.
   - Enter **Keywords** (e.g., Gyms, Cafes, Mechanics).
   - Specify the **Location** (default is "Dubai").
   - Set the number of pages to scrape.
   - Click **Start Search** and download your leads!

## 📁 Project Structure

- `app.py`: The Streamlit frontend application.
- `scraper_service.py`: Core logic for API interaction and business filtering.
- `README.md`: Project documentation.

## ⚖️ License

[MIT](LICENSE)

---

_Created by [Muhsin](https://github.com/Muhsin903125)_

## Optional enrichment of a permitted business CSV

`lead_enrichment.py` is a separate CSV-in/CSV-out workflow. It does **not** call
Google Places or export its results. Use it with a business list that you have
permission to process and export. The existing Places-based lead-export code is
not extended by this feature: Google Maps Platform terms restrict exporting
Places content and using it for advertising/lead datasets. Review the current
terms and your data rights before using the older feature:
https://cloud.google.com/maps-platform/terms

Your input needs a `Company Name` column. Optional columns are `Website` (or
`Website URL`), `Address`, `Phone`, `Intl Phone`, `Mobile`, and `Email`. For an
already known company website, no API key is needed:

```bash
python lead_enrichment.py authorized_businesses.csv enriched.csv --has-email --has-mobile --limit 25
```

The script visits at most the homepage and one linked contact page per row,
respects robots.txt, refuses local/private hosts, rate-limits requests, and
records the source URL. Public emails/phones/social links are best-effort
extractions, not verified ownership or consent for outreach. `--has-email`
filters rows with an actual extracted or supplied email; `--has-mobile` checks
UAE mobile number format. `--whatsapp-possible` uses the same format check and
**does not verify** an active WhatsApp account. A missing company website often
means no email can be found. Filtering may produce an empty file with headers.

For missing website URLs, optional official search discovery needs **both**
`SERPAPI_API_KEY` and `TYPESAFE_API_KEY` in local environment variables.
SerpApi Google Search provides candidates; TypeSafe judges whether a single candidate
matches the named company and area. An ambiguous answer leaves the site blank.
Neither service is used without its key; the script does not guess domains or
scrape a search-results page. Search/API calls may incur fees; set your own
limits/budgets before enabling keys. The `--limit` argument caps this run to
1-100 rows (default 25). SerpApi Free currently allows 250 successful searches per month. Check your
account limits before each run and review SerpApi terms for result use. Keep keys out of the input CSV and version control.

Sites requiring JavaScript can optionally use `--playwright` after installing
`playwright` and Chromium (`pip install playwright; playwright install chromium`).
This loads only the target site's document, not images/scripts/subresources,
so some JavaScript-rendered contact details will not appear; use the default
HTTP mode first. The script will not bypass access blocks. No email is supplied
by Google Places. Do not call a number "WhatsApp verified" based on its shape.

Synthetic unit tests (no paid API calls or live website fetches):

```bash
python -m unittest -v test_lead_enrichment.py
```

## Free-text search of your local lead CSV

After importing or enriching an export-authorized CSV, search the data by
company name, location, business type, or category in one query. Terms can
match across separate columns, case-insensitively; put quotes around a phrase.
This is **local filtering**, not a new web/Google Places search or discovery
of businesses absent from the CSV.

```bash
python lead_search.py enriched.csv 'Dubai cafe' --output-csv dubai-cafes.csv
python -m unittest -v test_lead_search.py
```

Recognized headers include `Company Name`, `Location`, `Area`, `City`, `Emirate`,
`Address`, `Business Type`, `Business Category`, `Category`, `Categories`,
`Keywords`, and `Description`. Other fields are preserved in output but not
searched (for example, private contact information). The original Streamlit
app's "Additional Keywords" box already feeds the existing Places search and
is unchanged; this new feature searches the data you supply locally.

### Local CSV filters

The Streamlit local CSV panel also offers category/type, emirate/city and
area/location selections drawn from the uploaded file; company-name contains;
website, phone, email and UAE mobile presence; and optional rating/review
bounds. The fields must exist in the CSV: absent ratings and review counts do
not pass active numeric bounds. Mobile/WhatsApp-possible checks only supplied
fields or the number format, never an active WhatsApp account. These controls
filter only the uploaded CSV, not the Google Places query or its export.

The Places query's Business Categories menu has a broader list of common UAE
business phrases. It is a set of suggestions, not an exhaustive Google Places
type list. Enter any missing category in the separate "Other business
categories" field, comma-separated. Each phrase is used as a search query;
this does not change the existing Places export behavior or its data rights.
