"""Test script to check NI Direct website structure"""
import requests
from bs4 import BeautifulSoup

NI_DIRECT_URL = "https://www.nidirect.gov.uk/articles/emergency-department-average-waiting-times"

print("Fetching NI Direct page...")
r = requests.get(NI_DIRECT_URL, timeout=30)
r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")

print("\n=== Looking for Emergency Departments heading ===")
for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
    text = tag.get_text(strip=True)
    if "emergency" in text.lower() or "department" in text.lower():
        print(f"Found: <{tag.name}> {text}")

print("\n=== All tables on page ===")
tables = soup.find_all("table")
print(f"Total tables found: {len(tables)}")

for i, table in enumerate(tables):
    print(f"\nTable {i+1}:")
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    print(f"  Headers: {headers[:5]}")  # First 5 headers
    
    # Get first data row
    first_row = table.find("tr")
    if first_row:
        cells = [td.get_text(strip=True) for td in first_row.find_all(["td", "th"])]
        if cells:
            print(f"  First row: {cells[:3]}")  # First 3 cells

print("\n=== Checking for data in divs/sections ===")
# Sometimes data is in divs instead of tables
for div in soup.find_all("div", class_=True):
    text = div.get_text(strip=True)
    if "altnagelvin" in text.lower() or "royal victoria" in text.lower():
        print(f"Found hospital data in: {div.get('class')}")
        print(f"  Text preview: {text[:100]}...")
        break
