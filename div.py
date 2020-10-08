from pprint import pprint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import sys
from datetime import datetime
from ghettobird import basic_method_A, basic_method_B, basic_method_C, master_method_selenium, fly
from ethnicolr import census_ln, pred_census_ln, pred_wiki_name
import pandas as pd


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
client = gspread.authorize(creds)

chromedriver_location = 'c:/chromedriver.exe'
browser = webdriver.Chrome(executable_path=chromedriver_location)

settings = {
    "li_username": "",
    "li_password": "",
    "div_scroll_depth": 15,
    "race_list": ["Asian,GreaterEastAsian,EastAsian", "Asian,GreaterEastAsian,Japanese", "Asian,IndianSubContinent", "GreaterAfrican,Africans", "GreaterAfrican,Muslim", "GreaterEuropean,British", "GreaterEuropean,EastEuropean", "GreaterEuropean,Jewish", "GreaterEuropean,WestEuropean,French"	, "GreaterEuropean,WestEuropean,Germanic", "GreaterEuropean,WestEuropean,Hispanic", "GreaterEuropean,WestEuropean,Italian", "GreaterEuropean,WestEuropean,Nordic"]
}

inputAlias = "Diversity Input"

diversity_header = ["company",  "li_link", "li_allstaff", "private", "public", "names", "", "Asian,GreaterEastAsian,EastAsian", "Asian,GreaterEastAsian,Japanese", "Asian,IndianSubContinent", "GreaterAfrican,Africans", "GreaterAfrican,Muslim", "GreaterEuropean,British", "GreaterEuropean,EastEuropean", "GreaterEuropean,Jewish", "GreaterEuropean,WestEuropean,French"	, "GreaterEuropean,WestEuropean,Germanic", "GreaterEuropean,WestEuropean,Hispanic", "GreaterEuropean,WestEuropean,Italian", "GreaterEuropean,WestEuropean,Nordic"]

def scroll(depth):
    SCROLL_PAUSE_TIME = 2
    last_height = browser.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)
        # Calculate new scroll height and compare with last scroll height
        new_height = browser.execute_script(
            "return document.body.scrollHeight")
        if new_height == last_height or depth == 0:
            break
        last_height = new_height
        depth = depth - 1



def getSheetData(sheet):
    s = client.open("Indeed v2").worksheet(sheet)
    data = s.get_all_records()
    return data


def handleSettings():
    data = getSheetData("Settings")
    settings["li_username"] = data[4]["value"]
    settings["li_password"] = data[5]["value"]
    settings["div_scroll_depth"] = data[6]["value"]
    print(data[6]["value"])

def logExecution():
    now = datetime.now() 
    time = now.strftime("%H:%M:%S, %m/%d/%Y")
    s = client.open("Indeed v2").worksheet(inputAlias)
    s.update_cell(1, 7, time)

def writeToSheet(sheet, header, data):
    if len(data) > 0:
        client.login()
        s = client.open("Indeed v2").worksheet(sheet)
        book = client.open("Indeed v2")
        book.values_clear(sheet + "!A1:U10000")
        data.insert(0, header)
        cells = []
        for row_num, row in enumerate(data):
            for col_num, cell in enumerate(row):
                cells.append(gspread.Cell(
                    row_num + 1, col_num + 1, data[row_num][col_num]))
        s.update_cells(cells)

def login(browser):
    browser.get("https://www.linkedin.com/login")
    time.sleep(2)
    username = browser.find_element_by_xpath('//input[@id="username"]')
    password = browser.find_element_by_xpath('//input[@id="password"]')
    username.send_keys(settings["li_username"])
    password.send_keys(settings["li_password"])
    browser.find_element_by_xpath('//button[@type="submit"]').click()

def analyzeRace(names):
    df = pd.DataFrame(names)
    races = {}
    results = pred_wiki_name(df, 'last', 'first')
    pprint(results)
    for race in results['race']:
        if race in list(races.keys()):
            races[race] += 1
        else:
            races[race] = 1
    return races

def TRANSFORM_clean_li_allstaff(element):
    time.sleep(2)
    scroll(settings["div_scroll_depth"])
    return element.text.split(" ")[0]

li_roadmap_ROADMAP = {
    "url": "https://www.linkedin.com/company/adjustcom/people?keywords=germany",
    "method": {
        "type": master_method_selenium,
        "browser": browser,
        "sleep": 3
    },
    "flightpath": {
        "li_allstaff": {
            "path": "//span[@class='t-20 t-black']",
            "transformer": TRANSFORM_clean_li_allstaff
        },
        "names": [{
            "path": "//li[@class='org-people-profiles-module__profile-item']",
             "name": {
                "path": ".//div[@class='artdeco-entity-lockup__title ember-view']",
             },
        }]
     }
}

def scrape():
    handleSettings()
    login(browser)
    inputSpreadsheet = getSheetData(inputAlias)
    firms = []
    for firmInput in inputSpreadsheet:
        races = {
            "Asian,GreaterEastAsian,EastAsian": 0,
            "Asian,GreaterEastAsian,Japanese":0,
            "Asian,IndianSubContinent": 0,
            "GreaterAfrican,Africans": 0,
            "GreaterAfrican,Muslim": 0,
            "GreaterEuropean,British": 0,
            "GreaterEuropean,EastEuropean": 0,
            "GreaterEuropean,Jewish": 0,
            "GreaterEuropean,WestEuropean,French": 0,
            "GreaterEuropean,WestEuropean,Germanic": 0,
            "GreaterEuropean,WestEuropean,Hispanic": 0,
            "GreaterEuropean,WestEuropean,Italian": 0, 
            "GreaterEuropean,WestEuropean,Nordic": 0
        }
        f = {
            "company": firmInput["company"],
            "li_link": firmInput["li_link"],
            "private": 0,
            "public": 0,
            "names": "",
            "formattedNames": [],
            "li_allstaff": 0,
            "foreign": 0,
            "non-foreign": 0
        }
        link_or_names = f["li_link"]
        if "http://" in link_or_names or "https://" in link_or_names:
            try:
                url = link_or_names + "/people?facetGeoRegion=de%3A0"
                li_roadmap_ROADMAP["url"] = url
                results = fly(li_roadmap_ROADMAP)["results"]
                if results["li_allstaff"] == None or results["li_allstaff"] == "":
                    results = fly(li_roadmap_ROADMAP)["results"]
                f["li_allstaff"] = results['li_allstaff']
                for name in results["names"]:
                    name = name["name"]
                    if name != "LinkedIn Member":
                        f["public"] += 1
                        f["names"] += name + ", "
                        split = name.split(" ")
                        first = split[0]
                        last = split[1]
                        f["formattedNames"].append({'first': first, 'last': last})
                    else:
                        f["private"] += 1
                pprint(f["formattedNames"])
                analysis = analyzeRace(f["formattedNames"])
                pprint(analysis)
                for race in settings["race_list"]:
                    if race in list(analysis.keys()):
                        races[race] = analysis[race]
            except Exception as e:
                print(url)
                print(e)
        else:
            try:
                names = link_or_names.split(",")
                f["li_allstaff"] = len(names)
                f["public"] = len(names)
                f["names"] += link_or_names
                for name in names:
                    split = name.split(" ")
                    first = split[0]
                    last = split[1]
                    f["formattedNames"].append({'first': first, 'last': last})
                    pprint(f["formattedNames"])
                    analysis = analyzeRace(f["formattedNames"])
                    for race in settings["race_list"]:
                        if race in list(analysis.keys()):
                            races[race] = analysis[race]
            except Exception as e:
                print(link_or_names)
                print(e)
        row = [f["company"], f["li_link"], f["li_allstaff"], f["private"], f["public"], f["names"], ""]
        for race in settings["race_list"]:
            row.append(races[race])
        firms.append(row)
    writeToSheet("Diversity", diversity_header, firms)
    logExecution()

scrape()

