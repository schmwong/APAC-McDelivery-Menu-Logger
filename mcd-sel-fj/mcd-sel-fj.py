# pip install selenium
# pip install pandas
# pip install pathlib2


import time
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import datetime as dt
import pytz
import pandas as pd
from pathlib import Path  # install pathlib2 instead of pathlib
import traceback


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Pacific/Fiji"))
Date = local_datetime.strftime("%Y/%m/%d")
Day = local_datetime.strftime("%a")


# configure webdriver
options = Options()
################################################
# To run on Linux root without crashing
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
################################################

# configure browser to not load images
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

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("prefs", prefs)

browser = webdriver.Firefox(options=options)


try:

    # --------------------------------------- #
    # Getting the Live Exchange Rate from XE  #
    # --------------------------------------- #

    # Getting the correct XE webpage (all elements)
    XE = browser.get(
        "https://www.xe.com/currencyconverter/convert/?Amount=1&From=FJD&To=USD")

    # Scraping the text from the selected element (CSS selector)
    # findall() and select() methods return a list, indicate index [0] to extract the first element as a string value
    # Extracting only the number from the text string and converting it to a float value (decimal number)
    exchange_rate = float(re.findall(
        r"[-+]?(?:\d*\.\d+|\d+)", browser.find_element(By.CSS_SELECTOR, "p.result__BigRate-sc-1bsijpp-1.iGrAod").text)[0])

    print(exchange_rate)
    print()

    # -------------------------------------- #
    # Parsing the data into Dictionary List  #
    # -------------------------------------- #

    # Vendor updated page URL
    browser.get("https://fijieats.com/vendor/mcdonalds-nadi")

    time.sleep(6)

    product_list = []

    # Revamped page has menu items split across different html section elements
    submenus = browser.find_elements(
        By.CSS_SELECTOR, "section.scrolling_section"
    )

    # Outer For Loop iterates through each section element
    for submenu in submenus:

        # Category Names should only contain alphabetical characters
        category_id = submenu.get_attribute("id")
        category = " ".join(
            re.findall(
                r"[a-zA-Z]+",
                ((browser.find_element(
                    By.CSS_SELECTOR,
                    f'nav.scrollspy-menu a[href="#{category_id}"]'
                )).text)
            )
        )

        items = submenu.find_elements(By.CSS_SELECTOR, "div.price_head")

        # Inner For Loop iterates through each div containing a Menu Item
        for item in items:
            product = {}
            product["Date"] = Date
            product["Day"] = Day
            product["Territory"] = "Fiji"
            product["Menu Item"] = (item.find_element(
                By.CSS_SELECTOR, "h5")).text.strip()
            product["Price (FJD)"] = round(
                float(
                    re.findall(
                        r"[-+]?(?:\d*\.\d+|\d+)",
                        (item.find_element(By.CSS_SELECTOR, "p.product_price").text)
                    )[0]
                ), 2
            )
            product["Price (USD)"] = round(
                (product["Price (FJD)"] * exchange_rate), 2
            )
            product["Category"] = category
            if ("Breakfast" in category):
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

    output_file = str(timestamp + " mcd-sel-fj.csv")
    output_dir = Path("./scraped-data")

    # Create directory as required; won't raise an error if directory already exists
    output_dir.mkdir(parents=True, exist_ok=True)

    product_list_df.to_csv((output_dir / output_file),
                           float_format="%.2f", encoding="utf-8")

    # Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-sel-fj.csv"

    time.sleep(5)

    browser.quit()


except Exception:
    print(
        f'''
	  \n\n
	  ---
	  One or more errors occurred:
	  
	  {traceback.format_exc()}
	  ---
	  \n\n
	  '''
    )
