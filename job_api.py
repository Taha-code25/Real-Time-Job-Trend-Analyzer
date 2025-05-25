from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote_plus
import time
import os
import pandas as pd
from datetime import datetime,timedelta

def setup_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver


def save_to_csv(jobs, file_path="combined_jobs.csv"):
    df = pd.DataFrame(jobs)
    write_header = not os.path.exists(file_path) or os.path.getsize(file_path) == 0
    df.to_csv(file_path, mode='a', index=False, header=write_header)
    print(f"✅ Saved {len(jobs)} job(s) to {file_path}")


def scrape_rozee_jobs(job_title="data analyst", pages=1):
    driver = setup_driver()
    jobs = []
    query = quote_plus(job_title)

    for page in range(1, pages + 1):
        url = f"https://www.rozee.pk/search/job?q={query}&page={page}"
        print(f"\n🔍 Scraping Rozee Page {page}: {url}")
        driver.get(url)
        time.sleep(4)

        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job")

        for card in job_cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, "div.jobt h3 a bdi").text.strip()

                cname_tags = card.find_elements(By.CSS_SELECTOR, "div.cname a.display-inline")
                company = cname_tags[0].text.strip() if len(cname_tags) > 0 else ""
                location = ", ".join([el.text.strip() for el in cname_tags[1:]])

                date_elem = card.find_element(By.CSS_SELECTOR, "i.rz-calendar")
                date_posted = date_elem.find_element(By.XPATH, "..").text.strip()

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "date_posted": date_posted,
                })

            except Exception as e:
                print("⛔ Error in Rozee job card:", e)
                continue

    driver.quit()
    save_to_csv(jobs)
    return pd.DataFrame(jobs)


def scrape_glassdoor_jobs(job_title="data analyst", pages=1):
    driver = setup_driver()
    jobs = []
    query = quote_plus(job_title)

    for page in range(1, pages + 1):
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query}&p={page}"
        print(f"\n🔍 Scraping Glassdoor Page {page}: {url}")
        driver.get(url)
        time.sleep(5)

        job_cards = driver.find_elements(By.CSS_SELECTOR, 'li[data-test="jobListing"]')
        for card in job_cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, "a.JobCard_jobTitle__GLyJ1").text.strip()
                company = card.find_element(By.CSS_SELECTOR, "span.EmployerProfile_compactEmployerName__9MGcV").text.strip()
                location = card.find_element(By.CSS_SELECTOR, "div.JobCard_location__Ds1fM").text.strip()
                date_posted = card.find_element(By.CSS_SELECTOR, "div.JobCard_listingAge__jJsuc").text.strip()
                today = datetime.today()
                formatted_date = "unknown"  # Default value
    
                if "d" in date_posted:
                    days_ago = ''.join(filter(str.isdigit, date_posted))
                    if days_ago:
                        days_ago = int(days_ago)
                        formatted_date = (today - timedelta(days=days_ago)).strftime("%B %d, %Y")
                elif "30d+" in date_posted:
                     formatted_date = (today - timedelta(days=30)).strftime("%B %d, %Y")
                elif 'h' in date_posted:
                    formatted_date = today.strftime("%B %d, %Y")
                
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "date_posted": formatted_date
                })
            except Exception as e:
                print("⛔ Error in Glassdoor job card:", e)
                continue

    driver.quit()
    save_to_csv(jobs)
    return pd.DataFrame(jobs)


if __name__ == "__main__":
    df_rozee = scrape_rozee_jobs("data analyst", pages=2)
    df_glassdoor = scrape_glassdoor_jobs("data analyst", pages=2)
    print("\n✅ All jobs successfully scraped and saved.")
