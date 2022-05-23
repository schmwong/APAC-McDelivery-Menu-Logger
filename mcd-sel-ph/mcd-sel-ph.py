# pip install selenium
# pip install pandas
# pip install pathlib2


import time
import selenium
from selenium import webdriver

from selenium.webdriver.firefox.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import datetime as dt
import pytz
import pandas as pd
from pathlib import Path  # install pathlib2 instead of pathlib


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Asia/Manila"))


# configure webdriver
options = Options()
# configure chrome browser to not load images
# 0 = default, 1 = allow, 2 = block
prefs = {"profile.managed_default_content_settings.images": 2,
         "profile.default_content_setting_values.notifications": 2,
         "profile.managed_default_content_settings.stylesheets": 1,
         "profile.managed_default_content_settings.cookies": 1,
         "profile.managed_default_content_settings.javascript": 1,
         "profile.managed_default_content_settings.plugins": 1,
         "profile.managed_default_content_settings.popups": 2,
         "profile.managed_default_content_settings.geolocation": 2,
         "profile.managed_default_content_settings.media_stream": 2,
         }

################################################
# To run on Linux root without crashing
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
################################################

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("prefs", prefs)

browser = webdriver.Firefox(options=options)


# --------------------------------------- #
# Getting the Live Exchange Rate from XE  #
# --------------------------------------- #

# Getting the correct XE webpage (all elements)
XE = browser.get(
    "https://www.xe.com/currencyconverter/convert/?Amount=1&From=PHP&To=USD")

# Scraping the text from the selected element (CSS selector)
# findall() and select() methods return a list, indicate index [0] to extract the first element as a string value
# Extracting only the number from the text string and converting it to a float value (decimal number)
exchange_rate = float(re.findall(
    r"[-+]?(?:\d*\.\d+|\d+)", browser.find_element(By.CSS_SELECTOR, "p.result__BigRate-sc-1bsijpp-1.iGrAod").text)[0])

print(f"1 PHP = {exchange_rate} USD (1 USD = {1/exchange_rate} PHP) on {local_datetime.strftime('%A, %-d %B %Y')}")
# >> 1 PHP = 0.019133839 USD (1 USD = 52.2634271147 PHP) on 21 May 2022
print()


# ----------------------------------- #
#  Selecting the Biggest Mcdo Outlet  #
# ----------------------------------- #
# ref: https://thesmartlocal.com/philippines/mcdonalds-pampanga/

# -- Element Selectors -- #
SEARCH_BOX = (By.ID, "inputData")

Outlet_Address = "711 Capitol Boulevard, San Fernando, Pampanga, Philippines"

Alternate_Address = "1052 M. H. Del Pilar St, Ermita, Manila, 1000 Metro Manila, Philippines"

CONFIRM_BUTTON = (By.XPATH, "//button[contains(string(), 'Confirm')]")

DIALOG_CONFIRM_BUTTON = (By.XPATH, "//div[@class='pb-5']//button[contains(string(), 'Confirm')]")

DIALOG_SELECT_STORE = (By.XPATH, "//div[@class='pb-2' and not(contains(string(), 'Store is currently unavailable')) and contains(string(), 'Capital Town')]")

CLOSE_BUTTON = (By.CSS_SELECTOR, "div.text-right.pa-2 > button")

DIALOG_FALLBACK_STORE = (By.XPATH, "//div[@class='pb-2' and contains(string(), 'Un Del Pilar')]")

FINAL_CONFIRM_BUTTON = (By.XPATH, "//button[contains(string(), 'Confirm')]/..")


# -- Steps taken -- #
browser.get("https://www.mcdelivery.com.ph/account/location/")

WebDriverWait(browser, 100).until(
	EC.visibility_of_element_located(SEARCH_BOX)
).send_keys(Outlet_Address)

time.sleep(2)

WebDriverWait(browser, 10).until(
    EC.visibility_of_element_located(SEARCH_BOX)
).send_keys(Keys.DOWN, Keys.ENTER)

time.sleep(6)

WebDriverWait(browser, 10).until(
    EC.element_to_be_clickable(CONFIRM_BUTTON)
).click()

time.sleep(6)

WebDriverWait(browser, 10).until(
	EC.visibility_of_element_located(DIALOG_CONFIRM_BUTTON)
).click()

time.sleep(6)

try:
	WebDriverWait(browser, 10).until(
    EC.element_to_be_clickable(DIALOG_SELECT_STORE)
	).click()

except:
	WebDriverWait(browser, 10).until(
			EC.element_to_be_clickable(CLOSE_BUTTON)
	).click()

	WebDriverWait(browser, 10).until(
			EC.visibility_of_element_located(SEARCH_BOX)
	).clear()

	WebDriverWait(browser, 10).until(
			EC.visibility_of_element_located(SEARCH_BOX)
	).send_keys(Alternate_Address)

	time.sleep(2)

	WebDriverWait(browser, 10).until(
			EC.visibility_of_element_located(SEARCH_BOX)
	).send_keys(Keys.DOWN, Keys.ENTER)

	time.sleep(6)

	WebDriverWait(browser, 10).until(
			EC.element_to_be_clickable(CONFIRM_BUTTON)
	).click()

	time.sleep(6)

	WebDriverWait(browser, 10).until(
			EC.element_to_be_clickable(DIALOG_CONFIRM_BUTTON)
	).click()

	WebDriverWait(browser,10).until(
		EC.element_to_be_clickable(DIALOG_FALLBACK_STORE)
	).click()

time.sleep(12)

try:
	WebDriverWait(browser, 10).until(
    EC.element_to_be_clickable(FINAL_CONFIRM_BUTTON)
	).click()

except:
	browser.refresh()
		
time.sleep(4)


# -------------------------------------- #
# Parsing the data into Dictionary List  #
# -------------------------------------- #


browser.get("https://www.mcdelivery.com.ph/menu/")

time.sleep(5)

breakfast_list = []
category_id_list = []
item_list = []
price_list = []
category_list = []
product_list = []


# Get ID of each Category section element
submenus = browser.find_elements(By.CSS_SELECTOR, "div#card section")

for submenu in submenus:
    category_id = submenu.get_attribute("id")
    category_id_list.append(category_id)


# Outer For Loop iterates through each Category section
for ID in category_id_list:

    # Inner For Loops scrape (text from the corresponding elements) for
    # menu items and prices into individual lists
		try:
				if "Breakfast" in ID:
					breakfast_items = browser.find_elements(
                By.XPATH, f'//*[@id="{ID}"]//div[contains(@class, "PRODUCT__NAME")]')
								# f'//*[@id="{ID}"]/div/div[2]/div/div/div/div[2]/div'
					for breakfast_item in breakfast_items:
						breakfast_item_text = breakfast_item.text
						breakfast_list.append(breakfast_item_text)
	
		except:
				pass
		
		finally:
			menu_items = browser.find_elements(
	        By.XPATH, f'//*[@id="{ID}"]//div[contains(@class, "PRODUCT__NAME")]')
					# f'//*[@id="{ID}"]/div/div[2]/div/div/div/div[2]/div'
			for menu_item in menu_items:
					menu_item_text = menu_item.text
					item_list.append(menu_item_text)
				
			prices = browser.find_elements(
	        By.XPATH, f'//*[@id="{ID}"]//span[contains(@class, "peso-sign")]/..')
					# Parent element selector: /.. is shorthand for /parent::*
					# f'//*[@id="{ID}"]/div/div[2]/div/div/div/div[3]/div'
			for price in prices:
					price_text = round(
							float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", price.text)[0]), 2
					)
					price_list.append(price_text)
	
# Nested to match each menu item with its Category
					category_text = ID
					category_list.append(category_text)


# Zip function merges lists in parallel
# Consolidating all the information: output each row of the menu into a {product dictionary}, then adding the {dictionary} to the [product_list]
for menu_item_text, price_text, category_text in zip(item_list, price_list, category_list):
		product = {}
		product["Date"] = local_datetime.strftime("%Y/%m/%d")
		product["Day"] = local_datetime.strftime("%a")
		product["Territory"] = "Philippines"
		product["Menu Item"] = menu_item_text
		product["Price (PHP)"] = price_text
		product["Price (USD)"] = round((price_text * exchange_rate), 2)
		product["Category"] = category_text
	
		if ("Breakfast" in category_text):
				product["Menu"] = "Breakfast"
		elif (menu_item_text in breakfast_list):
				product["Menu"] = "Breakfast"
		else:
				product["Menu"] = "Regular"
		product_list.append(product)


# ---------------------------------------------------- #
# Constructing the Dataframe and Exporting it to File  #
# ---------------------------------------------------- #

product_list_df = pd.DataFrame(product_list)
product_list_df.drop_duplicates(
    subset=None, keep='last', inplace=True, ignore_index=True)
product_list_df.reset_index(drop=True, inplace=True)
product_list_df.index = pd.RangeIndex(
    start=1, stop=(len(product_list_df.index) + 1), step=1)

print(product_list_df)
print()

timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

output_file = str(timestamp + " mcd-sel-ph.csv")
output_dir = Path("./scraped-data")

# Create directory as required; won't raise an error if directory already exists
output_dir.mkdir(parents=True, exist_ok=True)

product_list_df.to_csv((output_dir / output_file),
                       float_format="%.2f", encoding="utf-8")

# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-sel-ph.csv"


time.sleep(5)

browser.quit()
