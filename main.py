from pprint import pprint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from ghettobird import basic_method_A, basic_method_B, basic_method_C, selenium_method_B, fly

chromedriver_location = 'c:/chromedriver.exe'
browser = webdriver.Chrome(executable_path=chromedriver_location)

def TRANSFORM_firm_jobs(data):
    return data

def TRANSFORM_selenium_get_href(data):
    return data.get_attribute("href")

def login(browser):
    browser.get("https://www.linkedin.com/login")
    time.sleep(2)
    username = browser.find_element_by_xpath('//input[@id="username"]')
    password = browser.find_element_by_xpath('//input[@id="password"]')
    username.send_keys("throwaway1993@live.com")
    password.send_keys("fukthaPoleece!911")
    browser.find_element_by_xpath('//button[@type="submit"]').click()

#firm
id_firm_general_ROADMAP = {
    "url": "https://de.indeed.com/cmp/Getyourguide",
    "method": {
        "type": basic_method_C,
        "head": "window._initialData=JSON.parse('",
        "tail": "');"
        },
    "structure": {
        "id_company": {
            "path": ["topLocationsAndJobsStory", "companyName"]
        },
        "@id_lessText": {
            "path": ["aboutStory", "aboutDescription", "lessText"]
        },
        "@id_moreText": {
            "path": ["aboutStory", "aboutDescription", "moreText"]
        },
        "id_jobsopen": {
            "path": ["topLocationsAndJobsStory", "totalJobCount"]
        }
    }
}

id_jobs_ROADMAP = {
    "url": "https://de.indeed.com/cmp/Getyourguide/jobs?q=software",
    "method": {
        "type": basic_method_C,
        "head": "window._initialData=JSON.parse('",
        "tail": "');"
        },
    "structure": {
        "id_software_jobsopen": {
            "path": ["jobList", "filteredJobCount"]
        },
        "@id_jobs": {
            "path": ["jobList", "jobs"],
            "transformer": TRANSFORM_firm_jobs
        },
    }
}

id_job_ROADMAP = {
    "url": "https://de.indeed.com/cmp/Hellofresh/jobs?jk=22c38db700e6b578",
    "method": {
        "type": selenium_method_B,
        "browser": browser,
        "sleep": 2
    },
    "structure": {
        "//div[@class='cmp-JobDetail']": {
            ".//div[@class='cmp-JobDetailTitle']": {
                "value": "jobtitle",
            },
            ".//div[@class='cmp-JobDetailDescription-description']": {
                "value": "jobdesc",
            },
            ".//a[@data-tn-element='NonIAApplyButton']": {
                "value": "@id_apply",
                "transformer": TRANSFORM_selenium_get_href
            }
        }
     }
}

gd_firm_ROADMAP = {
    "url": "https://www.glassdoor.com/Overview/Working-at-UniGroup-EI_IE3422.11,19.htm",
    "method": {
        "type": basic_method_C,
        "script": "//script[@type='application/ld+json']"
        },
    "structure": {
        "gd_rating": {
            "path": ["ratingValue"]
        },
    }
}

li_firm_ROADMAP = {
    "url": "https://www.linkedin.com/company/adjustcom/jobs/",
    "method": {
        "type": selenium_method_B,
        "browser": browser,
        "sleep": 2
    },
    "structure": {
        "//body": {
            ".//h4": {
                "value": "li_jobsopen",
            },
            ".//span[@class='v-align-middle']": {
                "value": "li_allstaff",
            },
        }
     }
}

# pprint(fly(id_firm_general_ROADMAP)["results"])
# pprint(fly(id_jobs_ROADMAP)["results"])
# pprint(fly(id_job_ROADMAP)["results"])
# pprint(fly(gd_firm_ROADMAP)["results"])
login(browser)
pprint(fly(li_firm_ROADMAP)["results"])





