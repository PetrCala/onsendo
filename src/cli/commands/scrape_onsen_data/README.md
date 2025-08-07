# Onsen Data Scraper

This module provides functionality to scrape onsen (hot spring) data from the Oita Prefecture onsen hunter website.

## Features

- **Deterministic and Stateful**: The scraper is designed to be deterministic and stateful, meaning it always produces the same outcome and can resume from where it left off.
- **Incremental Scraping**: If a JSON file already exists with scraped data, the scraper will skip already scraped onsens and only scrape new ones.
- **Comprehensive Logging**: All scraping activities are logged to both console and file for debugging and monitoring.
- **Respectful Scraping**: Includes delays between requests to be respectful to the target server.
- **Detailed Data Extraction**: Extracts comprehensive onsen information including names, addresses, coordinates, contact details, and more.
- **Data Mapping**: Automatically maps scraped data to database model fields for easy integration.

## Files

- `__init__.py`: Main scraping command implementation
- `scraper.py`: Core scraping functionality and utilities
- `data_mapper.py`: Data mapping utilities for converting scraped data to database format
- `test_scraper.py`: Test script to verify scraping functionality
- `test_basic.py`: Basic structure and import tests
- `README.md`: This documentation file

## Output Files

The scraper creates two main output files in the `output/` directory:

1. **`onsen_mapping.json`**: Maps onsen IDs to ban numbers
2. **`scraped_onsen_data.json`**: Contains all scraped onsen data with onsen ID as keys
3. **`scraping.log`**: Log file containing all scraping activities

## Data Extraction

The scraper extracts the following data from each onsen page:

### Basic Information

- **Name**: Onsen name from the page header
- **Ban Number**: Extracted from the combined ban number and name field
- **Full Name**: Complete onsen name with ban number

### Location Data

- **Map URL**: Full Google Maps iframe URL
- **Coordinates**: Latitude and longitude extracted from the map URL
- **Address**: Full address from the information table

### Contact & Business Information

- **Phone**: Contact phone number
- **Business Form**: Type of business operation
- **Admission Fee**: Entry fee information
- **Usage Time**: Operating hours
- **Closed Days**: Days when the onsen is closed

### Facilities & Services

- **Private Bath**: Information about private/family baths
- **Spring Quality**: Type and quality of the hot spring water
- **Nearest Bus Stop**: Closest bus stop information
- **Nearest Station**: Closest train station with walking distance
- **Parking**: Parking availability and information

### Additional Information

- **Remarks**: Additional notes and information
- **Region**: Automatically extracted from address or name

## Usage

### Command Line

```bash
# Run the scraping command
python -m src.cli scrape-onsen-data
```

### Programmatic Usage

```python
from src.cli.commands.scrape_onsen_data import scrape_onsen_data
import argparse

args = argparse.Namespace()
scrape_onsen_data(args)
```

## Scraping Process

1. **Extract Onsen Mapping**: Scrapes the main onsen list page to extract onsen ID to ban number mappings
2. **Load Existing Data**: Checks for existing scraped data to enable incremental scraping
3. **Scrape Individual Onsens**: For each onsen not already scraped, fetches the individual onsen page
4. **Extract Detailed Data**: Uses XPath selectors to extract comprehensive onsen information
5. **Map to Database Format**: Converts scraped data to database model format
6. **Save Progress**: Saves data after each onsen to ensure no data loss
7. **Logging**: Provides detailed logging of all activities

## Data Structure

Each scraped onsen entry contains:

```json
{
  "onsen_id": "123",
  "url": "https://...",
  "raw_html": "...",
  "extracted_data": {
    "name": "温泉名",
    "ban_number_and_name": "123 温泉名",
    "latitude": 33.123,
    "longitude": 131.456,
    "map_url": "https://maps.google.co.jp/...",
    "住所": "大分県別府市...",
    "電話": "0977-12-3456",
    // ... other table data
  },
  "mapped_data": {
    "name": "温泉名",
    "ban_number": "123",
    "address": "大分県別府市...",
    "phone": "0977-12-3456",
    "latitude": 33.123,
    "longitude": 131.456,
    // ... mapped to database fields
  },
  "mapping_summary": {
    "total_fields": 15,
    "filled_fields": 12,
    "required_fields_present": true,
    "has_coordinates": true,
    "table_entries_mapped": 8
  }
}
```

## Dependencies

- `selenium`: For web scraping with JavaScript support
- `beautifulsoup4`: For HTML parsing
- `requests`: For HTTP requests
- `logging`: For comprehensive logging

## Configuration

The scraper uses constants defined in `src.const.CONST`:

- `ONSEN_URL`: Main onsen list page URL
- `ONSEN_DETAIL_URL_TEMPLATE`: Template for individual onsen detail pages

## Testing

Run the basic test script to verify the scraping functionality:

```bash
python src/cli/commands/scrape_onsen_data/test_basic.py
```

## Notes

- The scraper uses Selenium with Chrome in headless mode for better JavaScript handling
- Includes a 1-second delay between requests to be respectful to the server
- All data is saved in UTF-8 encoding to properly handle Japanese text
- The scraper is designed to handle the complex div structure of the target website
- Data mapping automatically converts Japanese field names to English database field names
- Coordinates are extracted from Google Maps iframe URLs
- Region information is automatically extracted from addresses or names

## Database Integration

The scraped data is automatically mapped to the Onsen database model fields:

- Basic information (name, ban_number, region)
- Location data (latitude, longitude, address)
- Contact information (phone)
- Business details (business_form, admission_fee, usage_time, closed_days)
- Facility information (private_bath, spring_quality, parking)
- Transportation (nearest_bus_stop, nearest_station)
- Additional notes (remarks, description)

The mapped data is ready for direct insertion into the database using SQLAlchemy models.
