import requests
import pandas as pd
import time
import random
import os
from collections import defaultdict

# Base URL and endpoints
BASE_URL = "https://basis.org.bd"
MEMBER_LIST_ENDPOINT = f"{BASE_URL}/get-member-list"
PROFILE_ENDPOINT = f"{BASE_URL}/get-company-profile"

# Headers to simulate browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def create_directories():
    """Create necessary directories for storing data."""
    base_dir = "basis-data"
    categories_dir = os.path.join(base_dir, "service-categories")

    for directory in [base_dir, categories_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    return base_dir, categories_dir


def clean_text(text):
    """Clean text for Excel compatibility."""
    if not isinstance(text, str):
        return text
    return str(text).replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')


def get_member_list(page=1):
    """Fetch paginated member list."""
    params = {"page": page, "team": ""}
    try:
        response = requests.get(MEMBER_LIST_ENDPOINT, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching member list page {page}: {e}")
        return None


def get_company_profile(membership_no):
    """Fetch detailed company profile."""
    try:
        response = requests.get(f"{PROFILE_ENDPOINT}/{membership_no}", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching profile for {membership_no}: {e}")
        return None


def process_member_data(member_data, detailed_profile):
    """Process and combine member data with detailed profile."""
    base_data = {
        "Company Name": clean_text(member_data.get("company_name", "N/A")),
        "Membership No": clean_text(member_data.get("membership_no", "N/A")),
        "Membership Type": clean_text(member_data.get("membership_type", "N/A")),
        "Establishment": f"{member_data.get('establishment_month', '')} {member_data.get('establishment_year', '')}".strip() or "N/A",
        "Logo URL": BASE_URL + member_data.get("logo", "") if member_data.get("logo") else "N/A",
        "Short Profile": clean_text(member_data.get("short_profile", "N/A")),
        # "Website": clean_text(member_data.get("FullUrl", "N/A"))
    }

    if detailed_profile and 'member' in detailed_profile:
        profile = detailed_profile['member']
        base_data.update({
            "Address": clean_text(profile.get("address", "N/A")),
            "Area": clean_text(profile.get("area", "N/A")),
            "Postcode": profile.get("postcode", "N/A"),
            "Phone": clean_text(profile.get("phone", "N/A")),
            "Email": clean_text(profile.get("email", "N/A")),
            "Company Website": clean_text(profile.get("website", "N/A")),
            "Legal Structure": clean_text(profile.get("legal_structure", "N/A")),
            "Valid Till": clean_text(profile.get("valid_till", "N/A"))
        })

        # Extract services
        services = profile.get("services", [])
        categories = []
        for service in services:
            if service.get("service"):
                categories.append(service["service"])

        base_data["Services"] = ", ".join(categories) if categories else "N/A"
        return base_data, categories

    return base_data, []


def save_to_excel(data, filepath):
    """Save data to Excel file with error handling."""
    try:
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False, engine='openpyxl')
        print(f"Successfully saved: {filepath}")
    except Exception as e:
        print(f"Error saving Excel file {filepath}: {e}")
        # Fallback to CSV
        csv_filepath = filepath.replace('.xlsx', '.csv')
        df.to_csv(csv_filepath, index=False, encoding='utf-8')
        print(f"Saved as CSV instead: {csv_filepath}")


def main():
    print("Starting BASIS member data collection...")
    base_dir, categories_dir = create_directories()

    # Storage for categorized data
    category_data = defaultdict(list)
    all_members = []

    current_page = 1
    total_pages = None

    while True:
        print(f"\nProcessing page {current_page}...")
        response = get_member_list(current_page)

        if not response:
            break

        members = response.get("data", [])
        if not members:
            break

        if total_pages is None:
            total_pages = response.get("meta", {}).get("last_page")
            print(f"Total pages to process: {total_pages}")

        for member in members:
            membership_no = member.get("membership_no")
            print(f"Fetching profile for member: {membership_no}")

            detailed_profile = get_company_profile(membership_no)
            processed_data, categories = process_member_data(member, detailed_profile)

            all_members.append(processed_data)

            # Categorize by services
            if categories:
                for category in categories:
                    category_data[category].append(processed_data)

            # Add delay between requests
            time.sleep(random.uniform(1, 2))

        if current_page >= total_pages:
            break

        current_page += 1
        time.sleep(random.uniform(2, 3))

    # Save complete dataset
    save_to_excel(all_members, os.path.join(base_dir, "all_members.xlsx"))

    # Save category-specific files
    for category, members in category_data.items():
        if members:
            filename = f"{category.replace('/', '_').replace(' ', '_')}.xlsx"
            save_to_excel(members, os.path.join(categories_dir, filename))

    print("\nData Collection Summary:")
    print(f"Total members collected: {len(all_members)}")
    print(f"Total service categories: {len(category_data)}")
    print(f"Data saved in: {base_dir}")
    print(f"Category files saved in: {categories_dir}")


if __name__ == "__main__":
    main()
