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

def scrape():
    handleSettings()
    login(browser)
    inputSpreadsheet = getSheetData(inputAlias)
    firms = []
    for firmInput in inputSpreadsheet:
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
        try:
            url = f["li_link"] + "/people?keywords=germany"
            browser.get(url)
            time.sleep(3)
            captchaExists = len(browser.find_elements_by_xpath("//*[contains(text(),'do a quick security check')]")) > 0
            loginExists = len(browser.find_elements_by_xpath("//*[contains(text(),'Sign up for free to get more')]")) > 0
            if captchaExists or loginExists:
                input("--Captcha Detected--") 
                time.sleep(3)
                browser.get(url)
                time.sleep(3)
            try:
                f["li_allstaff"] = browser.find_element_by_xpath("//span[@class='t-20 t-black']").text.split(" ")[0]
            except:
                f["li_allstaff"] = 0
            container = browser.find_element_by_xpath("//ul[@class='org-people-profiles-module__profile-list']")
            scroll(15)
            time.sleep(1)
            nameEls = container.find_elements_by_xpath(
                "/div[@class='artdeco-entity-lockup__title ember-view']")
            for name in nameEls:
                if name.text != 'LinkedIn Member':
                    f["public"] += 1
                    split = name.text.split(" ")
                    print(split)
                    if len(split) < 2:
                        continue
                    f["names"] += name.text + ", "
                    first = split[0]
                    last = split[1]
                    f["formattedNames"].append({'first': first, 'last': last})
                else:
                    f["private"] += 1
            analysis = analyzeRace(f["formattedNames"])
            races = {}
            for race in settings["race_list"]:
                if race in list(analysis.keys()):
                    races[race] = analysis[race]
                else:
                    races[race] = 0
        except Exception as e:
            print(url)
            print(e)
        row = [f["company"], f["li_link"], f["li_allstaff"], f["private"], f["public"], f["names"], ""]
        for race in settings["race_list"]:
            row.append(races[race])
        firms.append(row)
    writeToSheet("Diversity", diversity_header, firms)
    logExecution()

scrape()

