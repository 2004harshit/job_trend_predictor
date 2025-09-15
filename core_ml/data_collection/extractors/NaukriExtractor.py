from core_ml.data_collection.base import JobExtractor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import random, time
from core_ml.configuration.logger import setup_logging
import logging
# from core_ml.utils.robots import is_allowed
from core_ml.utils.backoff import exponential_backoff


setup_logging()
logger = logging.getLogger("data_collection")

class NaukriJobExtractor(JobExtractor):
    def __init__(self , max_pages , per_page_limit , min_delay , max_delay ,role_delay=10):
        self.max_pages = max_pages
        self.per_page_limit = per_page_limit
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.role_delay = role_delay
        
    def extract(self  ,job_name: str):
        logger.info(f"tarting job scraping for `{job_name}` using NaukriJobExtractor")


        options = webdriver.ChromeOptions()
        options.add_argument("--headless")          # Run without GUI
        options.add_argument("--no-sandbox")        # Required for many Linux servers
        options.add_argument("--disable-dev-shm-usage")  # Avoid memory issues
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 ... Chrome/117.0 Safari/537.36")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 8)

        extracted_data = []
        seen_job_urls = set()

        job_url = f"https://www.naukri.com/{job_name}-jobs"

        # if not is_allowed(job_url, "JobPipelineBot"):
        #     logger.error(f"Skipping {job_url} due to robots.txt restrictions")
        #     return []
        
        # start from first page
        exponential_backoff(lambda: driver.get(job_url))
        # driver.get(job_url)
        page_no = 1

        while page_no <= self.max_pages:
            logger.debug(f"Processing page {page_no} for {job_name}")
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.title")))
            except Exception as e:
                logger.error(f"Failed to load job listing for {job_name} on page {page_no}: {e}")
                break

            # collect job URLs
            job_elems = driver.find_elements(By.CSS_SELECTOR, "a.title")
            job_hrefs = [a.get_attribute("href") for a in job_elems if a.get_attribute("href")]

            if self.per_page_limit:
                job_hrefs = job_hrefs[:self.per_page_limit]
            
            logger.info(f"Found {len(job_hrefs)} links on page {page_no} for `{job_name}`")

            # scrape each job
            for job_url in job_hrefs:
                if job_url in seen_job_urls:
                    logger.debug(f"Skipping duplicate job url : {job_url}")
                    continue
                seen_job_urls.add(job_url)

                try:
                    driver.execute_script("window.open(arguments[0], '_blank');", job_url)
                    driver.switch_to.window(driver.window_handles[-1])
                    # random delay to mimic human behavior
                    time.sleep(random.uniform(self.min_delay,self.max_delay))

                    page = BeautifulSoup(driver.page_source, "html.parser")

                    # extract job  info
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

                    details = {}
                    details_section = page.find("div", class_="styles_other-details__oEN4O")
                    if details_section:
                        for div in details_section.find_all("div", class_="styles_details__Y424J"):
                            label = div.find("label")
                            span = div.find("span")
                            if label:
                                details[label.get_text(strip=True).replace(":", "")] = span.get_text(" ", strip=True) if span else "NA"

                    edu_elem = page.find("div", class_="styles_education__KXFkO")
                    education = edu_elem.get_text(strip=True) if edu_elem else "Not Available"

                    skills_section = page.find("div", class_="styles_key-skill__GIPn_")
                    star_skills, normal_skills = [], []
                    if skills_section:
                        for a in skills_section.find_all("a", class_="styles_chip__7YCfG"):
                            skill_name = a.find("span").get_text(strip=True) if a.find("span") else "NA"
                            if a.find("i", class_="ni-icon-jd-save"):
                                star_skills.append(skill_name)
                            else:
                                normal_skills.append(skill_name)
                    skills = [star_skills, normal_skills]

                    jd_elem = page.find("div", class_="styles_JDC__dang-inner-html__h0K4t")
                    job_description = jd_elem.get_text(" ", strip=True) if jd_elem else "NA"

                    extracted_data.append({
                        "Job Type": job_name,
                        "Title": title,
                        "Company": company,
                        "Experience": exp,
                        "Salary": salary,
                        "Location": location,
                        "Education": education,
                        "Skills": skills,
                        **details,
                        "Description": job_description,
                        "Job URL": job_url
                    })

                    logger.debug(f"Extracted job: {title} ({job_url})")

                except Exception as e:
                    logger.error(f"Error extracting job at {job_url}: {e}")
                finally:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

            # move to next page
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "a.styles_btn-secondary__2AsIP[href*='-jobs-']")
                next_href = next_btn.get_attribute("href")
                if not next_href:
                    logger.warning(f"No 'Next' link found on page {page_no} for {job_name}. Stopping")
                    break
                driver.get(next_href)
                page_no += 1
            except:
                logger.warning(f"No Next button found on page {page_no} for {job_name} Ending pagination")
                break

        logger.info(f"Finished scraping {len(extracted_data)} jobs for '{job_name}'")
        logger.info(f"Sleeping {self.role_delay} seconds before next role")
        time.sleep(self.role_delay)

        return extracted_data
    
    def get_name(self):
        return "NaukriExtractor"
    
    
if __name__ == "__main__":
    Nje = NaukriJobExtractor()
    Nje.extract("python-developer", 10 , 15)