from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# garmin has a div named mat-paginator-range-label with contains the number of jobs we've seen out of the 
# total number of jobs, so we can use that gauge when we get to the last page
def scrape_garmin():
    options = Options()
    options.add_argument("--headless") # Run in headless mode after testing is complete
    driver = webdriver.Chrome(options=options)
    jobs = []
    try:
        url = "https://careers.garmin.com/careers-home/jobs"
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        # wait until the job cards are loaded
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".mat-accordion.cards")))

        # get the job cards
        while True:
            # wait for the jobs cards to load
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".mat-accordion.cards")))
            job_cards = driver.find_elements(By.CLASS_NAME, "mat-expansion-panel")
            for job_card in job_cards:
                try:
                    title_tag = job_card.find_element(By.CLASS_NAME, "job-title-link")
                    title = title_tag.find_element(By.TAG_NAME, "span").text
                    # print(title)
                    link = job_card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    job_description_tag = job_card.find_element(By.TAG_NAME, "mat-panel-description")
                    job_location = job_description_tag.find_element(By.CSS_SELECTOR, "span .label-value.location").text
                    position_type = job_description_tag.find_element(By.CSS_SELECTOR, "span .label-value.tags3").text

                    print(f"Title: {title}, Location: {job_location}, Position Type: {position_type}")
                    jobs.append({
                        "title": title,
                        "link": link,
                        "location": job_location,
                        "position_type": position_type
                    })
                except Exception as e:
                    print(f"Error with job: {e}")
            
            # check if on last page, if not then move on to next page and go up the loop
            # if on last page, break out of the loop
            paginator = driver.find_element(By.CSS_SELECTOR, "div .mat-paginator-range-label")
            paginator_text = paginator.text
            job_num = paginator_text.split(" ")[2]
            total_jobs = paginator_text.split(" ")[4]
            print(f"Jobs seen: {job_num}, Total jobs: {total_jobs}")
            if job_num == total_jobs:
                print("Reached the last page.")
                break
            else:
                pag = driver.find_element(By.CSS_SELECTOR, "div .mat-paginator-range-actions")      
                next_button = pag.find_element(By.CSS_SELECTOR, "button[aria-label='Next Page of Job Search Results']")
                # print(next_button.get_attribute("outerHTML"))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                driver.execute_script("arguments[0].click();", next_button)

    finally:
        driver.quit()
        return jobs


if __name__ == "__main__":
    scrape_garmin()