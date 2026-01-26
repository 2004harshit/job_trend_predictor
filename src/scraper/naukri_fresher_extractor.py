# from .base_scraper import JobExtractor
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
# import re
# from typing import List, Optional, Set, Dict
# from ..utils.backoff import exponential_backoff
# import logging
# from ..utils.logger import setup_logging

# setup_logging()


# class FresherJobExtractor(JobExtractor):
#     """
#     Specialized extractor for fresher/entry-level job listings from Naukri.com.
#     Features:
#     - Fresher-specific experience filters (0-1 years)
#     - Multi-location support with validation
#     - Enhanced skill extraction for career guidance
#     - Salary range filtering
#     - Company type classification (Product/Service/Startup)
#     """
    
#     # Supported locations on Naukri
#     SUPPORTED_LOCATIONS = {
#         'delhi', 'bengaluru', 'bangalore', 'mumbai', 'hyderabad', 'pune', 
#         'kolkata', 'chennai', 'ahmedabad', 'jaipur', 'lucknow', 'surat', 
#         'indore', 'chandigarh', 'kochi', 'noida', 'gurgaon', 'gurugram',
#         'nagpur', 'visakhapatnam', 'bhopal', 'coimbatore', 'vadodara'
#     }
    
#     # Fresher-relevant job keywords
#     FRESHER_KEYWORDS = [
#         'fresher', 'trainee', 'intern', 'entry level', 'graduate', 
#         'junior', 'associate', 'beginner', 'apprentice'
#     ]
    
#     # Experience patterns for freshers (0-2 years max)
#     FRESHER_EXP_PATTERNS = [
#         r'0[-\s]?to[-\s]?[0-2]',
#         r'0[-\s]?[-][-\s]?[0-2]',
#         r'fresher',
#         r'0\s*yrs?',
#         r'0\s*years?',
#     ]

#     def __init__(
#         self, 
#         max_pages: int = 3,
#         per_page_limit: Optional[int] = None,
#         min_delay: float = 2, 
#         max_delay: float = 5, 
#         role_delay: float = 10,
#         locations: Optional[List[str]] = None,
#         max_experience_years: int = 1,
#         min_salary: Optional[int] = None,
#         max_salary: Optional[int] = None,
#         logger=None
#     ):
#         """
#         Initialize the Fresher Job Extractor.
        
#         Args:
#             max_pages: Maximum pages to scrape per location
#             per_page_limit: Max jobs per page (None for all)
#             min_delay: Min delay between requests (seconds)
#             max_delay: Max delay between requests (seconds)
#             role_delay: Delay between different job roles (seconds)
#             locations: List of locations to search (e.g., ['bangalore', 'mumbai'])
#             max_experience_years: Max years of experience (default: 1 for freshers)
#             min_salary: Minimum salary filter in LPA (optional)
#             max_salary: Maximum salary filter in LPA (optional)
#             logger: Logger instance
#         """
#         self.max_pages = max_pages
#         self.per_page_limit = per_page_limit
#         self.min_delay = min_delay
#         self.max_delay = max_delay
#         self.role_delay = role_delay
#         self.max_experience_years = max_experience_years
#         self.min_salary = min_salary
#         self.max_salary = max_salary
#         self.driver = None
#         self.service = None
#         self.logger = logger or logging.getLogger("data_collection")
        
#         # Location filtering
#         self.locations = [loc.lower().strip() for loc in (locations or [])]
#         self._validate_locations()

#     def _validate_locations(self) -> None:
#         """Validate and normalize location inputs."""
#         if self.locations:
#             invalid = [loc for loc in self.locations if loc not in self.SUPPORTED_LOCATIONS]
#             if invalid:
#                 self.logger.warning(
#                     f"Invalid locations removed: {invalid}. "
#                     f"Supported locations: {sorted(self.SUPPORTED_LOCATIONS)}"
#                 )
#             self.locations = [loc for loc in self.locations if loc in self.SUPPORTED_LOCATIONS]
            
#             # Normalize bangalore -> bengaluru
#             self.locations = ['bengaluru' if loc == 'bangalore' else loc for loc in self.locations]
            
#             if not self.locations:
#                 self.logger.error("No valid locations provided. Please use supported locations.")
#                 raise ValueError("No valid locations specified")

#     def _setup_driver(self) -> None:
#         """Initialize Selenium WebDriver with anti-detection measures."""
#         try:
#             options = webdriver.ChromeOptions()
#             options.add_argument("--headless")
#             options.add_argument("--no-sandbox")
#             options.add_argument("--disable-dev-shm-usage")
#             options.add_argument("--window-size=1920,1080")
#             options.add_argument("--disable-gpu")
#             options.add_argument("--disable-extensions")
            
#             # Anti-detection
#             options.add_argument(
#                 "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#             )
#             options.add_argument("--disable-blink-features=AutomationControlled")
#             options.add_experimental_option("excludeSwitches", ["enable-automation"])
#             options.add_experimental_option("useAutomationExtension", False)

#             self.service = Service(ChromeDriverManager().install())
#             self.driver = webdriver.Chrome(service=self.service, options=options)
#             self.driver.execute_script(
#                 "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
#             )
#             self.logger.info("WebDriver initialized successfully")
#         except Exception as e:
#             self.logger.error(f"Failed to initialize WebDriver: {e}")
#             raise

#     def _close_driver(self) -> None:
#         """Safely close WebDriver and cleanup."""
#         try:
#             if self.driver:
#                 self.driver.quit()
#                 self.logger.info("WebDriver closed successfully")
#         except Exception as e:
#             self.logger.error(f"Error closing WebDriver: {e}")

#     def _build_fresher_job_url(self, job_role: str, location: Optional[str] = None) -> str:
#         """
#         Build Naukri URL specifically for fresher jobs.
        
#         Args:
#             job_role: Job role/keyword (e.g., 'python-developer', 'data-analyst')
#             location: Location filter
            
#         Returns:
#             Complete Naukri URL with fresher filters
#         """
#         # Normalize job role
#         job_role_normalized = job_role.lower().strip().replace(' ', '-')
        
#         # Base URL with fresher keyword
#         base_url = f"https://www.naukri.com/{job_role_normalized}-jobs"
        
#         # Add location if specified
#         if location and location in self.SUPPORTED_LOCATIONS:
#             base_url += f"-in-{location}"
        
#         # Add experience filter for freshers (0-1 years)
#         # Note: Naukri URL params may vary, adjust as needed
#         base_url += f"?experience={self.max_experience_years}"
        
#         return base_url

#     def _is_fresher_job(self, experience_text: str, job_title: str, description: str) -> bool:
#         """
#         Determine if a job is suitable for freshers.
        
#         Args:
#             experience_text: Experience requirement from job listing
#             job_title: Job title
#             description: Job description
            
#         Returns:
#             True if job is fresher-appropriate
#         """
#         if not experience_text or experience_text == "NA":
#             return False
        
#         experience_lower = experience_text.lower()
#         title_lower = job_title.lower()
#         desc_lower = description.lower()
        
#         # Check for fresher keywords in title or description
#         if any(keyword in title_lower or keyword in desc_lower for keyword in self.FRESHER_KEYWORDS):
#             return True
        
#         # Check experience patterns
#         for pattern in self.FRESHER_EXP_PATTERNS:
#             if re.search(pattern, experience_lower, re.IGNORECASE):
#                 return True
        
#         # Extract numeric experience
#         exp_match = re.search(r'(\d+)\s*[-to]*\s*(\d+)?\s*yrs?', experience_lower)
#         if exp_match:
#             min_exp = int(exp_match.group(1))
#             max_exp = int(exp_match.group(2)) if exp_match.group(2) else min_exp
            
#             # Accept if minimum experience is <= max_experience_years
#             if min_exp <= self.max_experience_years:
#                 return True
        
#         return False

#     def _extract_salary_range(self, salary_text: str) -> Dict[str, Optional[float]]:
#         """
#         Extract and parse salary information.
        
#         Args:
#             salary_text: Raw salary text
            
#         Returns:
#             Dict with min_salary, max_salary, currency
#         """
#         result = {"min_salary": None, "max_salary": None, "currency": "INR"}
        
#         if not salary_text or salary_text == "NA" or "not disclosed" in salary_text.lower():
#             return result
        
#         try:
#             # Pattern: "3-5 Lacs P.A." or "₹3,00,000 - ₹5,00,000"
#             lpa_match = re.search(r'(\d+\.?\d*)\s*[-to]+\s*(\d+\.?\d*)\s*lacs?', salary_text, re.IGNORECASE)
#             if lpa_match:
#                 result["min_salary"] = float(lpa_match.group(1))
#                 result["max_salary"] = float(lpa_match.group(2))
#                 return result
            
#             # Pattern: "Up to 5 Lacs"
#             upto_match = re.search(r'up\s*to\s*(\d+\.?\d*)\s*lacs?', salary_text, re.IGNORECASE)
#             if upto_match:
#                 result["max_salary"] = float(upto_match.group(1))
#                 return result
            
#         except Exception as e:
#             self.logger.debug(f"Error parsing salary '{salary_text}': {e}")
        
#         return result

#     def _filter_by_salary(self, salary_dict: Dict) -> bool:
#         """Check if job meets salary criteria."""
#         if self.min_salary is None and self.max_salary is None:
#             return True
        
#         min_sal = salary_dict.get("min_salary")
#         max_sal = salary_dict.get("max_salary")
        
#         if self.min_salary and max_sal and max_sal < self.min_salary:
#             return False
        
#         if self.max_salary and min_sal and min_sal > self.max_salary:
#             return False
        
#         return True

#     def _classify_company_type(self, company_name: str, description: str) -> str:
#         """
#         Classify company as Product/Service/Startup.
        
#         Args:
#             company_name: Company name
#             description: Job description
            
#         Returns:
#             Company type classification
#         """
#         company_lower = company_name.lower()
#         desc_lower = description.lower()
        
#         # Service-based indicators
#         service_companies = ['tcs', 'infosys', 'wipro', 'cognizant', 'accenture', 'capgemini', 'hcl']
#         if any(svc in company_lower for svc in service_companies):
#             return "Service-Based"
        
#         # Startup indicators
#         startup_keywords = ['startup', 'series a', 'series b', 'funded', 'venture']
#         if any(kw in desc_lower for kw in startup_keywords):
#             return "Startup"
        
#         # Product-based indicators (FAANG, etc.)
#         product_companies = ['google', 'microsoft', 'amazon', 'facebook', 'meta', 'apple', 
#                            'adobe', 'oracle', 'salesforce', 'netflix']
#         if any(prod in company_lower for prod in product_companies):
#             return "Product-Based (MNC)"
        
#         return "Unknown"

#     def _extract_timestamps(self, page: BeautifulSoup) -> tuple:
#         """Extract job posting and application deadline dates."""
#         posted_date = "NA"
#         last_apply_date = "NA"
        
#         try:
#             # Primary selector - stats section
#             jd_stats = page.find("div", class_="styles_jhc__jd-stats__KrId0")
#             if jd_stats:
#                 stat_spans = jd_stats.find_all("span", class_="styles_jhc__stat__PgY67")
#                 for span in stat_spans:
#                     label = span.find("label")
#                     value_span = span.find("span")
                    
#                     if label and value_span:
#                         label_text = label.get_text(strip=True).lower()
#                         value_text = value_span.get_text(strip=True)
                        
#                         if "posted" in label_text:
#                             posted_date = value_text
            
#             # Alternative selector
#             if posted_date == "NA":
#                 posted_div = page.find("div", class_="styles_SJC__posted-date__eiY9o")
#                 if posted_div:
#                     span = posted_div.find("span")
#                     if span:
#                         posted_date = span.get_text(strip=True)
            
#             # Look for application deadline
#             page_text = page.get_text()
#             date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', page_text)
#             if date_match:
#                 last_apply_date = date_match.group(1)
        
#         except Exception as e:
#             self.logger.debug(f"Error extracting timestamps: {e}")
        
#         return posted_date, last_apply_date

#     def _extract_applicant_stats(self, page: BeautifulSoup) -> Dict[str, Optional[int]]:
#         """
#         Extract number of openings and applicants.
        
#         Returns:
#             Dict with num_openings and num_applicants
#         """
#         stats = {"num_openings": None, "num_applicants": None}
        
#         try:
#             # Strategy 1: Look in job stats section
#             jd_stats = page.find("div", class_="styles_jhc__jd-stats__KrId0")
#             if jd_stats:
#                 stat_spans = jd_stats.find_all("span", class_="styles_jhc__stat__PgY67")
#                 for span in stat_spans:
#                     label = span.find("label")
#                     value_span = span.find("span")
                    
#                     if label and value_span:
#                         label_text = label.get_text(strip=True).lower()
#                         value_text = value_span.get_text(strip=True)
                        
#                         # Extract number of openings
#                         if "opening" in label_text or "vacancy" in label_text or "vacancies" in label_text:
#                             opening_match = re.search(r'(\d+)', value_text)
#                             if opening_match:
#                                 stats["num_openings"] = int(opening_match.group(1))
                        
#                         # Extract number of applicants
#                         if "applicant" in label_text or "applied" in label_text:
#                             # Handle formats like "100+ applicants" or "50 applicants"
#                             applicant_match = re.search(r'(\d+)', value_text.replace('+', '').replace(',', ''))
#                             if applicant_match:
#                                 stats["num_applicants"] = int(applicant_match.group(1))
            
#             # Strategy 2: Look for applicants in other sections
#             if stats["num_applicants"] is None:
#                 # Check for applicant count in different locations
#                 applicant_elem = page.find("div", class_=re.compile(r"applicant|applied", re.I))
#                 if applicant_elem:
#                     applicant_text = applicant_elem.get_text(strip=True)
#                     applicant_match = re.search(r'(\d+)', applicant_text.replace('+', '').replace(',', ''))
#                     if applicant_match:
#                         stats["num_applicants"] = int(applicant_match.group(1))
            
#             # Strategy 3: Search entire page text for applicant info
#             if stats["num_applicants"] is None:
#                 page_text = page.get_text()
#                 # Pattern: "150 applicants" or "100+ people applied"
#                 applicant_pattern = re.search(r'(\d+)\+?\s*(?:applicants?|people applied)', page_text, re.I)
#                 if applicant_pattern:
#                     stats["num_applicants"] = int(applicant_pattern.group(1))
            
#         except Exception as e:
#             self.logger.debug(f"Error extracting applicant stats: {e}")
        
#         return stats

#     def _extract_job_details(self, page: BeautifulSoup, job_url: str) -> Optional[dict]:
#         """
#         Extract comprehensive job details for fresher positions.
        
#         Returns:
#             Detailed job data dictionary or None
#         """
#         try:
#             # Core fields
#             title = page.find("h1", class_="styles_jd-header-title__rZwM1")
#             title = title.get_text(strip=True) if title else "NA"

#             comp_elem = page.find("a", href=lambda x: x and "jobs-careers" in x)
#             company = comp_elem.get_text(strip=True) if comp_elem else "NA"

#             exp_elem = page.find("div", class_="styles_jhc__exp__k_giM")
#             experience = exp_elem.find("span").get_text(strip=True) if exp_elem and exp_elem.find("span") else "NA"

#             salary_elem = page.find("div", class_="styles_jhc__salary__jdfEC")
#             salary_text = salary_elem.find("span").get_text(strip=True) if salary_elem and salary_elem.find("span") else "NA"

#             loc_elem = page.find("span", class_="styles_jhc__location__W_pVs")
#             location = loc_elem.get_text(strip=True) if loc_elem else "NA"

#             # Timestamps
#             posted_date, last_apply_date = self._extract_timestamps(page)
            
#             # Applicant statistics
#             applicant_stats = self._extract_applicant_stats(page)

#             # Education
#             edu_elem = page.find("div", class_="styles_education__KXFkO")
#             education = edu_elem.get_text(strip=True) if edu_elem else "Not Specified"

#             # Skills
#             star_skills, normal_skills = self._extract_skills(page)

#             # Job description
#             jd_elem = page.find("div", class_="styles_JDC__dang-inner-html__h0K4t")
#             job_description = jd_elem.get_text(" ", strip=True) if jd_elem else "NA"

#             # Additional details
#             other_details = self._extract_other_details(page)

#             # Parse salary
#             salary_dict = self._extract_salary_range(salary_text)

#             # Classify company
#             company_type = self._classify_company_type(company, job_description)

#             # Check if fresher-appropriate
#             is_fresher = self._is_fresher_job(experience, title, job_description)

#             return {
#                 "Title": title,
#                 "Company": company,
#                 "Company_Type": company_type,
#                 "Experience_Required": experience,
#                 "Salary_Text": salary_text,
#                 "Min_Salary_LPA": salary_dict["min_salary"],
#                 "Max_Salary_LPA": salary_dict["max_salary"],
#                 "Location": location,
#                 "Education": education,
#                 "Key_Skills": star_skills,
#                 "Additional_Skills": normal_skills,
#                 "Total_Skills_Required": len(star_skills) + len(normal_skills),
#                 "Num_Openings": applicant_stats["num_openings"],
#                 "Num_Applicants": applicant_stats["num_applicants"],
#                 "Posted_Date": posted_date,
#                 "Last_Apply_Date": last_apply_date,
#                 "Is_Fresher_Friendly": is_fresher,
#                 **other_details,
#                 "Description": job_description,
#                 "Job_URL": job_url,
#                 "Scraped_At": datetime.datetime.now().isoformat()
#             }
#         except Exception as e:
#             self.logger.error(f"Error extracting job details from {job_url}: {e}")
#             return None

#     def _extract_other_details(self, page: BeautifulSoup) -> dict:
#         """Extract miscellaneous job details (role category, industry, etc.)."""
#         details = {}
#         try:
#             details_section = page.find("div", class_="styles_other-details__oEN4O")
#             if details_section:
#                 for div in details_section.find_all("div", class_="styles_details__Y424J"):
#                     label = div.find("label")
#                     span = div.find("span")
#                     if label and span:
#                         key = label.get_text(strip=True).replace(":", "").replace(" ", "_")
#                         value = span.get_text(" ", strip=True)
#                         details[key] = value
#         except Exception as e:
#             self.logger.debug(f"Error extracting other details: {e}")
#         return details

#     def _extract_skills(self, page: BeautifulSoup) -> tuple:
#         """
#         Extract and categorize skills.
        
#         Returns:
#             Tuple of (key_skills, additional_skills)
#         """
#         key_skills, additional_skills = [], []
#         try:
#             skills_section = page.find("div", class_="styles_key-skill__GIPn_")
#             if skills_section:
#                 for a in skills_section.find_all("a", class_="styles_chip__7YCfG"):
#                     skill_span = a.find("span")
#                     skill_name = skill_span.get_text(strip=True) if skill_span else None
                    
#                     if skill_name:
#                         # Star icon indicates key/primary skill
#                         if a.find("i", class_="ni-icon-jd-save"):
#                             key_skills.append(skill_name)
#                         else:
#                             additional_skills.append(skill_name)
#         except Exception as e:
#             self.logger.debug(f"Error extracting skills: {e}")
        
#         return key_skills, additional_skills

#     def _apply_location_filter(self, job_location: str) -> bool:
#         """Check if job location matches filter criteria."""
#         if not self.locations:
#             return True
        
#         location_lower = job_location.lower()
#         return any(loc in location_lower for loc in self.locations)

#     def extract(self, job_roles: List[str], locations: Optional[List[str]] = None) -> List[dict]:
#         """
#         Extract fresher jobs for multiple roles and locations.
        
#         Args:
#             job_roles: List of job roles to search (e.g., ['python-developer', 'data-analyst'])
#             locations: Override instance locations
            
#         Returns:
#             List of extracted job dictionaries
#         """
#         active_locations = locations or self.locations or [None]
#         all_jobs = []

#         for role in job_roles:
#             self.logger.info(f"\n{'='*60}")
#             self.logger.info(f"Extracting fresher jobs for role: {role}")
#             self.logger.info(f"{'='*60}")
            
#             role_jobs = self._extract_for_role(role, active_locations)
#             all_jobs.extend(role_jobs)

#         # Filter for fresher jobs and salary criteria
#         fresher_jobs = [
#             job for job in all_jobs 
#             if job.get("Is_Fresher_Friendly", False) and 
#             self._filter_by_salary({
#                 "min_salary": job.get("Min_Salary_LPA"),
#                 "max_salary": job.get("Max_Salary_LPA")
#             })
#         ]

#         self.logger.info(f"\n{'='*60}")
#         self.logger.info(f"EXTRACTION COMPLETE")
#         self.logger.info(f"Total jobs scraped: {len(all_jobs)}")
#         self.logger.info(f"Fresher-friendly jobs: {len(fresher_jobs)}")
#         self.logger.info(f"{'='*60}\n")

#         return fresher_jobs

#     def _extract_for_role(self, job_role: str, locations: List[Optional[str]]) -> List[dict]:
#         """Extract jobs for a specific role across multiple locations."""
#         role_jobs = []
        
#         for location in locations:
#             self.logger.info(f"Searching in: {location or 'All Locations'}")
#             location_jobs = self._extract_for_location(job_role, location)
#             role_jobs.extend(location_jobs)
        
#         return role_jobs

#     def _extract_for_location(self, job_role: str, location: Optional[str]) -> List[dict]:
#         """Extract jobs for specific role and location."""
#         self._setup_driver()
#         extracted_data = []
#         seen_urls: Set[str] = set()

#         try:
#             url = self._build_fresher_job_url(job_role, location)
#             self.logger.debug(f"URL: {url}")
            
#             wait = WebDriverWait(self.driver, 15)
#             exponential_backoff(lambda: self.driver.get(url))
            
#             page_no = 1

#             while page_no <= self.max_pages:
#                 self.logger.debug(f"    Page {page_no}/{self.max_pages}")
                
#                 try:
#                     wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.title")))
#                 except Exception as e:
#                     self.logger.warning(f"No jobs found on page {page_no}: {e}")
#                     break

#                 # Collect job URLs
#                 job_elems = self.driver.find_elements(By.CSS_SELECTOR, "a.title")
#                 job_urls = [elem.get_attribute("href") for elem in job_elems if elem.get_attribute("href")]

#                 if self.per_page_limit:
#                     job_urls = job_urls[:self.per_page_limit]

#                 self.logger.debug(f"    Found {len(job_urls)} job listings")

#                 # Extract each job
#                 for job_url in job_urls:
#                     if job_url in seen_urls:
#                         continue
                    
#                     seen_urls.add(job_url)
#                     job_data = self._scrape_single_job(job_url, wait, job_role)
                    
#                     if job_data and self._apply_location_filter(job_data.get("Location", "")):
#                         extracted_data.append(job_data)

#                 # Navigate to next page
#                 if not self._go_to_next_page(page_no):
#                     break

#                 page_no += 1
#                 time.sleep(random.uniform(self.min_delay, self.max_delay))

#         except Exception as e:
#             self.logger.error(f"Error during extraction: {e}")
#         finally:
#             self._close_driver()

#         self.logger.info(f"     Extracted {len(extracted_data)} jobs")
#         time.sleep(self.role_delay)
#         return extracted_data

#     def _scrape_single_job(self, job_url: str, wait, job_role: str) -> Optional[dict]:
#         """Scrape details from a single job listing."""
#         try:
#             self.driver.execute_script("window.open(arguments[0], '_blank');", job_url)
#             self.driver.switch_to.window(self.driver.window_handles[-1])
#             time.sleep(random.uniform(self.min_delay, self.max_delay))

#             page = BeautifulSoup(self.driver.page_source, "html.parser")
#             job_data = self._extract_job_details(page, job_url)
            
#             if job_data:
#                 job_data["Job_Role_Searched"] = job_role
#                 return job_data
                
#         except Exception as e:
#             self.logger.error(f"Error scraping {job_url}: {e}")
#         finally:
#             try:
#                 self.driver.close()
#                 self.driver.switch_to.window(self.driver.window_handles[0])
#             except Exception as e:
#                 self.logger.debug(f"Error closing tab: {e}")
        
#         return None

#     def _go_to_next_page(self, current_page: int) -> bool:
#         """Navigate to next page of results."""
#         try:
#             next_btn = self.driver.find_element(By.CSS_SELECTOR, "a.styles_btn-secondary__2AsIP")
#             next_href = next_btn.get_attribute("href")
            
#             if not next_href or f"page-{current_page+1}" not in next_href:
#                 return False
            
#             self.driver.get(next_href)
#             return True
#         except Exception:
#             return False

#     def get_name(self) -> str:
#         """Return extractor identifier."""
#         return "FresherJobExtractor"


# # Example usage
# if __name__ == "__main__":
#     # Initialize extractor
#     extractor = FresherJobExtractor(
#         max_pages=2,
#         per_page_limit=3,
#         min_delay=2,
#         max_delay=4,
#         locations=['bengaluru', 'mumbai', 'jaipur'],
#         max_experience_years=1,
#         min_salary=3,  # Minimum 3 LPA
#         max_salary=8   # Maximum 8 LPA
#     )
    
#     # Extract jobs for multiple roles
#     job_roles = [
#         'python-developer',
#         'data-analyst',
#         'software-engineer',
#         'full-stack-developer'
#     ]
    
#     # Returns list of dictionaries
#     fresher_jobs = extractor.extract(job_roles)
    
#     if fresher_jobs:
#         print(f"\n✓ Successfully extracted {len(fresher_jobs)} fresher jobs!")
        
#         # Display sample
#         df = pd.DataFrame(fresher_jobs)
#         print("\nSample jobs:")
#         print(df[['Title', 'Company', 'Location', 'Experience_Required', 
#                   'Num_Openings', 'Num_Applicants', 'Salary_Text']].head())
        
#         # Pass to storage handler
#         # storage_handler.save(fresher_jobs)
#     else:
#         print("No fresher jobs found matching criteria.")


from .base_scraper import JobExtractor
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
import re
from typing import List, Optional, Set, Dict
from ..utils.backoff import exponential_backoff
import logging
from ..utils.logger import setup_logging

setup_logging()


class FresherJobExtractor(JobExtractor):
    """
    Specialized extractor for fresher/entry-level job listings from Naukri.com.
    
    Returns standardized fields:
    - Title, Company, Experience, Salary, Location, Education
    - Star_Skills, Normal_Skills, Posted_Date, Last_Apply_Date
    - Role, Industry Type, Department, Employment Type, Role Category
    - Description, Job_URL, Scraped_At, Job_Type
    - num_openings, num_applicants
    """
    
    # Supported locations on Naukri
    SUPPORTED_LOCATIONS = {
        'delhi', 'bengaluru', 'bangalore', 'mumbai', 'hyderabad', 'pune', 
        'kolkata', 'chennai', 'ahmedabad', 'jaipur', 'lucknow', 'surat', 
        'indore', 'chandigarh', 'kochi', 'noida', 'gurgaon', 'gurugram',
        'nagpur', 'visakhapatnam', 'bhopal', 'coimbatore', 'vadodara'
    }
    
    # Fresher-relevant job keywords
    FRESHER_KEYWORDS = [
        'fresher', 'trainee', 'intern', 'entry level', 'graduate', 
        'junior', 'associate', 'beginner', 'apprentice'
    ]
    
    # Experience patterns for freshers (0-2 years max)
    FRESHER_EXP_PATTERNS = [
        r'0[-\s]?to[-\s]?[0-2]',
        r'0[-\s]?[-][-\s]?[0-2]',
        r'fresher',
        r'0\s*yrs?',
        r'0\s*years?',
    ]

    def __init__(
        self, 
        max_pages: int = 3,
        per_page_limit: Optional[int] = None,
        min_delay: float = 2, 
        max_delay: float = 5, 
        role_delay: float = 10,
        locations: Optional[List[str]] = None,
        max_experience_years: int = 1,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        logger=None
    ):
        """
        Initialize the Fresher Job Extractor.
        
        Args:
            max_pages: Maximum pages to scrape per location
            per_page_limit: Max jobs per page (None for all)
            min_delay: Min delay between requests (seconds)
            max_delay: Max delay between requests (seconds)
            role_delay: Delay between different job roles (seconds)
            locations: List of locations to search (e.g., ['bangalore', 'mumbai'])
            max_experience_years: Max years of experience (default: 1 for freshers)
            min_salary: Minimum salary filter in LPA (optional)
            max_salary: Maximum salary filter in LPA (optional)
            logger: Logger instance
        """
        self.max_pages = max_pages
        self.per_page_limit = per_page_limit
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.role_delay = role_delay
        self.max_experience_years = max_experience_years
        self.min_salary = min_salary
        self.max_salary = max_salary
        self.driver = None
        self.service = None
        self.logger = logger or logging.getLogger("data_collection")
        
        # Location filtering
        self.locations = [loc.lower().strip() for loc in (locations or [])]
        self._validate_locations()

    def _validate_locations(self) -> None:
        """Validate and normalize location inputs."""
        if self.locations:
            invalid = [loc for loc in self.locations if loc not in self.SUPPORTED_LOCATIONS]
            if invalid:
                self.logger.warning(
                    f"Invalid locations removed: {invalid}. "
                    f"Supported locations: {sorted(self.SUPPORTED_LOCATIONS)}"
                )
            self.locations = [loc for loc in self.locations if loc in self.SUPPORTED_LOCATIONS]
            
            # Normalize bangalore -> bengaluru
            self.locations = ['bengaluru' if loc == 'bangalore' else loc for loc in self.locations]
            
            if not self.locations:
                self.logger.error("No valid locations provided. Please use supported locations.")
                raise ValueError("No valid locations specified")

    def _setup_driver(self) -> None:
        """Initialize Selenium WebDriver with anti-detection measures."""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            
            # Anti-detection
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            self.service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=self.service, options=options)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            self.logger.info("WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def _close_driver(self) -> None:
        """Safely close WebDriver and cleanup."""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("WebDriver closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing WebDriver: {e}")

    def _build_fresher_job_url(self, job_role: str, location: Optional[str] = None) -> str:
        """
        Build Naukri URL specifically for fresher jobs.
        
        Args:
            job_role: Job role/keyword (e.g., 'python-developer', 'data-analyst')
            location: Location filter
            
        Returns:
            Complete Naukri URL with fresher filters
        """
        # Normalize job role
        job_role_normalized = job_role.lower().strip().replace(' ', '-')
        
        # Base URL
        base_url = f"https://www.naukri.com/{job_role_normalized}-jobs"
        
        # Add location if specified
        if location and location in self.SUPPORTED_LOCATIONS:
            base_url += f"-in-{location}"
        
        # Add experience filter for freshers (0-1 years)
        base_url += f"?experience={self.max_experience_years}"
        
        return base_url

    def _is_fresher_job(self, experience_text: str, job_title: str, description: str) -> bool:
        """
        Determine if a job is suitable for freshers.
        
        Args:
            experience_text: Experience requirement from job listing
            job_title: Job title
            description: Job description
            
        Returns:
            True if job is fresher-appropriate
        """
        if not experience_text or experience_text == "NA":
            return False
        
        experience_lower = experience_text.lower()
        title_lower = job_title.lower()
        desc_lower = description.lower()
        
        # Check for fresher keywords in title or description
        if any(keyword in title_lower or keyword in desc_lower for keyword in self.FRESHER_KEYWORDS):
            return True
        
        # Check experience patterns
        for pattern in self.FRESHER_EXP_PATTERNS:
            if re.search(pattern, experience_lower, re.IGNORECASE):
                return True
        
        # Extract numeric experience
        exp_match = re.search(r'(\d+)\s*[-to]*\s*(\d+)?\s*yrs?', experience_lower)
        if exp_match:
            min_exp = int(exp_match.group(1))
            max_exp = int(exp_match.group(2)) if exp_match.group(2) else min_exp
            
            # Accept if minimum experience is <= max_experience_years
            if min_exp <= self.max_experience_years:
                return True
        
        return False

    def _extract_salary_range(self, salary_text: str) -> Dict[str, Optional[float]]:
        """
        Extract and parse salary information.
        
        Args:
            salary_text: Raw salary text
            
        Returns:
            Dict with min_salary, max_salary, currency
        """
        result = {"min_salary": None, "max_salary": None, "currency": "INR"}
        
        if not salary_text or salary_text == "NA" or "not disclosed" in salary_text.lower():
            return result
        
        try:
            # Pattern: "3-5 Lacs P.A." or "₹3,00,000 - ₹5,00,000"
            lpa_match = re.search(r'(\d+\.?\d*)\s*[-to]+\s*(\d+\.?\d*)\s*lacs?', salary_text, re.IGNORECASE)
            if lpa_match:
                result["min_salary"] = float(lpa_match.group(1))
                result["max_salary"] = float(lpa_match.group(2))
                return result
            
            # Pattern: "Up to 5 Lacs"
            upto_match = re.search(r'up\s*to\s*(\d+\.?\d*)\s*lacs?', salary_text, re.IGNORECASE)
            if upto_match:
                result["max_salary"] = float(upto_match.group(1))
                return result
            
        except Exception as e:
            self.logger.debug(f"Error parsing salary '{salary_text}': {e}")
        
        return result

    def _filter_by_salary(self, salary_dict: Dict) -> bool:
        """Check if job meets salary criteria."""
        if self.min_salary is None and self.max_salary is None:
            return True
        
        min_sal = salary_dict.get("min_salary")
        max_sal = salary_dict.get("max_salary")
        
        if self.min_salary and max_sal and max_sal < self.min_salary:
            return False
        
        if self.max_salary and min_sal and min_sal > self.max_salary:
            return False
        
        return True

    def _extract_timestamps(self, page: BeautifulSoup) -> tuple:
        """Extract job posting and application deadline dates."""
        posted_date = "NA"
        last_apply_date = "NA"
        
        try:
            # Primary selector - stats section
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
            
            # Alternative selector
            if posted_date == "NA":
                posted_div = page.find("div", class_="styles_SJC__posted-date__eiY9o")
                if posted_div:
                    span = posted_div.find("span")
                    if span:
                        posted_date = span.get_text(strip=True)
            
            # Look for application deadline
            page_text = page.get_text()
            date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', page_text)
            if date_match:
                last_apply_date = date_match.group(1)
        
        except Exception as e:
            self.logger.debug(f"Error extracting timestamps: {e}")
        
        return posted_date, last_apply_date

    def _extract_applicant_stats(self, page: BeautifulSoup) -> Dict[str, Optional[int]]:
        """
        Extract number of openings and applicants.
        
        Returns:
            Dict with num_openings and num_applicants
        """
        stats = {"num_openings": None, "num_applicants": None}
        
        try:
            # Strategy 1: Look in job stats section
            jd_stats = page.find("div", class_="styles_jhc__jd-stats__KrId0")
            if jd_stats:
                stat_spans = jd_stats.find_all("span", class_="styles_jhc__stat__PgY67")
                for span in stat_spans:
                    label = span.find("label")
                    value_span = span.find("span")
                    
                    if label and value_span:
                        label_text = label.get_text(strip=True).lower()
                        value_text = value_span.get_text(strip=True)
                        
                        # Extract number of openings
                        if "opening" in label_text or "vacancy" in label_text or "vacancies" in label_text:
                            opening_match = re.search(r'(\d+)', value_text)
                            if opening_match:
                                stats["num_openings"] = int(opening_match.group(1))
                        
                        # Extract number of applicants
                        if "applicant" in label_text or "applied" in label_text:
                            # Handle formats like "100+ applicants" or "50 applicants"
                            applicant_match = re.search(r'(\d+)', value_text.replace('+', '').replace(',', ''))
                            if applicant_match:
                                stats["num_applicants"] = int(applicant_match.group(1))
            
            # Strategy 2: Look for applicants in other sections
            if stats["num_applicants"] is None:
                # Check for applicant count in different locations
                applicant_elem = page.find("div", class_=re.compile(r"applicant|applied", re.I))
                if applicant_elem:
                    applicant_text = applicant_elem.get_text(strip=True)
                    applicant_match = re.search(r'(\d+)', applicant_text.replace('+', '').replace(',', ''))
                    if applicant_match:
                        stats["num_applicants"] = int(applicant_match.group(1))
            
            # Strategy 3: Search entire page text for applicant info
            if stats["num_applicants"] is None:
                page_text = page.get_text()
                # Pattern: "150 applicants" or "100+ people applied"
                applicant_pattern = re.search(r'(\d+)\+?\s*(?:applicants?|people applied)', page_text, re.I)
                if applicant_pattern:
                    stats["num_applicants"] = int(applicant_pattern.group(1))
            
        except Exception as e:
            self.logger.debug(f"Error extracting applicant stats: {e}")
        
        return stats

    def _extract_structured_details(self, page: BeautifulSoup) -> Dict[str, str]:
        """
        Extract structured job details (Role, Industry Type, Department, etc.).
        Maps Naukri's field names to standardized field names.
        
        Returns:
            Dict with Role, Industry_Type, Department, Employment_Type, Role_Category
        """
        details = {
            "Role": "NA",
            "Industry_Type": "NA", 
            "Department": "NA",
            "Employment_Type": "NA",
            "Role_Category": "NA"
        }
        
        # Mapping from Naukri labels to our standardized fields
        field_mapping = {
            "role": "Role",
            "industry": "Industry_Type",
            "industry type": "Industry_Type",
            "functional area": "Department",
            "department": "Department",
            "employment type": "Employment_Type",
            "role category": "Role_Category",
            "job type": "Employment_Type"
        }
        
        try:
            details_section = page.find("div", class_="styles_other-details__oEN4O")
            if details_section:
                for div in details_section.find_all("div", class_="styles_details__Y424J"):
                    label = div.find("label")
                    span = div.find("span")
                    
                    if label and span:
                        label_text = label.get_text(strip=True).replace(":", "").lower()
                        value_text = span.get_text(" ", strip=True)
                        
                        # Map to standardized field name
                        for naukri_label, std_field in field_mapping.items():
                            if naukri_label in label_text:
                                details[std_field] = value_text
                                break
        
        except Exception as e:
            self.logger.debug(f"Error extracting structured details: {e}")
        
        return details

    def _extract_skills(self, page: BeautifulSoup) -> tuple:
        """
        Extract and categorize skills.
        
        Returns:
            Tuple of (star_skills_list, normal_skills_list)
        """
        star_skills = []
        normal_skills = []
        
        try:
            skills_section = page.find("div", class_="styles_key-skill__GIPn_")
            if skills_section:
                for a in skills_section.find_all("a", class_="styles_chip__7YCfG"):
                    skill_span = a.find("span")
                    skill_name = skill_span.get_text(strip=True) if skill_span else None
                    
                    if skill_name:
                        # Star icon indicates key/primary skill
                        if a.find("i", class_="ni-icon-jd-save"):
                            star_skills.append(skill_name)
                        else:
                            normal_skills.append(skill_name)
        except Exception as e:
            self.logger.debug(f"Error extracting skills: {e}")
        
        return star_skills, normal_skills

    def _extract_job_details(self, page: BeautifulSoup, job_url: str) -> Optional[dict]:
        """
        Extract comprehensive job details with standardized field names.
        
        Returns standardized fields:
        - Title, Company, Experience, Salary, Location, Education
        - Star_Skills, Normal_Skills, Posted_Date, Last_Apply_Date
        - Role, Industry Type, Department, Employment Type, Role Category
        - Description, Job_URL, Scraped_At, Job_Type
        - num_openings, num_applicants
        """
        try:
            # Core fields
            title_elem = page.find("h1", class_="styles_jd-header-title__rZwM1")
            title = title_elem.get_text(strip=True) if title_elem else "NA"

            company_elem = page.find("a", href=lambda x: x and "jobs-careers" in x)
            company = company_elem.get_text(strip=True) if company_elem else "NA"

            exp_elem = page.find("div", class_="styles_jhc__exp__k_giM")
            experience = exp_elem.find("span").get_text(strip=True) if exp_elem and exp_elem.find("span") else "NA"

            salary_elem = page.find("div", class_="styles_jhc__salary__jdfEC")
            salary = salary_elem.find("span").get_text(strip=True) if salary_elem and salary_elem.find("span") else "NA"

            loc_elem = page.find("span", class_="styles_jhc__location__W_pVs")
            location = loc_elem.get_text(strip=True) if loc_elem else "NA"

            # Education
            edu_elem = page.find("div", class_="styles_education__KXFkO")
            education = edu_elem.get_text(strip=True) if edu_elem else "NA"

            # Skills - returns lists
            star_skills, normal_skills = self._extract_skills(page)

            # Timestamps
            posted_date, last_apply_date = self._extract_timestamps(page)
            
            # Applicant statistics
            applicant_stats = self._extract_applicant_stats(page)

            # Structured details (Role, Industry Type, Department, etc.)
            structured_details = self._extract_structured_details(page)

            # Job description
            jd_elem = page.find("div", class_="styles_JDC__dang-inner-html__h0K4t")
            description = jd_elem.get_text(" ", strip=True) if jd_elem else "NA"

            # Return standardized dictionary
            return {
                "Title": title,
                "Company": company,
                "Experience": experience,
                "Salary": salary,
                "Location": location,
                "Education": education,
                "Star_Skills": star_skills,
                "Normal_Skills": normal_skills,
                "Posted_Date": posted_date,
                "Last_Apply_Date": last_apply_date,
                "Role": structured_details["Role"],
                "Industry_Type": structured_details["Industry_Type"],
                "Department": structured_details["Department"],
                "Employment_Type": structured_details["Employment_Type"],
                "Role_Category": structured_details["Role_Category"],
                "Description": description,
                "Job_URL": job_url,
                "Scraped_At": datetime.datetime.now().isoformat(),
                "Job_Type": "Fresher",  # Will be overridden with actual job role searched
                "num_openings": applicant_stats["num_openings"],
                "num_applicants": applicant_stats["num_applicants"]
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting job details from {job_url}: {e}")
            return None

    def _apply_location_filter(self, job_location: str) -> bool:
        """Check if job location matches filter criteria."""
        if not self.locations:
            return True
        
        location_lower = job_location.lower()
        return any(loc in location_lower for loc in self.locations)

    def extract(self, job_roles: List[str], locations: Optional[List[str]] = None) -> List[dict]:
        """
        Extract fresher jobs for multiple roles and locations.
        
        Args:
            job_roles: List of job roles to search (e.g., ['python-developer', 'data-analyst'])
            locations: Override instance locations
            
        Returns:
            List of extracted job dictionaries with standardized fields
        """
        active_locations = locations or self.locations or [None]
        all_jobs = []

        for role in job_roles:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Extracting fresher jobs for role: {role}")
            self.logger.info(f"{'='*60}")
            
            role_jobs = self._extract_for_role(role, active_locations)
            all_jobs.extend(role_jobs)

        # Filter for fresher jobs and salary criteria
        fresher_jobs = []
        for job in all_jobs:
            # Parse salary for filtering
            salary_dict = self._extract_salary_range(job.get("Salary", "NA"))
            
            # Check if fresher-friendly
            is_fresher = self._is_fresher_job(
                job.get("Experience", "NA"),
                job.get("Title", ""),
                job.get("Description", "")
            )
            
            # Apply filters
            if is_fresher and self._filter_by_salary(salary_dict):
                fresher_jobs.append(job)

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"EXTRACTION COMPLETE")
        self.logger.info(f"Total jobs scraped: {len(all_jobs)}")
        self.logger.info(f"Fresher-friendly jobs: {len(fresher_jobs)}")
        self.logger.info(f"{'='*60}\n")

        return fresher_jobs

    def _extract_for_role(self, job_role: str, locations: List[Optional[str]]) -> List[dict]:
        """Extract jobs for a specific role across multiple locations."""
        role_jobs = []
        
        for location in locations:
            self.logger.info(f"  → Searching in: {location or 'All Locations'}")
            location_jobs = self._extract_for_location(job_role, location)
            role_jobs.extend(location_jobs)
        
        return role_jobs

    def _extract_for_location(self, job_role: str, location: Optional[str]) -> List[dict]:
        """Extract jobs for specific role and location."""
        self._setup_driver()
        extracted_data = []
        seen_urls: Set[str] = set()

        try:
            url = self._build_fresher_job_url(job_role, location)
            self.logger.debug(f"URL: {url}")
            
            wait = WebDriverWait(self.driver, 15)
            exponential_backoff(lambda: self.driver.get(url))
            
            page_no = 1

            while page_no <= self.max_pages:
                self.logger.debug(f"    Page {page_no}/{self.max_pages}")
                
                try:
                    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.title")))
                except Exception as e:
                    self.logger.warning(f"No jobs found on page {page_no}: {e}")
                    break

                # Collect job URLs
                job_elems = self.driver.find_elements(By.CSS_SELECTOR, "a.title")
                job_urls = [elem.get_attribute("href") for elem in job_elems if elem.get_attribute("href")]

                if self.per_page_limit:
                    job_urls = job_urls[:self.per_page_limit]

                self.logger.debug(f"    Found {len(job_urls)} job listings")

                # Extract each job
                for job_url in job_urls:
                    if job_url in seen_urls:
                        continue
                    
                    seen_urls.add(job_url)
                    job_data = self._scrape_single_job(job_url, wait, job_role)
                    
                    if job_data and self._apply_location_filter(job_data.get("Location", "")):
                        extracted_data.append(job_data)

                # Navigate to next page
                if not self._go_to_next_page(page_no):
                    break

                page_no += 1
                time.sleep(random.uniform(self.min_delay, self.max_delay))

        except Exception as e:
            self.logger.error(f"Error during extraction: {e}")
        finally:
            self._close_driver()

        self.logger.info(f"    ✓ Extracted {len(extracted_data)} jobs")
        time.sleep(self.role_delay)
        return extracted_data

    def _scrape_single_job(self, job_url: str, wait, job_role: str) -> Optional[dict]:
        """Scrape details from a single job listing."""
        try:
            self.driver.execute_script("window.open(arguments[0], '_blank');", job_url)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(random.uniform(self.min_delay, self.max_delay))

            page = BeautifulSoup(self.driver.page_source, "html.parser")
            job_data = self._extract_job_details(page, job_url)
            
            if job_data:
                # Override Job_Type with actual job role searched
                job_data["Job_Type"] = job_role
                return job_data
                
        except Exception as e:
            self.logger.error(f"Error scraping {job_url}: {e}")
        finally:
            try:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception as e:
                self.logger.debug(f"Error closing tab: {e}")
        
        return None

    def _go_to_next_page(self, current_page: int) -> bool:
        """Navigate to next page of results."""
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "a.styles_btn-secondary__2AsIP")
            next_href = next_btn.get_attribute("href")
            
            if not next_href or f"page-{current_page+1}" not in next_href:
                return False
            
            self.driver.get(next_href)
            return True
        except Exception:
            return False

    def get_name(self) -> str:
        """Return extractor identifier."""
        return "FresherJobExtractor"


# Example usage
if __name__ == "__main__":
    # Initialize extractor
    extractor = FresherJobExtractor(
        max_pages=2,
        per_page_limit=3,
        min_delay=2,
        max_delay=4,
        locations=['bengaluru', 'mumbai', 'jaipur'],
        max_experience_years=1,
        min_salary=3,  # Minimum 3 LPA
        max_salary=8   # Maximum 8 LPA
    )
    
    # Extract jobs for multiple roles
    job_roles = [
        'python-developer',
        'data-analyst',
        'software-engineer',
        'full-stack-developer'
    ]
    
    # Returns list of dictionaries with standardized fields
    fresher_jobs = extractor.extract(job_roles)
    
    if fresher_jobs:
        print(f"\n✓ Successfully extracted {len(fresher_jobs)} fresher jobs!")
        
        # Display sample with standardized fields
        df = pd.DataFrame(fresher_jobs)
        # print(df)
        df.to_csv("fresher_jobs_sample.csv", index=False)
