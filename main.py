import requests
import pandas as pd
import time
import random
import os
import re

# Base URL for constructing absolute links
BASE_URL = "https://e-cab.net"
API_ENDPOINT = f"{BASE_URL}/get-member-list"

# Headers to simulate a browser visit
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def clean_text_for_excel(text):
    """
    Clean text to remove or replace characters that Excel can't handle.
    """
    if not isinstance(text, str):
        return text

    # Replace problematic characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # Replace other potentially problematic characters
    text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    return text


def create_data_directory():
    """
    Create a directory for storing the scraped data if it doesn't exist.
    """
    directory = "e-cab-data"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def get_paginated_data(page=1):
    """
    Retrieves member data from the API with pagination and category filter.
    Returns the JSON response containing member data and pagination metadata.
    """
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


def process_member_data(member):
    """
    Processes a single member's data and returns a formatted dictionary.
    Cleans text fields for Excel compatibility.
    """
    return {
        "Company Name": clean_text_for_excel(member.get("company_name", "N/A")),
        "Logo": clean_text_for_excel(BASE_URL + member.get("company_logo", "") if member.get("company_logo") else "N/A"),
        "Membership No": clean_text_for_excel(member.get("membership_no", "N/A")),
        "Membership Type": clean_text_for_excel(member.get("membership_type", "N/A")),
        "Member Category": clean_text_for_excel(member.get("member_category", "N/A")),
        "Short Profile": clean_text_for_excel(member.get("short_profile", "N/A")),
        "Establishment": clean_text_for_excel(
            f"{member.get('establishment_month', 'N/A')} {member.get('establishment_year', 'N/A')}"
        ),
        "Website URL": clean_text_for_excel(member.get("FullUrl", "N/A"))
    }


def generate_html_display(members_data):
    """
    Generates HTML content similar to the member-list page format.
    """
    html_content = """
    <html>
    <head>
        <style>
            .member-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                padding: 20px;
            }
            .member-card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            }
            .member-logo {
                max-width: 150px;
                height: auto;
                margin: 0 auto 15px;
            }
            .member-info {
                margin-top: 10px;
            }
            .member-name {
                font-weight: bold;
                font-size: 1.1em;
                margin-bottom: 8px;
            }
        </style>
    </head>
    <body>
        <div class="member-grid">
    """

    for member in members_data:
        html_content += f"""
            <div class="member-card">
                <img src="{member['Logo']}" alt="{member['Company Name']}" class="member-logo">
                <div class="member-info">
                    <div class="member-name">{member['Company Name']}</div>
                    <div>Member No: {member['Membership No']}</div>
                    <div>Category: {member['Member Category']}</div>
                    <div>Established: {member['Establishment']}</div>
                </div>
            </div>
        """

    html_content += """
        </div>
    </body>
    </html>
    """
    return html_content


def save_data(df, html_content, data_dir):
    """
    Save data to Excel and HTML files with error handling.
    """
    try:
        # Save Excel file
        excel_path = os.path.join(data_dir, "e_cab_members.xlsx")
        df.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"Excel file saved successfully: {excel_path}")

        # Save HTML file
        html_path = os.path.join(data_dir, "member_list.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML file saved successfully: {html_path}")

    except Exception as e:
        print(f"Error saving files: {str(e)}")

        # Fallback to CSV if Excel fails
        csv_path = os.path.join(data_dir, "e_cab_members.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"Saved data as CSV instead: {csv_path}")


def main():
    print("Starting the data collection process...")
    data_dir = create_data_directory()
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
            processed_data = process_member_data(member)
            all_members.append(processed_data)

        meta = response_data.get("meta", {})
        if total_pages is None:
            total_pages = meta.get("last_page")
            print(f"Total pages to process: {total_pages}")

        print(f"Processed {len(members_data)} members from page {current_page}")

        if current_page >= total_pages:
            break

        current_page += 1
        time.sleep(random.uniform(1, 3))

    # Convert to DataFrame
    df = pd.DataFrame(all_members)

    # Generate HTML display
    html_output = generate_html_display(all_members)

    # Save files
    save_data(df, html_output, data_dir)

    print("\nData Collection Summary:")
    print(f"Total members collected: {len(df)}")
    print(f"Total pages processed: {current_page}")
    print(f"\nFiles saved in directory: {data_dir}")


if __name__ == "__main__":
    main()
