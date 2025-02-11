import requests
import pandas as pd
import time
import random
import os
from collections import defaultdict

# Base URL for constructing absolute links
BASE_URL = "https://e-cab.net"
API_ENDPOINT = f"{BASE_URL}/get-member-list"
PROFILE_ENDPOINT = f"{BASE_URL}/get-company-profile"

# Headers to simulate a browser visit
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def clean_text_for_excel(text):
    """Clean text to remove or replace characters that Excel can't handle."""
    if not isinstance(text, str):
        return text
    text = str(text).replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    return text


def create_data_directory():
    """Create directories for storing the scraped data."""
    base_dir = "e-cab-data"
    categories_dir = os.path.join(base_dir, "categories")

    for directory in [base_dir, categories_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    return base_dir, categories_dir


def get_paginated_data(page=1):
    """Retrieve member data from the API with pagination."""
    params = {
        "page": page,
        "member_category": "General",
        "team": ""
    }
    try:
        response = requests.get(API_ENDPOINT, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching page {page}: {e}")
        return None


def get_company_profile(membership_no):
    """Fetch detailed company profile."""
    try:
        url = f"{PROFILE_ENDPOINT}/{membership_no}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching profile for member {membership_no}: {e}")
        return None


def process_member_data(member, detailed_profile=None):
    """Process member data including detailed profile information."""
    base_data = {
        "Company Name": clean_text_for_excel(member.get("company_name", "N/A")),
        "Logo": clean_text_for_excel(BASE_URL + member.get("company_logo", "") if member.get("company_logo") else "N/A"),
        "Membership No": clean_text_for_excel(member.get("membership_no", "N/A")),
        "Membership Type": clean_text_for_excel(member.get("membership_type", "N/A")),
        "Member Category": clean_text_for_excel(member.get("member_category", "N/A")),
        "Establishment": f"{member.get('establishment_month', 'N/A')} {member.get('establishment_year', 'N/A')}",
        "Website URL": clean_text_for_excel(member.get("FullUrl", "N/A"))
    }

    if detailed_profile and 'member' in detailed_profile:
        profile = detailed_profile['member']
        base_data.update({
            "Office Address": clean_text_for_excel(profile.get("current_office_address", "N/A")),
            "Postal Code": profile.get("current_office_postal_code", "N/A"),
            "Phone": clean_text_for_excel(profile.get("work_phone", "N/A")),
            "Email": clean_text_for_excel(
                profile.get("emails", [{}])
                if isinstance(profile.get("emails", []), list) and profile.get("emails", [])
                else [{}]
            )[0].get("email", "N/A"),
            # "Website": clean_text_for_excel(profile.get("website", "N/A")),
            "Legal Structure": clean_text_for_excel(profile.get("legal_structure", "N/A")),
            "TIN Number": clean_text_for_excel(profile.get("tin_number", "N/A")),
            "Trade License No": clean_text_for_excel(profile.get("trade_license_no", "N/A")),
            "Valid Till": clean_text_for_excel(profile.get("valid_till", "N/A")),
            "Business Activities": ", ".join([activity["activity"] for activity in profile.get("business_activity", [])])
        })

    return base_data, profile.get("business_activity", []) if detailed_profile and 'member' in detailed_profile else []


def save_category_data(category_data, categories_dir):
    """Save data to separate Excel files based on business activities."""
    for category, members in category_data.items():
        if members:
            filename = f"{category.replace('/', '_').replace(' ', '_')}.xlsx"
            filepath = os.path.join(categories_dir, filename)
            df = pd.DataFrame(members)
            try:
                df.to_excel(filepath, index=False, engine='openpyxl')
                print(f"Saved category file: {filename} with {len(members)} members")
            except Exception as e:
                print(f"Error saving {filename}: {e}")
                # Fallback to CSV if Excel fails
                csv_filepath = filepath.replace('.xlsx', '.csv')
                df.to_csv(csv_filepath, index=False, encoding='utf-8')
                print(f"Saved as CSV instead: {csv_filepath}")


def main():
    print("Starting the data collection process...")
    base_dir, categories_dir = create_data_directory()

    # Dictionary to store members by category
    category_data = defaultdict(list)
    all_members = []
    current_page = 1
    total_pages = None

    while True:
        print(f"Fetching page {current_page}...")
        response_data = get_paginated_data(current_page)

        if not response_data:
            print(f"Failed to fetch page {current_page}")
            break

        members_data = response_data.get("data", [])
        for member in members_data:
            membership_no = member.get("membership_no")

            # Fetch detailed profile
            print(f"Fetching detailed profile for member {membership_no}...")
            detailed_profile = get_company_profile(membership_no)

            # Process member data
            processed_data, business_activities = process_member_data(member, detailed_profile)
            all_members.append(processed_data)

            # Categorize member by business activities
            if business_activities:
                for activity in business_activities:
                    category_name = activity["activity"]
                    category_data[category_name].append(processed_data)

            # Add delay between requests
            time.sleep(random.uniform(1, 2))

        meta = response_data.get("meta", {})
        if total_pages is None:
            total_pages = meta.get("last_page")
            print(f"Total pages to process: {total_pages}")

        print(f"Processed {len(members_data)} members from page {current_page}")

        if current_page >= total_pages:
            break

        current_page += 1
        time.sleep(random.uniform(1, 3))

    # Save complete data
    complete_df = pd.DataFrame(all_members)
    complete_file = os.path.join(base_dir, "all_members.xlsx")
    try:
        complete_df.to_excel(complete_file, index=False)
        print(f"Saved complete data to: {complete_file}")
    except Exception as e:
        print(f"Error saving complete data: {e}")
        complete_df.to_csv(complete_file.replace('.xlsx', '.csv'), index=False)

    # Save category-specific files
    save_category_data(category_data, categories_dir)

    print("\nData Collection Summary:")
    print(f"Total members collected: {len(all_members)}")
    print(f"Total categories found: {len(category_data)}")
    print("Files saved in directories:")
    print(f"- Complete data: {base_dir}")
    print(f"- Category-specific data: {categories_dir}")


if __name__ == "__main__":
    main()
