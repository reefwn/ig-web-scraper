from bs4 import BeautifulSoup
import csv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import os

##################### Options ########################

# start from 1 to 10, each batch will scrape for 100 accounts
# (should do it in order because it will append at the end of the csv file)
BATCH_NUMBER = 1

# get scrape url country from this url
# https://starngage.com/app/global/influencer/ranking/
TOP1000_URL = 'https://starngage.com/app/global/influencer/ranking/'
COUNTRY = 'thailand'

# user & password for login, can give an empty string if do not want to login for scraping
# scraping with login will get more images for each user
IG_USERNAME = ''
IG_PASSWORD = ''

# these chrome options will disable GUI display for automation
# remove these options if you want to see how it scrapes through pages
# without these options, it is not working fine
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

######################################################

IG_URL = 'https://www.instagram.com'

try:
    chrome_options
except:
    wd = webdriver.Chrome('./chromedriver')
else:
    wd = webdriver.Chrome('./chromedriver', options=chrome_options)

def exportcsv(data, filename):
    folder = 'dataset'
    path = '{}/{}.csv'.format(folder, filename)
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open('dataset/{}.csv'.format(filename), 'a+', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

# scrape instagram accounts
def scrapeaccounts(ig_accounts, index):
    csvaccounts = [['id', 'account', 'posts', 'followers', 'follwings']] if index == 1 else []
    csvengagements = [['id', 'likes', 'comments']] if index == 1 else []
    for account in ig_accounts:

        print("scraping {}'s account (id = {})".format(account, index))
        wd.get('{}/{}'.format(IG_URL, account))
        try:
            images = WebDriverWait(wd, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '._9AhH0'))
            )
            info = WebDriverWait(wd, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.k9GMp'))
            )

            general = info.text.split()
            csvaccounts.append([
                index,
                account,
                general[0],
                general[2],
                general[4]
            ])

            wd.execute_script('window.scrollTo(0, 1000)')
            time.sleep(1)
            images = wd.find_elements_by_css_selector('.v1Nh3.kIKUG._bz0w')

            for item in images:
                hover = ActionChains(wd).move_to_element(item)
                wd.implicitly_wait(1)
                hover.perform()
                wd.implicitly_wait(1)

                try:
                    lpc = item.find_element_by_class_name('Ln-UN')
                    lc = lpc.text.split()
                    if len(lc) == 1:
                        lc.append(0)

                    csvengagements.append([
                        index,
                        lc[0],
                        lc[1]
                    ])
                finally:
                    continue
        finally:
            index += 1
            continue

    return csvaccounts, csvengagements

# login to instagram
def login():
    wd.get(IG_URL)
    username = WebDriverWait(wd, 10).until(
        EC.presence_of_element_located((By.NAME, 'username'))
    )
    username.send_keys(IG_USERNAME)
    password = WebDriverWait(wd, 10).until(
        EC.presence_of_element_located((By.NAME, 'password'))
    )
    password.send_keys(IG_PASSWORD)
    loginbtn = WebDriverWait(wd, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[type="submit"]'))
    )
    loginbtn.click()
    # searchbar is used to wait for login to complete
    search = WebDriverWait(wd, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[placeholder="Search"]'))
    )
    return search

# get top 1000 instagram accounts in the country
def getaccounts(i):
    ig_accounts = []
    url = '{}{}?page={}'.format(TOP1000_URL, COUNTRY, i)
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table').find('tbody')
    tr = table.find_all('tr')
    for j in range(len(tr)):
        td = tr[j].find_all('td')
        account = td[2].text.split('@')[-1].strip()
        ig_accounts.append(account)
    return ig_accounts

def main():
    print('start scraping ...')
    ig_accounts = getaccounts(BATCH_NUMBER)
    if IG_USERNAME and IG_PASSWORD:
        searchbar = login()
    id_number = ((BATCH_NUMBER - 1) * 100) + 1
    data1, data2 = scrapeaccounts(ig_accounts, id_number)
    exportcsv(data1, 'accounts')
    exportcsv(data2, 'engagements')

    return print('scraping is completed')
    

if __name__ == '__main__':
    main()
