from pprint import pprint
import json
import time
from lxml import html
import requests
import copy
import csv
def getTree(URL):
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
        'Accept-Language': 'en-gb',
        'Accept-Encoding': 'br, gzip, deflate',
        'Accept': 'test/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    try:
        r = requests.get(URL, headers=headers, timeout=10)
        tree = html.fromstring(r.content.decode("utf-8", "replace"))
        return tree
    except Exception as e:
        print(e)
        return None

def fly(routine):
    routine["log"] = []
    routine["results"] = routine["method"]["type"](routine)
    return routine

def writeRow(filename, row):
     with open('{}.csv'.format(filename),'a', encoding='utf-8') as j:
        writer = csv.writer(j, lineterminator = '\n')
        try:
            writer.writerow(row)
        except Exception as e:
            print(e)
            print("failure to write to CSV")

#scrapes elements based off of field selectors
def basic_method_A(routine):
    tree = getTree(routine["url"])
    structure = routine["structure"]
    data = [] 
    count = None 
    keys = structure.keys()

    for field in keys:
        try:
            elements = tree.xpath(structure[field]["path"])
            structure[field]["elements"] = elements
            length = len(elements)
            if count == None:
                count = length
            else:
                if length != count:
                    print ("error - number of elements differ per item.")
                    return None
        except Exception as e:
            print(e)
            return None

    for l in range(0, count):
        obj = {}
        for field in keys:
            if "transformer" in structure[field].keys():
                obj[field] = structure[field]["transformer"](structure[field]["elements"][l])
            else:
                obj[field] = structure[field]["elements"][l].text 
        data.append(obj)
    
    return data

def basic_method_B(routine):
    def explore(data, tree, roadmap, depth, root):
        items = roadmap.items()
        for branch in tree:
            if depth == 1:
                root = branch
                data[root] = {}
            fields = {}
            for item in items:
                key = item[0]
                obj = item[1]
                if key == "value":
                    return True
                leaf = branch.xpath(key)
                valueFound = explore(data, leaf, obj, depth + 1, root)
                if valueFound == True:
                    element = branch.xpath(key)
                    transformer = obj["transformer"]
                    value = transformer(element[0])
                    fields[obj["value"]] = value
                    if depth == 1:
                        data[root] = {**data[root], **fields}
                    if depth > 1:
                        data[root] = {**data[root], **fields}
        return data
        
    tree = getTree(routine["url"])
    roadmap = routine["structure"]
    data = explore({}, [tree], roadmap, 0, None)
    return list(data.values())

#scrapes fields through a script in the header
def basic_method_C(routine):
    tree = getTree(routine["url"])
    keys = routine["structure"].keys()
    methods = routine["method"].keys()
    script = ""
    data = {}
    if "head" in methods and "tail" in methods:
        head = routine["method"]["head"]
        tail = routine["method"]["tail"]
        scripts = tree.xpath('//script')
        for s in scripts:
            raw = s.text
            if head in str(raw):
                raw = raw.replace(head, "")
                raw = raw.replace(tail, "")
                script = raw
                break
    else:
        try:
            script = tree.xpath(routine["method"]["script"])[0].text
        except:
            return None
    try:
        raw = script.encode('utf-8')
        script = json.loads(raw, strict=False)
    except Exception as e:
        raw = script.encode('ascii', 'ignore').decode('unicode_escape')
        script = json.loads(raw, strict=False)
        print("error while encoding json")
        print(e)
    for field in keys:
        path = routine["structure"][field]["path"]
        route = script
        for p in path:
            if p in route.keys():
                route = route[p]
            else:
                print("{} not found".format(p))
                route = ""
                break
                #needs to error more gracefully, fieldn eeds to be empty, but right now its a clusterfuck
        if "transformer" in routine["structure"][field].keys() and route != "":
            data[field] = routine["structure"][field]["transformer"](route)
        else:
            data[field] = route
    return data 

def master_method_selenium(flight):
    browser = flight["method"]["browser"]
    def explore(tree, flightpath, log):
        flightpathCopy = copy.deepcopy(flightpath)
        keys = flightpathCopy.keys()
        for key in keys:
            obj = flightpathCopy[key]
            typeOfObj = type(obj)
            if typeOfObj == dict:
                innerKeys = obj.keys()
                if "path" in innerKeys:
                    element = None
                    try:
                        element = tree.find_element_by_xpath(obj["path"])
                    except Exception as e: 
                        time.sleep(5)
                        try:
                            element = tree.find_element_by_xpath(obj["path"])
                        except:
                            log.append("{} | {} element not found.".format(e, key))
                            flightpathCopy[key] = ""
                            continue
                    try:
                        if "transformer" in innerKeys:
                            flightpathCopy[key] = obj["transformer"](element)
                        else:
                            flightpathCopy[key] = element.text
                    except Exception as e: 
                        log.append("{} | {} transformer function failed.".format(e, key))
                        flightpathCopy[key] = ""
                else:
                    flightpathCopy[key] = explore(tree, obj, log)
            if typeOfObj == list:
                profile = {}
                try:
                    profile = obj[0]
                except Exception as e: 
                    log.append("{} | {} list is empty.".format(e, key))
                    flightpathCopy[key] = []
                    continue
                path = "//body"
                branch = None
                if "path" in profile.keys():
                    path = profile.pop("path")
                branches = tree.find_elements_by_xpath(path)
                if len(branches) == 0:
                    time.sleep(5)
                    branches = tree.find_elements_by_xpath(path)
                    if len(branches) == 0:
                        log.append("{} container element for list not found".format(key))
                        flightpathCopy[key] = []
                        continue
                leaves = []
                for branch in branches:
                    leaves.append(explore(branch, profile, log))
                flightpathCopy[key] = leaves
        return flightpathCopy

    browser.get(flight["url"])
    time.sleep(3)
    captchaExists = len(browser.find_elements_by_xpath("//*[contains(text(),'do a quick security check')]")) > 0
    loginExists = len(browser.find_elements_by_xpath("//*[contains(text(),'Sign In')]")) > 0
    if captchaExists or loginExists:
        input("--Captcha Detected--") 
    tree = browser.find_element_by_xpath("//html")
    results = explore(tree, flight["flightpath"], flight["log"])
    return results