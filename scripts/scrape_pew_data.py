"""
Script to scrape US media headlines from the Pew Research Center's Project for Excellence in Journalism (PEJ)
News Coverage Index for the period of July 1, 2011 to September 30, 2011.

This script uses the Wayback Machine to access archived versions of the PEJ News Index reports.
"""

import os
import re
import json
import csv
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "pew")
START_DATE = datetime(2011, 7, 1)
END_DATE = datetime(2011, 9, 30)
WAYBACK_BASE_URL = "https://web.archive.org/web/"
PEJ_NEWS_INDEX_URL = "http://www.journalism.org/news_index"

def ensure_dir_exists(directory):
    """Ensure the output directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_wayback_snapshots(url, start_date, end_date):
    """Get Wayback Machine snapshots for a URL within a date range."""
    start_timestamp = start_date.strftime("%Y%m%d")
    end_timestamp = end_date.strftime("%Y%m%d")
    
    cdx_url = f"https://web.archive.org/cdx/search/cdx?url={url}&from={start_timestamp}&to={end_timestamp}&output=json"
    
    try:
        response = requests.get(cdx_url)
        response.raise_for_status()
        snapshots = response.json()
        
        if snapshots and len(snapshots) > 0:
            snapshots = snapshots[1:]
        
        return snapshots
    except Exception as e:
        print(f"Error fetching Wayback snapshots: {e}")
        return []

def get_wayback_page(timestamp, url):
    """Get the content of a page from the Wayback Machine."""
    wayback_url = f"{WAYBACK_BASE_URL}{timestamp}/{url}"
    
    try:
        response = requests.get(wayback_url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching Wayback page: {e}")
        return None

def parse_news_index_page(html):
    """Parse the PEJ News Index page to extract report links."""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    reports = []
    
    for link in soup.find_all('a', href=True):
        text = link.get_text()
        if "PEJ News Coverage Index" in text and "2011" in text:
            date_match = re.search(r'(\w+ \d+-\d+, 2011)', text)
            if date_match:
                date_range = date_match.group(1)
                reports.append({
                    'title': text,
                    'url': link['href'],
                    'date_range': date_range
                })
    
    return reports

def parse_report_page(html):
    """Parse a PEJ News Coverage Index report page to extract headlines and data."""
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.find('h1')
    title_text = title.get_text() if title else "Unknown Report"
    
    date_posted = None
    date_element = soup.find(text=re.compile(r'Date Posted:'))
    if date_element:
        date_match = re.search(r'Date Posted: (\w+ \d+, 2011)', date_element)
        if date_match:
            date_posted = date_match.group(1)
    
    stories = []
    content_div = soup.find('div', class_='content')
    
    if content_div:
        paragraphs = content_div.find_all('p')
        
        for p in paragraphs:
            text = p.get_text().strip()
            if "top story" in text.lower() or "coverage" in text.lower() or "news agenda" in text.lower():
                stories.append(text)
    
    return {
        'title': title_text,
        'date_posted': date_posted,
        'stories': stories
    }

def save_data(data, filename):
    """Save the collected data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_csv(data, filename):
    """Save the collected data to a CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Report Title', 'Date Posted', 'Story'])
        
        for report in data:
            title = report.get('title', 'Unknown')
            date_posted = report.get('date_posted', 'Unknown')
            
            for story in report.get('stories', []):
                writer.writerow([title, date_posted, story])

def main():
    """Main function to scrape PEJ News Index data."""
    ensure_dir_exists(OUTPUT_DIR)
    
    print(f"Fetching Wayback Machine snapshots for PEJ News Index from {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}...")
    
    snapshots = get_wayback_snapshots(PEJ_NEWS_INDEX_URL, START_DATE, END_DATE)
    
    if not snapshots:
        print("No snapshots found for the specified date range.")
        return
    
    print(f"Found {len(snapshots)} snapshots. Processing...")
    
    all_reports = []
    processed_urls = set()
    
    for snapshot in snapshots:
        timestamp = snapshot[1]
        print(f"Processing snapshot from {timestamp}...")
        
        html = get_wayback_page(timestamp, PEJ_NEWS_INDEX_URL)
        
        reports = parse_news_index_page(html)
        
        for report in reports:
            if report['url'] not in processed_urls:
                processed_urls.add(report['url'])
                
                print(f"Processing report: {report['title']}...")
                
                report_html = get_wayback_page(timestamp, report['url'])
                
                report_data = parse_report_page(report_html)
                
                if report_data:
                    all_reports.append(report_data)
                
                time.sleep(1)
    
    if all_reports:
        json_filename = os.path.join(OUTPUT_DIR, "pew_news_coverage_index_2011.json")
        csv_filename = os.path.join(OUTPUT_DIR, "pew_news_coverage_index_2011.csv")
        
        save_data(all_reports, json_filename)
        save_csv(all_reports, csv_filename)
        
        print(f"Data saved to {json_filename} and {csv_filename}")
    else:
        print("No report data collected.")

if __name__ == "__main__":
    main()
