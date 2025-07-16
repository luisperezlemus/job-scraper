# An automated job scraper
This Python script will scrape jobs using Selenium to extract job postings from company websites and will filter by job title
and job location using regular expressions. The script emails the result to you using your Gmail credentials to send the 
email to the recipient(s) listed in the [config.yaml](config.yaml) file. The Gmail credentials must be inserted in [.env](.env).

This script currently works only with  Workday. 
