#!/usr/bin/env python3

# we run all scrapers in this file and we filter the postings by title and location
# then we check if the job is already in our database (csv file) and if not,
# we will add it to the pool of data that we will email to the user and later
# save to the csv file
import yaml
import pandas as pd
from datetime import datetime
from company_scrapers.workday_scraper import scrape_workday
import json
from email_utils import send_email  # Assuming you have an email_utils.py for sending emails
import re
import chromedriver_autoinstaller  
import os

# ensure we are in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# install latest chromedriver
chromedriver_autoinstaller.install()  

# csv file that contains all sent jobs
CSV_FILE = "sent_jobs.csv"

# config file for filtering jobs by title and location
def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

# load jobs sent from the csv file
def load_previous_jobs():
    try:
        df = pd.read_csv(CSV_FILE, parse_dates=[5])
        df["location"] = df["location"].apply(json.loads)
    except Exception as e:
        print(f"Error loading previous jobs: {e}")
    
    print(df.head())
    return df

# filters out jobs that have already been sent, mainly using the link as the identifier
def filter_jobs_in_dataframe(jobs, df, company_name):
    # returns the jobs that are not in the dataframe, if they are then the age must be greater than 14 days
    if df.empty:
        return jobs
    
    # we are only interested in jobs from the specified company
    df = df[df['company'] == company_name]

    df_links = set(df['link'])
    filtered_jobs = []
    for job in jobs:
        title = job.get("title")
        link = job.get("link", "")

        # if the title and link is in the dataframe, we skip it. Some job titles have the same name
        # so we use the link to ensure that it's a unique posting
        if link in df_links:
            prev_title = df[df['link'] == link]['title'].values[0].lower()
            if title.lower() == prev_title:
                print(f"Skipping {title} because it has already been sent.")
                continue

        filtered_jobs.append(job)
    
    return filtered_jobs


# checks if any of the words in the job title match the keywords in the config file
def keyword_match(job_title, key_groups):
    title = job_title.lower()
    for keywords in key_groups.values():
        for keyword in keywords:
            keyword = keyword.lower()
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, title):
                print(f"Found keyword match: {keyword} in {title}")
                return True


def filter_jobs(scraped_jobs, prev_scraped_jobs, config, company_name):
    print("filtering...")
    filtered_jobs = []
    # load the configs
    key_groups = config.get("key_groups", {})
    locations = config.get("locations", [])

    # first filter about by title and location
    for job in scraped_jobs:
        title = job.get("title").lower()
        location = job.get("location") # a list of locations or a single location
        NON_US_KEYWORDS = ["india", "china", "philippines", "brazil"]
        location_found = False
        # check if location matches any of the locations in the config
        for _, keywords in locations.items(): # location, [locations]
            for keyword in keywords: # each string that repesents a location
                keyword = keyword.lower()
                pattern = r"\b" + re.escape(keyword) + r"\b"  # Match whole words only
                for loc in location: # a list of locations in the job posting
                    loc = loc.lower()

                    if "remote" in loc and keyword == "remote":
                        if any(non_us in loc for non_us in NON_US_KEYWORDS):
                            print(f"Skipping {title} because it is a remote job in a non-US location: {loc}")
                            continue

                    if re.search(pattern, loc):  # Check if the keyword matches the location
                        print(f"Found location match: {keyword} in {loc} for job {title}")
                        location_found = True
                        break
                if location_found:
                    break
            if location_found:
                break
        # move on to the next job posting if no location matches
        if not location_found:
            continue

        # check any of the keywords are in the title
        if not keyword_match(title, key_groups):
            continue
        # append job to the list
        filtered_jobs.append(job)

    # filter jobs from the ones that have been sent already
    filtered_jobs = filter_jobs_in_dataframe(filtered_jobs, prev_scraped_jobs, company_name)
    return filtered_jobs


def save_jobs_to_csv(jobs, filename=CSV_FILE):
    jobs_to_write = []
    for job in jobs:
        jobs_to_write.append({
                "company": job["company"],
                "title": job["title"],
                "link": job["link"],
                "location": json.dumps(job["location"]),
                "job_id": job.get("job_id"),
                "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    df = pd.DataFrame(jobs_to_write)
    df.to_csv(filename, mode='a', header=not pd.io.common.file_exists(filename), index=False)

def main():
    config = load_config()
    prev_scraped_jobs = load_previous_jobs()
    jobs_to_send = []
    # companies have their own scrapers
    scrapers = {
        "Intel": lambda: scrape_workday("https://intel.wd1.myworkdayjobs.com/External"),
        "AT&T": lambda: scrape_workday("https://att.wd1.myworkdayjobs.com/ATTGeneral"),
        "Adobe": lambda: scrape_workday("https://adobe.wd5.myworkdayjobs.com/external_experienced"),
        "HP": lambda: scrape_workday("https://hp.wd5.myworkdayjobs.com/ExternalCareerSite"),
        "Salesforce": lambda: scrape_workday("https://salesforce.wd12.myworkdayjobs.com/External_Career_Site"),
        "Ancestry": lambda: scrape_workday("https://ancestry.wd5.myworkdayjobs.com/Careers"),
        "Slack": lambda: scrape_workday("https://salesforce.wd12.myworkdayjobs.com/Slack"),
        "Activision": lambda: scrape_workday("https://activision.wd1.myworkdayjobs.com/External"),
        "Autodesk": lambda: scrape_workday("https://autodesk.wd1.myworkdayjobs.com/Ext"),
        "Avant": lambda: scrape_workday("https://avant.wd1.myworkdayjobs.com/External_Careers"),
        "BlackBerry": lambda: scrape_workday("https://bb.wd3.myworkdayjobs.com/BlackBerry"),
        "Boston Dynamics": lambda: scrape_workday("https://bostondynamics.wd1.myworkdayjobs.com/Boston_Dynamics"),
        "Cadence": lambda: scrape_workday("https://cadence.wd1.myworkdayjobs.com/External_Careers"),
        "Dell": lambda: scrape_workday("https://dell.wd1.myworkdayjobs.com/External"),
        "DraftKings": lambda: scrape_workday("https://draftkings.wd1.myworkdayjobs.com/en-US/DraftKings/jobs"),
        "Etsy": lambda: scrape_workday("https://etsy.wd5.myworkdayjobs.com/Etsy_Careers"),
        "Workday": lambda: scrape_workday("https://workday.wd5.myworkdayjobs.com/Workday"),
        "Razer": lambda: scrape_workday("https://razer.wd3.myworkdayjobs.com/Careers"),
        "Red Hat": lambda: scrape_workday("https://redhat.wd5.myworkdayjobs.com/Jobs"),
        "Siemens": lambda: scrape_workday("https://onehealthineers.wd3.myworkdayjobs.com/SHSJB"),
        "Snapchat": lambda: scrape_workday("https://wd1.myworkdaysite.com/en-US/recruiting/snapchat/snap"),
        "Chevron": lambda: scrape_workday("https://chevron.wd5.myworkdayjobs.com/jobs"),
        "Mastercard": lambda: scrape_workday("https://mastercard.wd1.myworkdayjobs.com/CorporateCareers"),
        "NVIDIA": lambda: scrape_workday("https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"),
        "Microchip": lambda: scrape_workday("https://wd5.myworkdaysite.com/recruiting/microchiphr/External"),
        "NXP": lambda: scrape_workday("https://nxp.wd3.myworkdayjobs.com/careers"),
        "Analog Devices": lambda: scrape_workday("https://analogdevices.wd1.myworkdayjobs.com/External"),
        "Bank of America": lambda: scrape_workday("https://ghr.wd1.myworkdayjobs.com/Lateral-US"),
        "Citi": lambda: scrape_workday("https://citi.wd5.myworkdayjobs.com/CitiGlobal"),
        "Morgan Stanley": lambda: scrape_workday("https://ms.wd5.myworkdayjobs.com/External"),
        "BMO": lambda: scrape_workday("https://bmo.wd3.myworkdayjobs.com/External"),
        "Blackstone": lambda: scrape_workday("https://blackstone.wd1.myworkdayjobs.com/Blackstone_Careers"),
        "Toyota": lambda: scrape_workday("https://toyota.wd5.myworkdayjobs.com/TMNA"),
        "Southwest": lambda: scrape_workday("https://swa.wd1.myworkdayjobs.com/external"),
        "Abbott": lambda: scrape_workday("https://abbott.wd5.myworkdayjobs.com/abbottcareers"),
        "3M": lambda: scrape_workday("https://3m.wd1.myworkdayjobs.com/Search"),
        "Comcast": lambda: scrape_workday("https://comcast.wd5.myworkdayjobs.com/Comcast_Careers"),
        "The Washington Post": lambda: scrape_workday("https://washpost.wd5.myworkdayjobs.com/washingtonpostcareers"),
        "Warner Bros": lambda: scrape_workday("https://warnerbros.wd5.myworkdayjobs.com/en-US/global"),
        "Netflix": lambda: scrape_workday("https://netflix.wd1.myworkdayjobs.com/Netflix"),
        "Accenture": lambda: scrape_workday("https://accenture.wd103.myworkdayjobs.com/en-US/AccentureCareers/"),
    }

    for company, scraper in scrapers.items():
        print(f"Running: {company}")
        try:
            scraped_jobs = scraper()
            for job in scraped_jobs:
                job["company"] = company

            # filter the jobs based on config and if not already in previous jobs
            filtered_jobs = filter_jobs(scraped_jobs, prev_scraped_jobs, config, company)

            # append the filtered jobs to the list of jobs to send
            jobs_to_send.extend(filtered_jobs)
        except Exception as e:
            print(f"Error scraping {company}: {e}")
            continue
    
    # send email with the jobs
    if len(jobs_to_send) == 0:
        print("No new jobs to send.")
        return
    
    send_email(jobs_to_send, config.get("email_recipients"))
    save_jobs_to_csv(jobs_to_send)
    print(f"Saved {len(jobs_to_send)} jobs to {CSV_FILE}.")


if __name__ == "__main__":
    main()
