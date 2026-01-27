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
