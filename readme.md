# E-CAB Member Data Scraper

A Python script to collect and organize member data from the e-CAB (e-Commerce Association of Bangladesh) website. This tool scrapes member information, including company profiles and business activities, and organizes the data into Excel files both by category and as a complete dataset.

## Features

-   Scrapes member data from the e-CAB website API
-   Collects detailed company profiles for each member
-   Organizes data by business activity categories
-   Handles pagination automatically
-   Implements polite scraping with random delays
-   Saves data in both consolidated and category-specific Excel files
-   Includes fallback to CSV format if Excel export fails
-   Cleans and formats data for Excel compatibility

## Prerequisites

```python
pip install requests pandas openpyxl
```

## Configuration

The script uses the following configuration constants:

```python
BASE_URL = "https://e-cab.net"
API_ENDPOINT = f"{BASE_URL}/get-member-list"
PROFILE_ENDPOINT = f"{BASE_URL}/get-company-profile"
```

## Data Fields

The scraper collects the following information for each member:

-   Company Name
-   Company Logo URL
-   Membership Number
-   Membership Type
-   Member Category
-   Establishment Date
-   Website URL
-   Office Address
-   Postal Code
-   Phone Number
-   Email Address
-   Legal Structure
-   TIN Number
-   Trade License Number
-   License Validity
-   Business Activities

## Usage

1. Clone the repository
2. Install the required dependencies
3. Run the script:

```bash
python scraper.py
```

## Output

The script generates two types of output:

1. **Complete Dataset**: `all_members.xlsx` containing all member data
2. **Category-specific Files**: Individual Excel files for each business activity category

## Error Handling

-   Implements robust error handling for API requests
-   Automatically falls back to CSV format if Excel export fails
-   Logs errors during the scraping process

## Rate Limiting

The script implements polite scraping practices:

-   Random delays between requests (1-2 seconds for profile requests)
-   Random delays between pages (1-3 seconds)

## Contributing

Feel free to fork this repository and submit pull requests for any improvements.

## License

This project is open-source and available under the MIT License.

## Disclaimer

Please ensure you have permission to scrape data from e-CAB's website and comply with their terms of service and robots.txt file. This script is for educational purposes only.
