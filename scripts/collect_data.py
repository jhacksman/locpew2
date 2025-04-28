"""
Main script to collect US media headlines from July 1, 2011 to September 30, 2011
from multiple sources including New York Times, Pew Research Center, and Library of Congress.
"""

import os
import subprocess
import sys

def run_script(script_path):
    """Run a Python script and return its exit code."""
    print(f"Running {os.path.basename(script_path)}...")
    result = subprocess.run([sys.executable, script_path])
    return result.returncode

def main():
    """Main function to run all data collection scripts."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    nyt_script = os.path.join(script_dir, "collect_nyt_headlines.py")
    pew_script = os.path.join(script_dir, "scrape_pew_data.py")
    loc_script = os.path.join(script_dir, "scrape_loc_data.py")
    
    print("Collecting data from New York Times...")
    nyt_exit_code = run_script(nyt_script)
    
    if nyt_exit_code != 0:
        print(f"Error: New York Times data collection script failed with exit code {nyt_exit_code}")
    
    print("Collecting data from Pew Research Center...")
    pew_exit_code = run_script(pew_script)
    
    if pew_exit_code != 0:
        print(f"Error: Pew Research Center data collection script failed with exit code {pew_exit_code}")
    
    print("Collecting data from Library of Congress...")
    loc_exit_code = run_script(loc_script)
    
    if loc_exit_code != 0:
        print(f"Error: Library of Congress data collection script failed with exit code {loc_exit_code}")
    
    if nyt_exit_code == 0 or pew_exit_code == 0 or loc_exit_code == 0:
        print("Data collection completed successfully!")
        return 0
    else:
        print("Data collection completed with errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
