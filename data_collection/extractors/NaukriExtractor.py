from base import JobExtractor
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

class NaukriJobExtractor(JobExtractor):

    def extract(self  ,job_name: str , max_pages: int , per_page_limit: int):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 8)

        all_data = []
        seen_job_urls = set()

        print(f"Scraping jobs for: {job_name}")

        # start from first page
        driver.get(f"https://www.naukri.com/{job_name}-jobs")
        page_no = 1

        while page_no <= max_pages:
            print(f"Page {page_no} for {job_name}")
            # wait for jobs
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.title")))
            except:
                print("No jobs found, stopping.")
                break

            # collect job URLs
            job_elems = driver.find_elements(By.CSS_SELECTOR, "a.title")
            job_hrefs = [a.get_attribute("href") for a in job_elems if a.get_attribute("href")]
            if per_page_limit:
                job_hrefs = job_hrefs[:per_page_limit]

            # scrape each job
            for job_url in job_hrefs:
                if job_url in seen_job_urls:
                    continue
                seen_job_urls.add(job_url)

                # open in new tab
                driver.execute_script("window.open(arguments[0], '_blank');", job_url)
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(2)
                page = BeautifulSoup(driver.page_source, "html.parser")

                # extract info
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
                all_data.append({
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

                # close job tab
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            # find and click "Next"
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "a.styles_btn-secondary__2AsIP[href*='-jobs-']")
                next_href = next_btn.get_attribute("href")
                if not next_href:
                    print("No next page link, stopping.")
                    break
                driver.get(next_href)
                page_no += 1
            except:
                print("No Next button found, stopping pagination.")
                break
            print(f"Finished {job_name}")
            

if __name__ == "__main__":
    Nje = NaukriJobExtractor()
    Nje.extract("python-developer", 5 , 5)