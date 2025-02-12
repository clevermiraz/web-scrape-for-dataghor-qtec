import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
from datetime import datetime
from collections import defaultdict

# Define business focus categories
BUSINESS_CATEGORIES = {
    "1": "Voice Services",
    "2": "Data",
    "3": "IT Support",
    "4": "CMS Support",
    "5": "Digital Marketing",
    "6": "Graphic Design",
    "7": "Accounting BPO",
    "8": "Back office Support",
    "9": "Website Design & Development",
    "10": "Skill Development & IT Training",
    "11": "Software Development",
    "12": "Software Maintenance",
    "13": "Legal Outsourcing",
    "14": "HR Outsourcing",
    "15": "Cloud Service Management",
    "16": "AI Solutions",
    "17": "Knowledge Process Outsourcing",
    "18": "Research & Consultancy",
    "19": "E-Commerce"
}


def create_data_directory():
    """Create directories for storing scraped data"""
    base_dir = "bacco-data"
    categories_dir = os.path.join(base_dir, "categories")
    for directory in [base_dir, categories_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    return base_dir, categories_dir


def clean_text_for_excel(text):
    """Clean text to remove problematic characters for Excel"""
    if not isinstance(text, str):
        return text
    return str(text).replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')


def get_page_content(url):
    """Fetch the page content with error handling and retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Error fetching {url}: {e}")
                return None
            time.sleep(random.uniform(1, 2))


def parse_member_data(html):
    """Parse the HTML content and extract member information"""
    soup = BeautifulSoup(html, 'html.parser')
    members_data = []

    member_blocks = soup.find_all('div', class_='media mt-5 member-list-img')

    for block in member_blocks:
        member = {}

        # Get logo URL and company name
        logo_img = block.find('img', class_='mr-3')
        if logo_img:
            member['Company Name'] = clean_text_for_excel(logo_img.get('alt', 'N/A'))
            member['Logo'] = clean_text_for_excel(logo_img.get('src', 'N/A'))

        body = block.find('div', class_='media-body member-body')
        if body:
            name_tag = body.find('h5')
            if name_tag:
                member['Company Name'] = clean_text_for_excel(name_tag.text.strip())

            paragraphs = body.find_all('p')
            for p in paragraphs:
                text = p.text.strip()
                if text.startswith('Phone :'):
                    member['Phone'] = clean_text_for_excel(text.replace('Phone :', '').strip())
                elif text.startswith('Email :'):
                    member['Email'] = clean_text_for_excel(text.replace('Email :', '').strip())

            website_link = body.find('a', target='_blank')
            if website_link:
                member['Website'] = clean_text_for_excel(website_link.text.strip())

            details_link = body.find('a', class_='btn btn-bacco-2')
            if details_link:
                member['Details URL'] = clean_text_for_excel(details_link['href'])

        members_data.append(member)

    return members_data


def save_data(data, filename):
    """Save data to Excel file with CSV fallback"""
    try:
        # Try saving as Excel first
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"Data successfully saved to Excel: {filename}")
        return True
    except Exception as e:
        print(f"Error saving to Excel: {e}")
        try:
            # Fallback to CSV
            csv_filename = filename.replace('.xlsx', '.csv')
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"Data saved as CSV instead: {csv_filename}")
            return True
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            return False


def scrape_category(category_id, category_name, base_dir, categories_dir):
    """Scrape members for a specific business focus category"""
    print(f"\nScraping category: {category_name}")
    members = []
    page = 1

    while True:
        url = f"https://www.bacco.org.bd/member-list?business_foc%5B%5D={category_id}&page={page}"
        print(f"Fetching page {page}...")

        html = get_page_content(url)
        if not html:
            break

        page_members = parse_member_data(html)
        if not page_members:
            break

        for member in page_members:
            member['Business Category'] = category_name

        members.extend(page_members)
        print(f"Found {len(page_members)} members on page {page}")

        # Add random delay between requests
        time.sleep(random.uniform(1, 3))
        page += 1

    if members:
        # Save category-specific file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        category_filename = os.path.join(categories_dir, f"{category_name.lower().replace(' ', '_')}_{timestamp}.xlsx")
        save_data(members, category_filename)

    return members


def main():
    print("Starting the data collection process...")
    base_dir, categories_dir = create_data_directory()

    all_members = []

    # Scrape each category
    for category_id, category_name in BUSINESS_CATEGORIES.items():
        category_members = scrape_category(category_id, category_name, base_dir, categories_dir)
        all_members.extend(category_members)

    if all_members:
        # Save complete dataset
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        complete_filename = os.path.join(base_dir, f"all_members_{timestamp}.xlsx")
        save_data(all_members, complete_filename)

        print("\nData Collection Summary:")
        print(f"Total members collected: {len(all_members)}")
        print(f"Categories processed: {len(BUSINESS_CATEGORIES)}")
        print(f"Complete data saved to: {base_dir}")
        print(f"Category-specific data saved to: {categories_dir}")

        # Print members per category
        category_counts = defaultdict(int)
        for member in all_members:
            category_counts[member['Business Category']] += 1

        print("\nMembers per category:")
        for category, count in category_counts.items():
            print(f"- {category}: {count} members")
    else:
        print("No data was collected.")


if __name__ == "__main__":
    main()
