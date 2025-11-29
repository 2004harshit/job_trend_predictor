# """
# Debug script to find correct CSS selectors on Naukri job pages
# Run this to identify which selectors are currently working
# """

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from bs4 import BeautifulSoup
# import time

# def setup_driver():
#     options = webdriver.ChromeOptions()
#     options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
#     service = Service(ChromeDriverManager().install())
#     return webdriver.Chrome(service=service, options=options)

# def debug_job_listing_page():
#     """Debug a sample job listing page to find correct selectors"""
#     driver = setup_driver()
    
#     try:
#         # Open a job search page
#         url = "https://www.naukri.com/python-developer-jobs-in-bangalore"
#         print(f"Opening: {url}")
#         driver.get(url)
        
#         wait = WebDriverWait(driver, 10)
#         wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.title")))
        
#         page = BeautifulSoup(driver.page_source, "html.parser")
        
#         # Test different selectors for job titles
#         print("\n" + "="*60)
#         print("TESTING JOB TITLE SELECTORS")
#         print("="*60)
        
#         selectors_to_test = [
#             "a.title",
#             "a[class*='title']",
#             "h2 a",
#             "a[href*='/job-listings']",
#             ".jobTitl",
#             "div[class*='jobCard'] a"
#         ]
        
#         for selector in selectors_to_test:
#             try:
#                 elements = page.select(selector)
#                 if elements:
#                     print(f"✓ '{selector}': Found {len(elements)} elements")
#                     if len(elements) > 0:
#                         print(f"  Sample: {elements[0].get_text(strip=True)[:50]}")
#             except Exception as e:
#                 print(f"✗ '{selector}': Error - {e}")
        
#         # Test selectors on actual job detail page
#         print("\n" + "="*60)
#         print("OPENING FIRST JOB FOR DETAIL EXTRACTION TEST")
#         print("="*60)
        
#         job_links = page.select("a.title")
#         if job_links:
#             job_url = job_links[0].get("href")
#             print(f"Opening: {job_url}")
#             driver.get(job_url)
#             time.sleep(2)
            
#             job_page = BeautifulSoup(driver.page_source, "html.parser")
            
#             # Test various selectors
#             detail_selectors = {
#                 "Title (h1)": ("h1", {"class": "styles_jd-header-title__rZwM1"}),
#                 "Company (a)": ("a", {"href": lambda x: x and "jobs-careers" in x}),
#                 "Experience": ("div", {"class": "styles_jhc__exp__k_giM"}),
#                 "Salary": ("div", {"class": "styles_jhc__salary__jdfEC"}),
#                 "Location": ("span", {"class": "styles_jhc__location__W_pVs"}),
#                 "Posted Date": ("span", {"class": "styles_posted-on__LHzrs"}),
#                 "Apply By": ("span", {"class": "styles_apply-by__w_9TN"}),
#                 "Skills": ("div", {"class": "styles_key-skill__GIPn_"}),
#                 "Description": ("div", {"class": "styles_JDC__dang-inner-html__h0K4t"}),
#             }
            
#             for field_name, (tag, attrs) in detail_selectors.items():
#                 try:
#                     element = job_page.find(tag, attrs)
#                     if element:
#                         text = element.get_text(strip=True)[:80]
#                         print(f"✓ {field_name}: Found - {text}")
#                     else:
#                         print(f"✗ {field_name}: NOT FOUND")
#                 except Exception as e:
#                     print(f"✗ {field_name}: Error - {e}")
            
#             # Print full page source for manual inspection (first 3000 chars)
#             print("\n" + "="*60)
#             print("PAGE SOURCE SNIPPET")
#             print("="*60)
#             print(driver.page_source[:3000])
    
#     finally:
#         driver.quit()

# if __name__ == "__main__":
#     debug_job_listing_page()


"""
Find where date information is located on Naukri job pages
This helps identify the exact selectors needed for Posted Date and Apply By
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import time

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def find_date_info():
    driver = setup_driver()
    
    try:
        url = "https://www.naukri.com/job-listings-python-software-developer-capgemini-bengaluru-6-to-11-years-111125013560"
        print(f"Opening: {url}\n")
        driver.get(url)
        time.sleep(2)
        
        page = BeautifulSoup(driver.page_source, "html.parser")
        
        print("="*70)
        print("SEARCHING FOR DATE-RELATED INFORMATION")
        print("="*70)
        
        # Date patterns to search for
        date_patterns = [
            r'\d{1,2}-\w+-\d{4}',  # DD-Mon-YYYY
            r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY
            r'\d{1,2}\s+\w+\s+\d{4}',  # DD Month YYYY
            r'Posted\s+\d+',  # Posted X
            r'Apply by',  # Apply by
            r'Closing',  # Closing date
        ]
        
        page_text = page.get_text()
        
        print("\n1. SEARCHING FULL PAGE TEXT FOR DATE PATTERNS:")
        print("-" * 70)
        for pattern in date_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                # Get unique matches (remove duplicates)
                unique_matches = list(set(matches))[:5]
                print(f"Pattern '{pattern}':")
                for match in unique_matches:
                    print(f"  → {match}")
        
        print("\n2. SEARCHING HTML STRUCTURE FOR DATE FIELDS:")
        print("-" * 70)
        
        # Find all divs/spans with specific keywords
        keywords = ['posted', 'apply', 'deadline', 'closing', 'date']
        
        found_elements = []
        for elem in page.find_all(['div', 'span', 'p']):
            text = elem.get_text(strip=True)
            if any(keyword in text.lower() for keyword in keywords) and text and len(text) < 150:
                found_elements.append({
                    'tag': elem.name,
                    'class': elem.get('class'),
                    'text': text[:100],
                    'html': str(elem)[:200]
                })
        
        if found_elements:
            print(f"Found {len(found_elements)} relevant elements:\n")
            for i, elem_info in enumerate(found_elements[:10], 1):
                print(f"{i}. Tag: <{elem_info['tag']}>, Class: {elem_info['class']}")
                print(f"   Text: {elem_info['text']}")
                print(f"   HTML: {elem_info['html']}\n")
        else:
            print("No date-related elements found in common tags")
        
        print("\n3. CHECKING DETAILS SECTION:")
        print("-" * 70)
        
        details_div = page.find("div", class_="styles_other-details__oEN4O")
        if details_div:
            print("Details section found!")
            detail_items = details_div.find_all("div", class_="styles_details__Y424J")
            print(f"Found {len(detail_items)} detail items:\n")
            
            for i, item in enumerate(detail_items[:15], 1):
                label = item.find("label")
                span = item.find("span")
                
                label_text = label.get_text(strip=True) if label else "NA"
                span_text = span.get_text(strip=True) if span else "NA"
                
                print(f"{i}. Label: {label_text}")
                print(f"   Value: {span_text}\n")
        else:
            print("Details section NOT found")
        
        print("\n4. FULL PAGE SOURCE (FIRST 5000 CHARS):")
        print("-" * 70)
        print(driver.page_source[:5000])
    
    finally:
        driver.quit()

if __name__ == "__main__":
    find_date_info()