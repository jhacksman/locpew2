"""
Script to scrape US media headlines from the Library of Congress for the period of 
July 1, 2011 to September 30, 2011.
"""

import os
import json
import csv
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "loc")
START_DATE = datetime(2011, 7, 1)
END_DATE = datetime(2011, 9, 30)
LOC_SEARCH_URL = "https://www.loc.gov/newspapers/"

def ensure_dir_exists(directory):
    """Ensure the output directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def search_loc_newspapers(start_date, end_date):
    """Search for newspapers in the Library of Congress within a date range."""
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    search_url = f"{LOC_SEARCH_URL}?dates={start_date_str}/{end_date_str}&fo=json"
    
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error searching LOC newspapers: {e}")
        return None

def extract_headlines(results):
    """Extract headlines from LOC search results."""
    headlines = []
    
    if not results or 'results' not in results:
        return headlines
    
    for item in results.get('results', []):
        title = item.get('title', '')
        date = item.get('date', '')
        
        if title and date:
            headlines.append({
                'title': title,
                'date': date,
                'source': 'Library of Congress'
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
        writer.writerow(['Title', 'Date', 'Source'])
        
        for headline in data:
            writer.writerow([
                headline.get('title', ''),
                headline.get('date', ''),
                headline.get('source', '')
            ])

def main():
    """Main function to scrape Library of Congress data."""
    ensure_dir_exists(OUTPUT_DIR)
    
    print(f"Searching Library of Congress for newspapers from {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}...")
    
    results = search_loc_newspapers(START_DATE, END_DATE)
    
    if not results:
        print("No results found from the Library of Congress.")
        
        json_filename = os.path.join(OUTPUT_DIR, "loc_newspapers_2011.json")
        csv_filename = os.path.join(OUTPUT_DIR, "loc_newspapers_2011.csv")
        
        save_data([], json_filename)
        save_csv([], csv_filename)
        
        print(f"Empty data files created at {json_filename} and {csv_filename}")
        return
    
    headlines = extract_headlines(results)
    
    if headlines:
        json_filename = os.path.join(OUTPUT_DIR, "loc_newspapers_2011.json")
        csv_filename = os.path.join(OUTPUT_DIR, "loc_newspapers_2011.csv")
        
        save_data(headlines, json_filename)
        save_csv(headlines, csv_filename)
        
        print(f"Data saved to {json_filename} and {csv_filename}")
    else:
        print("No headlines extracted from the search results.")

if __name__ == "__main__":
    main()
