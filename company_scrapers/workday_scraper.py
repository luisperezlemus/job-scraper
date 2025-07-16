from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_workday(url):
    options = Options()
    options.add_argument("--headless") # Run in headless mode after testing is complete
    driver = webdriver.Chrome(options=options)
    jobs = []
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        # wait until the job cards are loaded
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='list']")))

        # get the job cards
        while True:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='list']")))
            ul = driver.find_element(By.CSS_SELECTOR, "ul[role='list']")
            job_cards = ul.find_elements(By.CSS_SELECTOR, ":scope > li")
            for job_card in job_cards:
                try:
                    title_tag = job_card.find_element(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")
                    title = title_tag.text
                    link = title_tag.get_attribute("href")

                    # check location
                    location_tag = job_card.find_element(By.TAG_NAME, "dd")
                    location = location_tag.text

                    job_id_ul = job_card.find_element(By.CSS_SELECTOR, "ul[data-automation-id='subtitle']")
                    job_id_tag = job_id_ul.find_element(By.TAG_NAME, "li")
                    job_id = job_id_tag.text

                    print(f"Title: {title}, location: {location}, job id: {job_id}")

                    jobs.append({
                        "title": title,
                        "link": link,
                        "location": location,
                        "position_type": "N/A", # not provided on the job card, 
                        "job_id": job_id
                    })
            
                except Exception as e:
                    print(f"Error with job: {e}")
            
            # check if on last page, if not then move on to next page and go up the loop
            # if on last page, break out of the loop
            num_job_text = driver.find_element(By.CSS_SELECTOR, "p[data-automation-id='jobOutOfText']").text
            print(num_job_text)
            cur_job_num = int(num_job_text.split(" ")[2])
            total_jobs = int(num_job_text.split(" ")[4])
            # print(f"Jobs seen: {cur_job_num}, Total jobs: {total_jobs}")
            if cur_job_num == total_jobs:
                print("Reached the last page.")
                break
            else:
                pag = driver.find_element(By.CSS_SELECTOR, "nav[aria-label='pagination']")
                next_button = pag.find_element(By.CSS_SELECTOR, "button[aria-label='next']")
                next_button.click()
                # Wait for previous job cards to be stale so the next set of jobs can be loaded
                wait.until(EC.staleness_of(job_cards[0]))  
            
    finally:
        driver.quit()
        jobs = resolve_locations_parallel(jobs)  # Use the parallel location resolver
        return jobs
    


# from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures import ThreadPoolExecutor

# resolve locations for jobs that have multiple locations
def resolve_block(jobs):
    options = Options()
    options.add_argument("--headless")  # Run in headless mode after testing is complete
    driver = webdriver.Chrome(options=options)
    resolved = []
    for job in jobs:
        try:
            driver.get(job["link"])
            wait = WebDriverWait(driver, 10)
            # wait until the job details are loaded
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-automation-id='job-posting-details']")))
            # get locations
            location_div = driver.find_element(By.CSS_SELECTOR, "div[data-automation-id='locations']")
            locations_dl = location_div.find_element(By.TAG_NAME, "dl")
            locations_tags = locations_dl.find_elements(By.TAG_NAME, "dd")
            locations = [location.text for location in locations_tags]
            print(f"Locations for {job['title']}: {locations}")
            job["location"] = locations if locations else [job["location"]]
        except Exception as e:
            print(f"Error retrieving locations for job {job['title']}: {e}")
            job["location"] = [job["location"]]  # Fallback to single location
        
        resolved.append(job)

    driver.quit()
    return resolved

def resolve_locations_parallel(jobs, max_workers=4):
    resolved_jobs = []

    # Split jobs into two groups
    jobs_with_multiple_locations = [job for job in jobs if "Locations" in job["location"]]
    jobs_with_single_location = [job for job in jobs if "Locations" not in job["location"]]

    # Resolve jobs with multiple locations in parallel
    blocks = [[] for _ in range(max_workers)] # a list of lists, size = max_workers, each list in the list has variable size, depending on the number of jobs, and they're evenly split
    # split jobs to process into blocks
    for i, job in enumerate(jobs_with_multiple_locations):
        blocks[i % max_workers].append(job)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(resolve_block, block) for block in blocks]

        for future in futures:
            try:
                resolved_jobs.extend(future.result())
            except Exception as e:
                print(f"Error resolving job locations: {e}")
    
    
    for job in jobs_with_single_location:
        job["location"] = [job["location"]]
        resolved_jobs.append(job)

    return resolved_jobs