import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
from datetime import datetime


def create_data_directory():
    """Create directory for storing scraped data"""
    base_dir = "bacco-data"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    return base_dir


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
            # Update company name from h5 if available
            name_tag = body.find('h5')
            if name_tag:
                member['Company Name'] = clean_text_for_excel(name_tag.text.strip())

            # Get phone and email
            paragraphs = body.find_all('p')
            for p in paragraphs:
                text = p.text.strip()
                if text.startswith('Phone :'):
                    member['Phone'] = clean_text_for_excel(text.replace('Phone :', '').strip())
                elif text.startswith('Email :'):
                    member['Email'] = clean_text_for_excel(text.replace('Email :', '').strip())

            # Get website
            website_link = body.find('a', target='_blank')
            if website_link:
                member['Website'] = clean_text_for_excel(website_link.text.strip())

            # Get details URL
            details_link = body.find('a', class_='btn btn-bacco-2')
            if details_link:
                member['Details URL'] = clean_text_for_excel(details_link['href'])

        members_data.append(member)

    return members_data


def save_data(data, base_dir):
    """Save data to Excel file with CSV fallback"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = os.path.join(base_dir, f"bacco_members_{timestamp}.xlsx")
    csv_filename = os.path.join(base_dir, f"bacco_members_{timestamp}.csv")

    df = pd.DataFrame(data)

    try:
        # Try saving as Excel first
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        print(f"Data successfully saved to Excel: {excel_filename}")
        return excel_filename
    except Exception as e:
        print(f"Error saving to Excel: {e}")
        try:
            # Fallback to CSV
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"Data saved as CSV instead: {csv_filename}")
            return csv_filename
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            return None


def main():
    print("Starting the data collection process...")
    base_dir = create_data_directory()
    base_url = "https://www.bacco.org.bd/member-list"
    all_members = []
    page = 1

    while True:
        print(f"Fetching page {page}...")
        url = f"{base_url}?page={page}"
        html = get_page_content(url)

        if not html:
            break

        members = parse_member_data(html)
        if not members:
            break

        all_members.extend(members)
        print(f"Processed {len(members)} members from page {page}")

        # Add random delay between requests
        time.sleep(random.uniform(1, 3))
        page += 1

    if all_members:
        print(f"\nTotal members collected: {len(all_members)}")
        saved_file = save_data(all_members, base_dir)
        if saved_file:
            print("\nData Collection Summary:")
            print(f"Total members: {len(all_members)}")
            print(f"Data saved to: {saved_file}")
    else:
        print("No data was collected.")


if __name__ == "__main__":
    main()
