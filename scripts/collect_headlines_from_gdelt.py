"""
Script to collect US media headlines from July 1, 2011 to September 30, 2011
using the GDELT Project's Global Database of Events, Language, and Tone.
"""

import os
import csv
import json
import requests
from datetime import datetime, timedelta
import time

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "gdelt")
START_DATE = datetime(2011, 7, 1)
END_DATE = datetime(2011, 9, 30)
GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

def ensure_dir_exists(directory):
    """Ensure the output directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def format_date(date):
    """Format date for GDELT API."""
    return date.strftime("%Y%m%d%H%M%S")

def get_headlines_for_date(date):
    """Get headlines for a specific date from GDELT."""
    start_time = format_date(date)
    end_time = format_date(date + timedelta(days=1))
    
    params = {
        'query': 'sourcecountry:USA',
        'format': 'json',
        'startdatetime': start_time,
        'enddatetime': end_time,
        'maxrecords': 250,
        'sort': 'DateDesc'
    }
    
    try:
        response = requests.get(GDELT_BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching headlines for {date.strftime('%Y-%m-%d')}: {e}")
        return None

def extract_headlines(data):
    """Extract headlines from GDELT API response."""
    headlines = []
    
    if not data or 'articles' not in data:
        return headlines
    
    for article in data.get('articles', []):
        headline = article.get('title', '')
        source = article.get('sourcename', '')
        url = article.get('url', '')
        date = article.get('seendate', '')
        
        if headline and source:
            headlines.append({
                'headline': headline,
                'source': source,
                'url': url,
                'date': date
            })
    
    return headlines

def save_data(data, filename):
    """Save the collected data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_csv(data, filename):
    """Save the collected data to a CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Headline', 'Source', 'URL', 'Date'])
        
        for headline in data:
            writer.writerow([
                headline.get('headline', ''),
                headline.get('source', ''),
                headline.get('url', ''),
                headline.get('date', '')
            ])

def main():
    """Main function to collect headlines from GDELT."""
    ensure_dir_exists(OUTPUT_DIR)
    
    print(f"Collecting US media headlines from {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}...")
    
    all_headlines = []
    current_date = START_DATE
    
    while current_date <= END_DATE:
        print(f"Processing date: {current_date.strftime('%Y-%m-%d')}...")
        
        data = get_headlines_for_date(current_date)
        
        if data:
            headlines = extract_headlines(data)
            all_headlines.extend(headlines)
            
            print(f"Found {len(headlines)} headlines for {current_date.strftime('%Y-%m-%d')}")
        
        current_date += timedelta(days=1)
        
        time.sleep(1)
    
    if all_headlines:
        json_filename = os.path.join(OUTPUT_DIR, "us_media_headlines_2011.json")
        csv_filename = os.path.join(OUTPUT_DIR, "us_media_headlines_2011.csv")
        
        save_data(all_headlines, json_filename)
        save_csv(all_headlines, csv_filename)
        
        print(f"Data saved to {json_filename} and {csv_filename}")
        print(f"Total headlines collected: {len(all_headlines)}")
    else:
        print("No headlines collected.")

if __name__ == "__main__":
    main()
