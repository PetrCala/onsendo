# Onsen Data Scraper

This module provides functionality to scrape onsen (hot spring) data from the Oita Prefecture onsen hunter website.

## Features

- **Deterministic and Stateful**: The scraper is designed to be deterministic and stateful, meaning it always produces the same outcome and can resume from where it left off.
- **Incremental Scraping**: If a JSON file already exists with scraped data, the scraper will skip already scraped onsens and only scrape new ones.
- **Comprehensive Logging**: All scraping activities are logged to both console and file for debugging and monitoring.
- **Respectful Scraping**: Includes delays between requests to be respectful to the target server.

## Files

- `__init__.py`: Main scraping command implementation
- `scraper.py`: Core scraping functionality and utilities
- `test_scraper.py`: Test script to verify scraping functionality
- `README.md`: This documentation file

## Output Files

The scraper creates two main output files in the `output/` directory:

1. **`onsen_mapping.json`**: Maps onsen IDs to ban numbers
2. **`scraped_onsen_data.json`**: Contains all scraped onsen data with onsen ID as keys
3. **`scraping.log`**: Log file containing all scraping activities

## Usage

### Command Line

```bash
# Run the scraping command
python -m src.cli scrape_onsen_data
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
4. **Save Progress**: Saves data after each onsen to ensure no data loss
5. **Logging**: Provides detailed logging of all activities

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

Run the test script to verify the scraping functionality:

```bash
python src/cli/commands/scrape_onsen_data/test_scraper.py
```

## Notes

- The scraper uses Selenium with Chrome in headless mode for better JavaScript handling
- Includes a 1-second delay between requests to be respectful to the server
- All data is saved in UTF-8 encoding to properly handle Japanese text
- The scraper is designed to handle the complex div structure of the target website

## Future Enhancements

The individual onsen page scraping currently includes placeholder fields for specific data extraction. Once you provide the specific XPath selectors for onsen details, the `scrape_onsen_page_with_selenium` function can be updated to extract:

- Onsen name
- Address
- Description
- Other specific fields as needed
