from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import random

def setup_driver():
    """Setup Chrome driver with necessary options"""
    options = webdriver.ChromeOptions()
    # Remove headless mode to bypass detection
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-notifications')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def wait_and_find_elements(driver, by, value, timeout=20):
    """Wait for elements to be present and return them"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        # Add random delay to mimic human behavior
        time.sleep(random.uniform(2, 4))
        return driver.find_elements(by, value)
    except TimeoutException:
        print(f"Timeout waiting for elements: {value}")
        return []

def scrape_naukri_jobs(max_jobs=30):
    """Scrape jobs from Naukri.com"""
    driver = setup_driver()
    jobs = []
    
    try:
        print("Opening Naukri.com...")
        # Use a more specific job search URL
        driver.get("https://www.naukri.com/data-science-jobs")
        
        # Wait for page load and handle popups
        time.sleep(5)
        
        # Execute JavaScript to modify navigator properties
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Waiting for job listings to load...")
        
        # Scroll with random delays
        for i in range(3):
            scroll_height = random.randint(500, 1000)
            driver.execute_script(f"window.scrollBy(0, {scroll_height})")
            time.sleep(random.uniform(2, 4))
            print(f"Scroll {i+1}/3 completed")
        
        print("Extracting job information...")
        
        # Try multiple selectors
        selectors = [
            "article[data-job-id]",  # Main job card
            ".jobTuple",             # Alternative job card
            ".job-card"              # Another alternative
        ]
        
        job_cards = []
        for selector in selectors:
            job_cards = wait_and_find_elements(driver, By.CSS_SELECTOR, selector)
            if job_cards:
                print(f"Found jobs using selector: {selector}")
                break
        
        print(f"Found {len(job_cards)} job cards")
        
        for card in job_cards[:max_jobs]:
            try:
                # Try multiple selectors for each field
                title = card.find_element(By.CSS_SELECTOR, "a.title, .jobTitle, .job-title").text
                company = card.find_element(By.CSS_SELECTOR, ".companyInfo, .company-name, .job-company").text
                
                try:
                    experience = card.find_element(By.CSS_SELECTOR, ".experience, .exp-container, .job-experience").text
                except:
                    experience = "Not specified"
                
                try:
                    salary = card.find_element(By.CSS_SELECTOR, ".salary, .salary-container, .job-salary").text
                except:
                    salary = "Not disclosed"
                
                try:
                    location = card.find_element(By.CSS_SELECTOR, ".location, .location-container, .job-location").text
                except:
                    location = "Not specified"
                
                try:
                    skills = [skill.text for skill in card.find_elements(By.CSS_SELECTOR, ".tag, .skill, .job-skill")]
                except:
                    skills = []
                
                job = {
                    'title': title.strip(),
                    'company': company.strip(),
                    'experience': experience.strip(),
                    'salary': salary.strip(),
                    'location': location.strip(),
                    'skills': [s.strip() for s in skills if s.strip()]
                }
                
                jobs.append(job)
                print(f"Scraped job: {title}")
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error scraping job card: {str(e)}")
                continue
        
        return jobs
        
    finally:
        driver.quit()

if __name__ == "__main__":
    try:
        print("Starting job scraper...")
        jobs_data = scrape_naukri_jobs(max_jobs=30)
        
        if jobs_data:
            output_file = 'naukri_jobs.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(jobs_data, f, indent=2, ensure_ascii=False)
            print(f"\nSuccessfully scraped {len(jobs_data)} jobs and saved to {output_file}")
        else:
            print("No jobs were scraped. Please check the website structure or try again later.")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")