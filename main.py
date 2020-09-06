from pprint import pprint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

from ghettobird import basic_method_A, basic_method_B, basic_method_C, selenium_method_B, fly

scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
client = gspread.authorize(creds)

chromedriver_location = 'c:/chromedriver.exe'
browser = webdriver.Chrome(executable_path=chromedriver_location)

firmHeader = ["company", "id_link", "id_jobsopen", "id_software_jobsopen", "id_about", "gd_link", "gd_score", "li_link", "li_allstaff", "li_jobsopen"]
jobHeader =  ["company", "id_jobtitle",	"id_joblink", "id_jobdesc", "id_daysopen", "id_location", "id_contact", "id_apply", "id_role", "id_stack_primary", "id_stack_secondary", "id_level"]

settings = {
    "indeed_query": "",
    "id_stack": "",
    "id_role": "",
    "id_level": "",
}

def handleSettings():
    data = getSheetData("Settings")
    settings["indeed_query"] = data[0]["value"]
    settings["id_stack"] = data[1]["value"].lower().split(',')
    settings["id_role"] = data[2]["value"].lower().split(',')
    settings["id_level"] = data[3]["value"].lower().split(',')

def TRANSFORM_firm_jobs(data):
    return data

def TRANSFORM_selenium_get_href(data):
    return data.get_attribute("href")

def TRANSFORM_clean_li_allstaff(data):
    data = data.text.replace("See all ", "")
    data = data.replace(" employees on LinkedIn", "")
    return data

def TRANSFORM_clean_li_jobsopen(data):
    data = data.text.replace("Templafy has ", "")
    data = data.replace(" job openings - find the one for you.", "")
    return data

def TRANSFORM_clean_id_daysopen(data):
    data = data.text.replace("vor ", "")
    data = data.replace(" Tagen", "")
    return data

def TRANSFORM_id_stray_jobsopen(data):
    data = data.text.replace("Seite 1 von ", "")
    data = data.replace(" Jobs", "")
    return data

def login(browser):
    browser.get("https://www.linkedin.com/login")
    time.sleep(2)
    username = browser.find_element_by_xpath('//input[@id="username"]')
    password = browser.find_element_by_xpath('//input[@id="password"]')
    username.send_keys("throwaway1993@live.com")
    password.send_keys("fukthaPoleece!911")
    browser.find_element_by_xpath('//button[@type="submit"]').click()

def getSheetData(sheet):
    s = client.open("Indeed v2").worksheet(sheet)
    data = s.get_all_records()
    return data

def writeToSheet(sheet, header, data):
    if len(data) > 0:
        s = client.open("Indeed v2").worksheet(sheet)
        book = client.open("Indeed v2")
        book.values_clear(sheet + "!A1:L10000")
        data.insert(0, header)
        cells = []
        for row_num, row in enumerate(data):
            for col_num, cell in enumerate(row):
                cells.append(gspread.Cell(row_num + 1, col_num + 1, data[row_num][col_num]))
        s.update_cells(cells)
def arrayToCommaSeperated(arr):
    new = ""
    for a in arr:
        new += a + ", "
    return new

def analyzeText(title, description):
    title = title.lower()
    description = description.lower()
    spacedTitle = title.split(" ")
    spacedDescription = description.split(" ")
    
    data = {
        "email": "",
        "id_stack_primary": [],
        "id_stack_secondary": [],
        "id_role": [],
        "id_level": [],
    }

    numbers = "0123456789"
    spacedDescriptionNewLine = description.replace("\n", " ")
    spacedDescriptionNewLine = spacedDescriptionNewLine.split(" ")
    for i in range(0, len(spacedDescriptionNewLine)):
        s = spacedDescriptionNewLine[i]
        if "@" in s and (".com" in s or ".net" in s or ".org" in s):
            data["email"] = s
    removelist = "+-"

    pattern = re.compile(r'[^\w'+removelist+']')
    
    spacedDescription = pattern.split(description)
    spacedTitle = pattern.split(title)

    stack = {}
    
    for setting in settings["id_stack"]:
        count = 0
        if setting in spacedTitle:
            data["id_stack_primary"].append(setting)
        else: 
            for word in spacedDescription:
                    if setting == word:
                        count += 1
            if count > 0:
                stack[setting] = count
    
    stack = sorted(stack.items(), key=lambda x: x[1], reverse=True)
    new = []
    for s in stack:
        new.append(s[0])
    if len(data["id_stack_primary"]) == 0 and len(stack) != 0:
        data["id_stack_primary"].append(new.pop(0))
    data["id_stack_secondary"] = new

    for setting in settings["id_role"]:
        if setting not in data["id_role"]:
            if " " in setting:
                if setting in title:
                    data["id_role"].append(setting)
            else:
                if setting in spacedTitle:
                    data["id_role"].append(setting)
    
    for setting in settings["id_level"]:
        if setting not in data["id_level"]:
            if " " in setting:
                if setting in title:
                    data["id_level"].append(setting)
            else:
                if setting in spacedTitle:
                    data["id_level"].append(setting)

    data["id_stack_primary"] = arrayToCommaSeperated(data["id_stack_primary"])
    data["id_stack_secondary"] = arrayToCommaSeperated(data["id_stack_secondary"])
    data["id_role"] = arrayToCommaSeperated(data["id_role"])
    data["id_level"] = arrayToCommaSeperated(data["id_level"])  
    return data

#firm
id_firm_general_ROADMAP = {
    "url": "https://de.indeed.com/cmp/Getyourguide", #model URL
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
    "url": "https://de.indeed.com/cmp/Getyourguide/jobs",
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
                "value": "@id_non_apply",
                "transformer": TRANSFORM_selenium_get_href
            },
            ".//a[@data-tn-element='IAApplyButton']": {
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
        "gd_score": {
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
                "transformer": TRANSFORM_clean_li_jobsopen
            },
            ".//span[@class='v-align-middle']": {
                "value": "li_allstaff",
                "transformer": TRANSFORM_clean_li_allstaff
            },
        }
     }
}

id_stray_firm_ROADMAP = {
    "url": "https://de.indeed.com/Jobs?as_and=&as_phr=&as_any=&as_not=&as_ttl=&as_cmp=neugelb+studios&st=&radius=25&fromage=any&limit=10&sort=&psf=advsrch&from=advancedsearch",
    "method": {
        "type": selenium_method_B,
        "browser": browser,
        "sleep": 2
    },
    "structure": {
        "//body": {
            # ".//div[@id='searchCountPages']": {
            #     "value": "id_software_jobsopen",
            #     "transformer": TRANSFORM_id_stray_jobsopen
            # },
            # ".//*[@id='searchCountPages']": {
            #     "value": "id_jobsopen",
            #     "transformer": TRANSFORM_id_stray_jobsopen
            # },
            ".//div[@data-tn-component='organicJob']": {
                ".//*[@data-tn-element='jobTitle']": {
                    "value": "id_jobtitle"
                },
                # ".//a[@data-tn-element='jobTitle']": {
                #     "value": "id_joblink",
                #     "transformer": TRANSFORM_selenium_get_href
                # },
            }
        }
     }
}


def scrape():
    login(browser)
    inputSpreadsheet = getSheetData("Input")
    firms = []
    for firmInput in inputSpreadsheet:
        f = {
            "company": firmInput["company"],
            "id_link": firmInput["id_link"],
            "id_jobsopen": "",
            "id_software_jobsopen": "",
            "id_about": "",
            "gd_link": firmInput["gd_link"], 
            "gd_score": "",
            "li_link": firmInput["li_link"],
            "li_allstaff": "",
            "li_jobsopen": "",
            "jobs": []
        }
        if f["id_link"] != "":
            #general firm method
            if "https://de.indeed.com/Jobs?" in f["id_link"]:
                print("stray")
                break
            else:
                id_firm_general_ROADMAP["url"] = f["id_link"]
                results = fly(id_firm_general_ROADMAP)["results"]
                f["id_jobsopen"] = results["id_jobsopen"]
                f["id_about"] = results["@id_lessText"] + " " + results["@id_moreText"]
                #firm jobs method
                id_jobs_ROADMAP["url"] = f["id_link"] + "/jobs" + "?q=" + settings["indeed_query"]
                results = fly(id_jobs_ROADMAP)["results"]
                f["id_software_jobsopen"] = results["id_software_jobsopen"]
                rawJobs = results = fly(id_jobs_ROADMAP)["results"]["@id_jobs"]
                for job in rawJobs:
                    j = {
                        "company": f["company"],
                        "id_jobtitle": job["title"],
                        "id_joblink": f["id_link"] + "/jobs" + job["url"],
                        "id_jobdesc": "",
                        "id_daysopen": job['formattedRelativeTime'],
                        "id_location": job["location"],
                        "id_contact": "",
                        "id_apply":	"",
                        "id_role": "",
                        "id_stack_primary": "",
                        "id_stack_secondary": "",
                        "id_level": ""
                    }
                    #id job method
                    id_job_ROADMAP["url"] = f["id_link"] + "/jobs?jk=" + job["jobKey"]
                    results = fly(id_job_ROADMAP)["results"][0] #COULD BE PROBLAMETIC SOON
                    if "@id_apply" in results.keys():
                        j["id_apply"] = results["@id_apply"]
                    if "@id_non_apply" in results.keys():
                        j["id_apply"] = results["@id_non_apply"]
                    j["id_jobdesc"] = results["jobdesc"]

                    analysis = analyzeText(j["id_jobtitle"], j["id_jobdesc"])
                    j["id_contact"] = analysis["email"]
                    j["id_stack_primary"] = analysis["id_stack_primary"]
                    j["id_stack_secondary"] = analysis["id_stack_secondary"]
                    j["id_role"] = analysis["id_role"]
                    j["id_level"] = analysis["id_level"]
                    f["jobs"].append(j)
            
        if f["gd_link"] != "":
            gd_firm_ROADMAP["url"] = f["gd_link"]
            results = fly(gd_firm_ROADMAP)["results"]
            f["gd_score"] = results["gd_score"]
        if f["li_link"] != "":
            li_firm_ROADMAP["url"] = f["li_link"] + "jobs"
            results = fly(li_firm_ROADMAP)["results"][0]
            f["li_allstaff"] = results["li_allstaff"]
            f["li_jobsopen"] = results["li_jobsopen"]
        firms.append(f)
    return firms

def main():
    handleSettings()        
    scraped = scrape()
    jobs = []
    firms = []
    creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope) #refresh creds for lengthy run time
    client = gspread.authorize(creds) #refresh creds for lengthy run time
    for firm in scraped:    
        firms.append([firm["company"], firm["id_link"], firm["id_jobsopen"], firm["id_software_jobsopen"], firm["id_about"], firm["gd_link"], firm["gd_score"], firm["li_link"], firm["li_allstaff"], firm["li_jobsopen"]])
        for job in firm["jobs"]:
            jobs.append([job['company'], job['id_jobtitle'], job['id_joblink'], job["id_jobdesc"], job['id_daysopen'], job['id_location'], job["id_contact"], job["id_apply"], job["id_role"], job["id_stack_primary"], job["id_stack_secondary"], job["id_level"]])

    writeToSheet("Firms", firmHeader, firms)
    writeToSheet("Jobs", jobHeader, jobs)

# main()

results = fly(id_job_ROADMAP)["results"]
pprint(results)



