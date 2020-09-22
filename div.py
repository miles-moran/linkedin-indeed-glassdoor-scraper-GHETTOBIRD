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
    "race_dict": {}
}

inputAlias = "Diversity Input"

diversity_header = ["company",  "li_link", "li_allstaff", "private", "public", "names", 'foreign', 'non_foreign', "diversity_rating", "HHI", ""]

race_list = []

def scroll():
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
        if new_height == last_height:
            break
        last_height = new_height



def getSheetData(sheet):
    s = client.open("Indeed v2").worksheet(sheet)
    data = s.get_all_records()
    return data


def handleSettings():
    data = getSheetData("Settings")
    settings["li_username"] = data[4]["value"]
    settings["li_password"] = data[5]["value"]
    races = getSheetData('Diversity Hidden')[0]
    settings["race_dict"] = races
    for race in list(races.keys()):
        diversity_header.append(race)
        race_list.append(race)


def writeToSheet(sheet, header, data):
    if len(data) > 0:
        client.login()
        s = client.open("Indeed v2").worksheet(sheet)
        book = client.open("Indeed v2")
        book.values_clear(sheet + "!A1:Z10000")
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
        url = f["li_link"] + "/people?keywords=germany"
        browser.get(url)
        time.sleep(3)
        scroll()
        time.sleep(1)
        nameEls = browser.find_elements_by_xpath(
            "//div[@class='artdeco-entity-lockup__title ember-view']")
        for name in nameEls:
            if name.text != 'LinkedIn Member':
                f["public"] += 1
                split = name.text.split(" ")
                if len(split) < 2:
                    continue
                f["names"] += name.text + ", "
                first = split[0]
                last = split[1]
                f["formattedNames"].append({'first': first, 'last': last})
                f["li_allstaff"] += 1
            else:
                f["private"] += 1
                f["li_allstaff"] += 1
        analysis = analyzeRace(f["formattedNames"])
        races = {}
        HHI = 1
        for race in race_list:
            if race in list(analysis.keys()):
                foreign = settings["race_dict"][race] == 'Yes'
                races[race] = analysis[race]
                if foreign == True:
                    count = analysis[race]
                    f['foreign'] += count
                    HHI = HHI - ((count / f["public"]) * (count / f["public"]))
                else:
                    f['non-foreign'] += analysis[race]
            else:
                races[race] = 0 
        HHI = HHI - ((f['non-foreign'] / f["public"]) * (f['non-foreign'] / f["public"]))
        f["HHI"] = HHI
        f["percentage"] = f["foreign"] / f["public"]
        pprint(HHI)
        row = [f["company"], f["li_link"], f["li_allstaff"], f["private"], f["public"], f["names"], f['foreign'], f['non-foreign'], f["percentage"], f["HHI"], ""]
        for race in race_list:
            row.append(races[race])
        firms.append(row)
    writeToSheet("Diversity", diversity_header, firms)

scrape()

