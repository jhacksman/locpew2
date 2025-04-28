"""
Script to scrape US media headlines from the Pew Research Center's Project for Excellence in Journalism (PEJ)
News Coverage Index for the period of July 1, 2011 to September 30, 2011 directly from the Wayback Machine.
"""

import os
import re
import json
import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "pew")
WAYBACK_URL = "https://web.archive.org/web/20110717024210/http://www.journalism.org/news_index"

def ensure_dir_exists(directory):
    """Ensure the output directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_page_content(url):
    """Get the content of a webpage."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def extract_report_links(html):
    """Extract links to PEJ News Coverage Index reports from the HTML."""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    reports = []
    
    for a_tag in soup.find_all('a'):
        text = a_tag.get_text()
        if "PEJ News Coverage Index" in text and "2011" in text:
            href = a_tag.get('href')
            if href:
                date_range_match = re.search(r'(\w+ \d+-\d+, 2011)', text)
                date_range = date_range_match.group(1) if date_range_match else "Unknown"
                
                if href.startswith('http'):
                    url = href
                else:
                    base_url = "https://web.archive.org/web/20110717024210/http://www.journalism.org"
                    url = f"{base_url}{href}" if href.startswith('/') else f"{base_url}/{href}"
                
                reports.append({
                    'title': text,
                    'url': url,
                    'date_range': date_range
                })
    
    return reports

def extract_report_content(html, report_title):
    """Extract content from a PEJ News Coverage Index report."""
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    date_posted = None
    date_element = soup.find(string=re.compile(r'Date Posted:'))
    if date_element:
        date_match = re.search(r'Date Posted: (\w+ \d+, 2011)', str(date_element))
        if date_match:
            date_posted = date_match.group(1)
    
    content_div = soup.find('div', class_='content')
    if not content_div:
        content_div = soup.find('div', id='content')
    
    if not content_div:
        for div in soup.find_all('div'):
            if div.find('h1') or div.find('h2'):
                content_div = div
                break
    
    if not content_div:
        return {
            'title': report_title,
            'date_posted': date_posted,
            'content': '',
            'top_stories': []
        }
    
    content = content_div.get_text()
    
    top_stories = []
    paragraphs = content_div.find_all('p')
    
    for p in paragraphs:
        text = p.get_text().strip()
        if any(keyword in text.lower() for keyword in ['top story', 'top stories', 'news agenda', 'coverage']):
            top_stories.append(text)
    
    return {
        'title': report_title,
        'date_posted': date_posted,
        'content': content,
        'top_stories': top_stories
    }

def save_data(data, filename):
    """Save the collected data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_csv(data, filename):
    """Save the collected data to a CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Report Title', 'Date Posted', 'Date Range', 'Top Stories'])
        
        for report in data:
            title = report.get('title', 'Unknown')
            date_posted = report.get('date_posted', 'Unknown')
            date_range = report.get('date_range', 'Unknown')
            
            for story in report.get('top_stories', []):
                writer.writerow([title, date_posted, date_range, story])

def main():
    """Main function to scrape PEJ News Coverage Index data."""
    ensure_dir_exists(OUTPUT_DIR)
    
    print(f"Fetching PEJ News Index page from Wayback Machine...")
    html = get_page_content(WAYBACK_URL)
    
    if not html:
        print("Failed to fetch the PEJ News Index page.")
        return
    
    print("Extracting report links...")
    reports = extract_report_links(html)
    
    if not reports:
        print("No report links found.")
        return
    
    print(f"Found {len(reports)} reports. Processing...")
    
    all_reports = []
    
    for i, report in enumerate(reports):
        print(f"Processing report {i+1}/{len(reports)}: {report['title']}...")
        
        report_html = get_page_content(report['url'])
        
        if not report_html:
            print(f"Failed to fetch report: {report['title']}")
            continue
        
        report_data = extract_report_content(report_html, report['title'])
        
        if report_data:
            report_data['date_range'] = report['date_range']
            all_reports.append(report_data)
        
        time.sleep(1)
    
    if all_reports:
        json_filename = os.path.join(OUTPUT_DIR, "pej_news_coverage_index_2011.json")
        csv_filename = os.path.join(OUTPUT_DIR, "pej_news_coverage_index_2011.csv")
        
        save_data(all_reports, json_filename)
        save_csv(all_reports, csv_filename)
        
        print(f"Data saved to {json_filename} and {csv_filename}")
    else:
        print("No report data collected.")

if __name__ == "__main__":
    main()
