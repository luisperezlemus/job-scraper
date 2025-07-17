# An automated job scraper
This Python script will scrape jobs using Selenium to extract job postings from company websites and will filter by job title
and job location using regular expressions. The script emails the result, using your Gmail credentials, to the recipient(s) listed in `config.yaml`. The Gmail credentials must be inserted in `.env`.

This script currently works only with Workday. 

## Getting Started
Below are the prerequisites to get the project up and running on your machine.

### Downloading ChromeDriver
Selenium needs ChromeDriver to create Chrome instances. Download [here.](https://developer.chrome.com/docs/chromedriver/downloads)

### Python packages
Install the Python packages needed for this script using
```
pip install -r requirements.txt
``` 
I created virtual environment with Python 3.12 to develop and run this.

### Gmail login
In `.env`, enter the email address for the account you are sending the email from and enter an app password. Help thread for that [here.](https://support.google.com/mail/answer/185833?hl=en)

### Templates
.env.template, config.yaml.template, and sent_jobs.csv.template are templates for the files needed for the script to run. Simply remove the .template extension. Then fill the information needed for `.env` and `config.yaml`. Don't modify `sent_jobs.csv`

### config.yaml
The config is used for filtering the type of jobs you are looking for. Enter the job titles you are interested in `key_groups`,
then enter the variations of strings that a post would typically include for that of job title. The same applies for locations under `locations`. Enter the email address or addresses you are sending to under `email_recipients`.

## Running the script
To run the script, enter
```
python main.py
```
