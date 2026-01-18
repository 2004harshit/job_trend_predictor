# from etl_pipeline.data_collection.base import JobExtractor
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import pandas as pd
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from bs4 import BeautifulSoup
# import random, time
# import datetime
# # from etl_pipeline.utils.robots import is_allowed
# from etl_pipeline.utils.backoff import exponential_backoff


# class NaukriJobExtractor(JobExtractor):
#     def __init__(self , max_pages , per_page_limit , min_delay , max_delay ,role_delay=10,logger=None):
#         self.max_pages = max_pages
#         self.per_page_limit = per_page_limit
#         self.min_delay = min_delay
#         self.max_delay = max_delay
#         self.role_delay = role_delay
#         self.logger = logger

#     def extract(self  ,job_name: str):
#         self.logger.info(f"tarting job scraping for `{job_name}` using NaukriJobExtractor")


#         options = webdriver.ChromeOptions()
#         options.add_argument("--headless")          # Run without GUI
#         options.add_argument("--no-sandbox")        # Required for many Linux servers
#         options.add_argument("--disable-dev-shm-usage")  # Avoid memory issues
#         options.add_argument("--window-size=1920,1080")
#         options.add_argument("user-agent=Mozilla/5.0 ... Chrome/117.0 Safari/537.36")

#         self.service = Service(ChromeDriverManager().install())
#         self.driver = webdriver.Chrome(service=self.service , options=options)
#         driver =self.driver
#         wait = WebDriverWait(self.driver, 8)
        

#         extracted_data = []
#         seen_job_urls = set()

#         job_url = f"https://www.naukri.com/{job_name}-jobs"

#         # if not is_allowed(job_url, "JobPipelineBot"):
#         #     self.logger.error(f"Skipping {job_url} due to robots.txt restrictions")
#         #     return []
        
#         # start from first page
#         exponential_backoff(lambda: driver.get(job_url))
#         # driver.get(job_url)
#         page_no = 1

#         while page_no <= self.max_pages:
#             self.logger.debug(f"Processing page {page_no} for {job_name}")
#             try:
#                 wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.title")))
#             except Exception as e:
#                 self.logger.error(f"Failed to load job listing for {job_name} on page {page_no}: {e}")
#                 break

#             # collect job URLs
#             job_elems = driver.find_elements(By.CSS_SELECTOR, "a.title")
#             job_hrefs = [a.get_attribute("href") for a in job_elems if a.get_attribute("href")]

#             if self.per_page_limit:
#                 job_hrefs = job_hrefs[:self.per_page_limit]
            
#             self.logger.info(f"Found {len(job_hrefs)} links on page {page_no} for `{job_name}`")

#             # scrape each job
#             for job_url in job_hrefs:
#                 if job_url in seen_job_urls:
#                     self.logger.debug(f"Skipping duplicate job url : {job_url}")
#                     continue
#                 seen_job_urls.add(job_url)

#                 try:
#                     driver.execute_script("window.open(arguments[0], '_blank');", job_url)
#                     driver.switch_to.window(driver.window_handles[-1])
#                     # random delay to mimic human behavior
#                     time.sleep(random.uniform(self.min_delay,self.max_delay))

#                     page = BeautifulSoup(driver.page_source, "html.parser")

#                     # extract job  info
#                     title = page.find("h1", class_="styles_jd-header-title__rZwM1")
#                     title = title.get_text(strip=True) if title else "NA"

#                     comp_elem = page.find("a", href=lambda x: x and "jobs-careers" in x)
#                     company = comp_elem.get_text(strip=True) if comp_elem else "NA"

#                     exp_elem = page.find("div", class_="styles_jhc__exp__k_giM")
#                     exp = exp_elem.find("span").get_text(strip=True) if exp_elem and exp_elem.find("span") else "NA"

#                     salary_elem = page.find("div", class_="styles_jhc__salary__jdfEC")
#                     salary = salary_elem.find("span").get_text(strip=True) if salary_elem and salary_elem.find("span") else "NA"

#                     loc_elem = page.find("span", class_="styles_jhc__location__W_pVs")
#                     location = loc_elem.get_text(strip=True) if loc_elem else "NA"

#                     details = {}
#                     details_section = page.find("div", class_="styles_other-details__oEN4O")
#                     if details_section:
#                         for div in details_section.find_all("div", class_="styles_details__Y424J"):
#                             label = div.find("label")
#                             span = div.find("span")
#                             if label:
#                                 details[label.get_text(strip=True).replace(":", "")] = span.get_text(" ", strip=True) if span else "NA"

#                     edu_elem = page.find("div", class_="styles_education__KXFkO")
#                     education = edu_elem.get_text(strip=True) if edu_elem else "Not Available"

#                     skills_section = page.find("div", class_="styles_key-skill__GIPn_")
#                     star_skills, normal_skills = [], []
#                     if skills_section:
#                         for a in skills_section.find_all("a", class_="styles_chip__7YCfG"):
#                             skill_name = a.find("span").get_text(strip=True) if a.find("span") else "NA"
#                             if a.find("i", class_="ni-icon-jd-save"):
#                                 star_skills.append(skill_name)
#                             else:
#                                 normal_skills.append(skill_name)
#                     skills = [star_skills, normal_skills]

#                     jd_elem = page.find("div", class_="styles_JDC__dang-inner-html__h0K4t")
#                     job_description = jd_elem.get_text(" ", strip=True) if jd_elem else "NA"

#                     extracted_data.append({
#                         "Job Type": job_name,
#                         "Title": title,
#                         "Company": company,
#                         "Experience": exp,
#                         "Salary": salary,
#                         "Location": location,
#                         "Education": education,
#                         "Skills": skills,
#                         **details,
#                         "Description": job_description,
#                         "Job URL": job_url,
#                         "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                     })

#                     self.logger.debug(f"Extracted job: {title} ({job_url})")

#                 except Exception as e:
#                     self.logger.error(f"Error extracting job at {job_url}: {e}")
#                 finally:
#                     driver.close()
#                     driver.switch_to.window(driver.window_handles[0])

#             # move to next page
#             try:
#                 next_btn = driver.find_element(By.CSS_SELECTOR, "a.styles_btn-secondary__2AsIP[href*='-jobs-']")
#                 next_href = next_btn.get_attribute("href")
#                 if not next_href:
#                     self.logger.warning(f"No 'Next' link found on page {page_no} for {job_name}. Stopping")
#                     break
#                 driver.get(next_href)
#                 page_no += 1
#             except:
#                 self.logger.warning(f"No Next button found on page {page_no} for {job_name} Ending pagination")
#                 break

#         self.logger.info(f"Finished scraping {len(extracted_data)} jobs for '{job_name}'")
#         self.logger.info(f"Sleeping {self.role_delay} seconds before next role")
#         time.sleep(self.role_delay)

#         return extracted_data
    
#     def get_name(self):
#         return "NaukriExtractor"
    
    
# if __name__ == "__main__":
#     Nje = NaukriJobExtractor()
#     Nje.extract("python-developer", 10 , 15)

# from etl_pipeline.data_collection.base import JobExtractor
from ..base import JobExtractor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import random, time
import datetime
from typing import List, Optional, Set
# from etl_pipeline.utils.backoff import exponential_backoff
from ...utils.backoff import exponential_backoff

import logging
from ...utils.logger import setup_logging

setup_logging()

class NaukriJobExtractor(JobExtractor):
    """
    Extracts job listings from Naukri.com with support for location filtering,
    retry logic, and comprehensive error handling.
    """
    
    # Supported locations on Naukri
    SUPPORTED_LOCATIONS = {
        'delhi', 'bengaluru', 'mumbai', 'hyderabad', 'pune', 'kolkata',
        'chennai', 'ahmedabad', 'jaipur', 'lucknow', 'surat', 'indore',
        'chandigarh', 'kochi', 'noida', 'gurgaon', 'gurugram'
    }

    def __init__(self, max_pages: int, per_page_limit: Optional[int] = None,
                 min_delay: float = 2, max_delay: float = 5, role_delay: float = 10,
                 locations: Optional[List[str]] = None, logger=None):
        """
        Initialize the Naukri Job Extractor.
        
        Args:
            max_pages: Maximum number of pages to scrape
            per_page_limit: Max jobs per page (None for all)
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            role_delay: Delay between different job roles (seconds)
            locations: List of locations to filter (e.g., ['bangalore', 'mumbai'])
            logger: Logger instance
        """
        self.max_pages = max_pages
        self.per_page_limit = per_page_limit
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.role_delay = role_delay
        self.logger = logger
        self.driver = None
        self.service = None
        self.logger = logger or logging.getLogger("data_collection") 
        
        # Location filtering
        self.locations = [loc.lower() for loc in (locations or [])]
        self._validate_locations()

    def _validate_locations(self):
        """Validate that provided locations are supported."""
        if self.locations:
            invalid = [loc for loc in self.locations if loc not in self.SUPPORTED_LOCATIONS]
            if invalid:
                self.logger.warning(f"Invalid locations: {invalid}. Supported: {self.SUPPORTED_LOCATIONS}")
                self.locations = [loc for loc in self.locations if loc in self.SUPPORTED_LOCATIONS]

    def _setup_driver(self):
        """Initialize and configure Selenium WebDriver."""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            self.service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=self.service, options=options)
            self.logger.info("WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def _close_driver(self):
        """Safely close the WebDriver."""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("WebDriver closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing WebDriver: {e}")

    def _build_job_url(self, job_name: str, location: Optional[str] = None) -> str:
        """
        Build Naukri job search URL with optional location filter.
        
        Args:
            job_name: Job title/keyword
            location: Location filter (optional)
            
        Returns:
            Complete URL string
        """
        base_url = f"https://www.naukri.com/{job_name}-jobs"
        if location and location in self.SUPPORTED_LOCATIONS:
            base_url += f"-in-{location}"
        return base_url

    def _extract_timestamps(self, page: BeautifulSoup) -> tuple:
        """
        Extract job posting date and last date to apply.
        Searches through multiple possible locations on the page.
        
        Returns:
            Tuple of (posted_date, last_apply_date)
        """
        posted_date = "NA"
        last_apply_date = "NA"
        
        try:
            # Strategy 1: Primary selector - found in stats section
            jd_stats = page.find("div", class_="styles_jhc__jd-stats__KrId0")
            if jd_stats:
                stat_spans = jd_stats.find_all("span", class_="styles_jhc__stat__PgY67")
                for span in stat_spans:
                    label = span.find("label")
                    value_span = span.find("span")
                    
                    if label and value_span:
                        label_text = label.get_text(strip=True).lower()
                        value_text = value_span.get_text(strip=True)
                        
                        if "posted" in label_text:
                            posted_date = value_text
            
            # Strategy 2: Alternative selector - similar jobs card
            if posted_date == "NA":
                posted_div = page.find("div", class_="styles_SJC__posted-date__eiY9o")
                if posted_div:
                    span = posted_div.find("span")
                    if span:
                        posted_date = span.get_text(strip=True)
            
            # Strategy 3: Look for "Apply by" or deadline info in page
            # Note: Naukri doesn't always show "Apply by" date, but we'll search for it
            page_text = page.get_text()
            
            # Try to find deadline using regex
            import re
            
            # Look for date patterns like "25 Aug 2025" or "Apply by X"
            if last_apply_date == "NA":
                # Pattern: "DD Month YYYY"
                date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', page_text)
                if date_match:
                    last_apply_date = date_match.group(1)
        
        except Exception as e:
            self.logger.debug(f"Error extracting timestamps: {e}")
        
        return posted_date, last_apply_date

    def _extract_job_details(self, page: BeautifulSoup, job_url: str) -> Optional[dict]:
        """
        Extract structured data from a job listing page.
        
        Args:
            page: BeautifulSoup parsed page
            job_url: URL of the job listing
            
        Returns:
            Dictionary with extracted job details or None on error
        """
        try:
            # Core fields with fallback
            title = page.find("h1", class_="styles_jd-header-title__rZwM1")
            title = title.get_text(strip=True) if title else "NA"

            comp_elem = page.find("a", href=lambda x: x and "jobs-careers" in x)
            company = comp_elem.get_text(strip=True) if comp_elem else "NA"

            exp_elem = page.find("div", class_="styles_jhc__exp__k_giM")
            exp = exp_elem.find("span").get_text(strip=True) if exp_elem and exp_elem.find("span") else "NA"

            salary_elem = page.find("div", class_="styles_jhc__salary__jdfEC")
            salary = salary_elem.find("span").get_text(strip=True) if salary_elem and salary_elem.find("span") else "NA"

            loc_elem = page.find("span", class_="styles_jhc__location__W_pVs")
            location = loc_elem.get_text(strip=True) if loc_elem else "NA"

            # Extract timestamps (may return "NA" if not found on page)
            posted_date, last_apply_date = self._extract_timestamps(page)
            
            self.logger.debug(f"Dates extracted - Posted: {posted_date}, Apply By: {last_apply_date}")

            # Extract additional details
            details = self._extract_other_details(page)
            
            # Education
            edu_elem = page.find("div", class_="styles_education__KXFkO")
            education = edu_elem.get_text(strip=True) if edu_elem else "Not Available"

            # Skills with star/normal classification
            star_skills, normal_skills = self._extract_skills(page)

            # Job description
            jd_elem = page.find("div", class_="styles_JDC__dang-inner-html__h0K4t")
            job_description = jd_elem.get_text(" ", strip=True) if jd_elem else "NA"

            return {
                "Title": title,
                "Company": company,
                "Experience": exp,
                "Salary": salary,
                "Location": location,
                "Education": education,
                "Star_Skills": star_skills,
                "Normal_Skills": normal_skills,
                "Posted_Date": posted_date,
                "Last_Apply_Date": last_apply_date,
                **details,
                "Description": job_description,
                "Job_URL": job_url,
                "Scraped_At": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error extracting job details from {job_url}: {e}")
            return None

    def _extract_other_details(self, page: BeautifulSoup) -> dict:
        """Extract miscellaneous job details."""
        details = {}
        try:
            details_section = page.find("div", class_="styles_other-details__oEN4O")
            if details_section:
                for div in details_section.find_all("div", class_="styles_details__Y424J"):
                    label = div.find("label")
                    span = div.find("span")
                    if label and span:
                        key = label.get_text(strip=True).replace(":", "")
                        value = span.get_text(" ", strip=True)
                        details[key] = value
        except Exception as e:
            self.logger.debug(f"Error extracting other details: {e}")
        return details

    def _extract_skills(self, page: BeautifulSoup) -> tuple:
        """Extract and categorize skills from job listing."""
        star_skills, normal_skills = [], []
        try:
            skills_section = page.find("div", class_="styles_key-skill__GIPn_")
            if skills_section:
                for a in skills_section.find_all("a", class_="styles_chip__7YCfG"):
                    skill_span = a.find("span")
                    skill_name = skill_span.get_text(strip=True) if skill_span else "NA"
                    if skill_name != "NA":
                        if a.find("i", class_="ni-icon-jd-save"):
                            star_skills.append(skill_name)
                        else:
                            normal_skills.append(skill_name)
        except Exception as e:
            self.logger.debug(f"Error extracting skills: {e}")
        return star_skills, normal_skills

    def _apply_location_filter(self, location: str) -> bool:
        """
        Check if job location matches desired filters.
        
        Args:
            location: Job location from listing
            
        Returns:
            True if location matches filter or no filter applied
        """
        if not self.locations:
            return True
        
        location_lower = location.lower()
        return any(loc in location_lower for loc in self.locations)

    def extract(self, job_name: str, locations: Optional[List[str]] = None) -> List[dict]:
        """
        Extract job listings from Naukri.com.
        
        Args:
            job_name: Job title/keyword to search
            locations: Override instance locations for this extraction
            
        Returns:
            List of extracted job dictionaries
        """
        # Override locations if provided
        active_locations = locations or self.locations or [None]
        extracted_data = []

        for location in active_locations:
            self.logger.info(f"Starting extraction for '{job_name}' in {location or 'All Locations'}")
            location_data = self._extract_for_location(job_name, location)
            extracted_data.extend(location_data)

        self.logger.info(f"Finished scraping {len(extracted_data)} total jobs for '{job_name}'")
        return extracted_data

    def _extract_for_location(self, job_name: str, location: Optional[str]) -> List[dict]:
        """Extract jobs for a specific location."""
        self._setup_driver()
        extracted_data = []
        seen_job_urls: Set[str] = set()

        try:
            job_url = self._build_job_url(job_name, location)
            wait = WebDriverWait(self.driver, 10)

            exponential_backoff(lambda: self.driver.get(job_url))
            page_no = 1

            while page_no <= self.max_pages:
                self.logger.debug(f"Processing page {page_no}")
                
                try:
                    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.title")))
                except Exception as e:
                    self.logger.error(f"Failed to load job listings on page {page_no}: {e}")
                    break

                # Collect job URLs
                job_elems = self.driver.find_elements(By.CSS_SELECTOR, "a.title")
                job_hrefs = [a.get_attribute("href") for a in job_elems if a.get_attribute("href")]

                if self.per_page_limit:
                    job_hrefs = job_hrefs[:self.per_page_limit]

                self.logger.info(f"Found {len(job_hrefs)} jobs on page {page_no}")

                # Extract each job
                for job_url in job_hrefs:
                    if job_url in seen_job_urls:
                        self.logger.debug(f"Skipping duplicate: {job_url}")
                        continue
                    
                    seen_job_urls.add(job_url)
                    self._scrape_job(job_url, extracted_data, wait, job_name)

                # Navigate to next page
                if not self._go_to_next_page(page_no):
                    break

                page_no += 1
                time.sleep(random.uniform(self.min_delay, self.max_delay))

        except Exception as e:
            self.logger.error(f"Error during extraction: {e}")
        finally:
            self._close_driver()

        self.logger.info(f"Scraped {len(extracted_data)} jobs for {location or 'all locations'}")
        time.sleep(self.role_delay)
        return extracted_data

    def _scrape_job(self, job_url: str, extracted_data: list, wait, job_name: str) -> None:
        """Scrape details from a single job listing."""
        try:
            self.driver.execute_script("window.open(arguments[0], '_blank');", job_url)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(random.uniform(self.min_delay, self.max_delay))

            page = BeautifulSoup(self.driver.page_source, "html.parser")
            job_data = self._extract_job_details(page, job_url)
            
            if job_data and self._apply_location_filter(job_data.get("Location", "")):
                job_data["Job_Type"] = job_name
                extracted_data.append(job_data)
                self.logger.debug(f"Extracted: {job_data.get('Title', 'Unknown')}")
        except Exception as e:
            self.logger.error(f"Error scraping {job_url}: {e}")
        finally:
            try:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception as e:
                self.logger.debug(f"Error closing tab: {e}")

    def _go_to_next_page(self, current_page: int) -> bool:
        """Navigate to the next page of results."""
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "a.styles_btn-secondary__2AsIP[href*='-jobs-']")
            next_href = next_btn.get_attribute("href")
            if not next_href:
                self.logger.warning(f"No next link on page {current_page}")
                return False
            self.driver.get(next_href)
            return True
        except Exception as e:
            self.logger.debug(f"No next button found: {e}")
            return False

    def get_name(self) -> str:
        """Return extractor name."""
        return "NaukriExtractor"


# Example usage
if __name__ == "__main__":
    
    
    
    
    extractor = NaukriJobExtractor(
        max_pages=2,
        per_page_limit=5,
        min_delay=2,
        max_delay=4,
        locations=['bengaluru', 'mumbai'],
    )
    
    jobs = extractor.extract("python-developer")
    df = pd.DataFrame(jobs)
    print(df.head())