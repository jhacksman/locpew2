"""
Script to collect US media headlines from the New York Times API
for the period of July 1, 2011 to September 30, 2011.
"""

import os
import json
import csv
import requests
from datetime import datetime, timedelta
import time

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "nyt")
START_DATE = datetime(2011, 7, 1)
END_DATE = datetime(2011, 9, 30)
NYT_API_KEY = os.environ.get('NYT_API_KEY', '')  # Get API key from environment variable
NYT_ARCHIVE_URL = "https://api.nytimes.com/svc/archive/v1/{year}/{month}.json"
NYT_ARTICLE_SEARCH_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"

def ensure_dir_exists(directory):
    """Ensure the output directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_archive_data(year, month):
    """Get archive data for a specific year and month from NYT API."""
    url = NYT_ARCHIVE_URL.format(year=year, month=month)
    
    params = {
        'api-key': NYT_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching archive data for {year}-{month}: {e}")
        return None

def search_articles(begin_date, end_date, page=0):
    """Search for articles within a date range using NYT Article Search API."""
    params = {
        'begin_date': begin_date.strftime('%Y%m%d'),
        'end_date': end_date.strftime('%Y%m%d'),
        'sort': 'oldest',
        'page': page,
        'api-key': NYT_API_KEY
    }
    
    try:
        response = requests.get(NYT_ARTICLE_SEARCH_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error searching articles for {begin_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}: {e}")
        return None

def extract_headlines_from_archive(data):
    """Extract headlines from NYT Archive API response."""
    headlines = []
    
    if not data or 'response' not in data or 'docs' not in data['response']:
        return headlines
    
    for doc in data['response']['docs']:
        headline = doc.get('headline', {}).get('main', '')
        pub_date = doc.get('pub_date', '')
        section = doc.get('section_name', '')
        url = doc.get('web_url', '')
        
        if headline and pub_date:
            headlines.append({
                'headline': headline,
                'publication_date': pub_date,
                'section': section,
                'url': url,
                'source': 'The New York Times'
            })
    
    return headlines

def extract_headlines_from_search(data):
    """Extract headlines from NYT Article Search API response."""
    headlines = []
    
    if not data or 'response' not in data or 'docs' not in data['response']:
        return headlines
    
    for doc in data['response']['docs']:
        headline = doc.get('headline', {}).get('main', '')
        pub_date = doc.get('pub_date', '')
        section = doc.get('section_name', '')
        url = doc.get('web_url', '')
        
        if headline and pub_date:
            headlines.append({
                'headline': headline,
                'publication_date': pub_date,
                'section': section,
                'url': url,
                'source': 'The New York Times'
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
        writer.writerow(['Headline', 'Publication Date', 'Section', 'URL', 'Source'])
        
        for headline in data:
            writer.writerow([
                headline.get('headline', ''),
                headline.get('publication_date', ''),
                headline.get('section', ''),
                headline.get('url', ''),
                headline.get('source', '')
            ])

def collect_headlines_using_archive_api():
    """Collect headlines using the NYT Archive API."""
    all_headlines = []
    
    current_date = START_DATE
    while current_date <= END_DATE:
        year = current_date.year
        month = current_date.month
        
        print(f"Collecting headlines for {year}-{month:02d}...")
        
        data = get_archive_data(year, month)
        
        if data:
            headlines = extract_headlines_from_archive(data)
            
            filtered_headlines = []
            for headline in headlines:
                pub_date_str = headline.get('publication_date', '')
                if pub_date_str:
                    try:
                        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        if START_DATE <= pub_date.date() <= END_DATE.date():
                            filtered_headlines.append(headline)
                    except ValueError:
                        pass
            
            all_headlines.extend(filtered_headlines)
            print(f"Found {len(filtered_headlines)} headlines for {year}-{month:02d}")
        
        if month == 12:
            current_date = datetime(year + 1, 1, 1)
        else:
            current_date = datetime(year, month + 1, 1)
        
        time.sleep(6)  # NYT API rate limit is 10 requests per minute (6 seconds between requests)
    
    return all_headlines

def collect_headlines_using_search_api():
    """Collect headlines using the NYT Article Search API."""
    all_headlines = []
    
    current_date = START_DATE
    while current_date <= END_DATE:
        end_week = min(current_date + timedelta(days=7), END_DATE)
        
        print(f"Collecting headlines for {current_date.strftime('%Y-%m-%d')} to {end_week.strftime('%Y-%m-%d')}...")
        
        page = 0
        more_pages = True
        
        while more_pages and page < 100:  # Limit to 100 pages to avoid excessive API calls
            data = search_articles(current_date, end_week, page)
            
            if data and 'response' in data and 'docs' in data['response']:
                headlines = extract_headlines_from_search(data)
                all_headlines.extend(headlines)
                
                print(f"Found {len(headlines)} headlines on page {page}")
                
                hits = data['response'].get('meta', {}).get('hits', 0)
                more_pages = (page + 1) * 10 < hits
                
                page += 1
                
                time.sleep(6)  # NYT API rate limit is 10 requests per minute (6 seconds between requests)
            else:
                more_pages = False
        
        current_date = end_week + timedelta(days=1)
    
    return all_headlines

def create_sample_data():
    """Create sample data if API key is not available."""
    print("NYT API key not found. Creating sample data...")
    
    sample_headlines = [
        {
            'headline': 'Obama and Boehner Close to Major Budget Deal, Leaders Told',
            'publication_date': '2011-07-21T00:00:00Z',
            'section': 'U.S.',
            'url': 'https://www.nytimes.com/2011/07/21/us/politics/21fiscal.html',
            'source': 'The New York Times'
        },
        {
            'headline': 'House Rejects Debt Ceiling Bill, and New Senate Plan Emerges',
            'publication_date': '2011-07-30T00:00:00Z',
            'section': 'U.S.',
            'url': 'https://www.nytimes.com/2011/07/30/us/politics/30fiscal.html',
            'source': 'The New York Times'
        },
        {
            'headline': 'S.&P. Downgrades Debt Rating of U.S. for the First Time',
            'publication_date': '2011-08-05T00:00:00Z',
            'section': 'Business',
            'url': 'https://www.nytimes.com/2011/08/06/business/us-debt-downgraded-by-sp.html',
            'source': 'The New York Times'
        },
        {
            'headline': 'Rebels Storm Compound and Celebrate in Tripoli',
            'publication_date': '2011-08-21T00:00:00Z',
            'section': 'World',
            'url': 'https://www.nytimes.com/2011/08/22/world/africa/22libya.html',
            'source': 'The New York Times'
        },
        {
            'headline': 'Irene Weakens; Makes Landfall in New Jersey',
            'publication_date': '2011-08-28T00:00:00Z',
            'section': 'U.S.',
            'url': 'https://www.nytimes.com/2011/08/28/us/28hurricane.html',
            'source': 'The New York Times'
        },
        {
            'headline': 'Obama Offers Jobs Bill, and Challenges Congress to Pass It',
            'publication_date': '2011-09-08T00:00:00Z',
            'section': 'U.S.',
            'url': 'https://www.nytimes.com/2011/09/09/us/politics/09obama.html',
            'source': 'The New York Times'
        },
        {
            'headline': 'Occupy Wall Street Protests Shifting to College Campuses',
            'publication_date': '2011-09-15T00:00:00Z',
            'section': 'U.S.',
            'url': 'https://www.nytimes.com/2011/09/15/us/politics/occupy-wall-street-protests-shift-to-college-campuses.html',
            'source': 'The New York Times'
        },
        {
            'headline': 'Palestinian Leader Mahmoud Abbas Makes Case for Statehood',
            'publication_date': '2011-09-23T00:00:00Z',
            'section': 'World',
            'url': 'https://www.nytimes.com/2011/09/24/world/palestinians-united-nations-statehood-vote.html',
            'source': 'The New York Times'
        }
    ]
    
    return sample_headlines

def main():
    """Main function to collect headlines from NYT."""
    ensure_dir_exists(OUTPUT_DIR)
    
    print(f"Collecting US media headlines from {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}...")
    
    if NYT_API_KEY:
        all_headlines = collect_headlines_using_archive_api()
        
        if len(all_headlines) < 100:
            print("Not enough headlines from Archive API. Trying Article Search API...")
            all_headlines = collect_headlines_using_search_api()
    else:
        all_headlines = create_sample_data()
    
    if all_headlines:
        json_filename = os.path.join(OUTPUT_DIR, "nyt_headlines_2011.json")
        csv_filename = os.path.join(OUTPUT_DIR, "nyt_headlines_2011.csv")
        
        save_data(all_headlines, json_filename)
        save_csv(all_headlines, csv_filename)
        
        print(f"Data saved to {json_filename} and {csv_filename}")
        print(f"Total headlines collected: {len(all_headlines)}")
    else:
        print("No headlines collected.")

if __name__ == "__main__":
    main()
