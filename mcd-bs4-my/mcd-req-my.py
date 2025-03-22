import requests as r
from bs4 import BeautifulSoup as BS
import pandas as pd
import datetime as dt
import pytz
import re
import traceback
import json
from pathlib import Path

# Reflects UTC time with offset indicator
# local_datetime = pytz.timezone("Asia/Kuala_Lumpur").localize(dt.datetime.utcnow())

# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Asia/Kuala_Lumpur"))

# Set headers to make HTTP request to seem to be from a normal browser
json_headers = {
    'authority': 'hk.fd-api.com',
    'accept': 'application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
              '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-GB,en;q=0.9',
    'cache-control': 'max-age=0',
    'dnt': '1',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/102.0.5005.61 Safari/537.36'
}

my_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "3600",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,image/apng,*/*;q=0.8"
}

session = r.Session()

try:

    # --------------------------------------- #
    # Getting the Live Exchange Rate from XE  #
    # --------------------------------------- #

    # Getting the correct XE webpage (all elements)
    XE = BS(session.get("https://www.xe.com/currencyconverter/convert/?Amount=1&From=MYR&To=USD",
                        headers=my_headers).content, "lxml")

    # Scraping the text from the selected element (CSS selector)
    # Extracting only the number from the text string and converting it to a float value (decimal number)
    # findall() and select() methods return a list, indicate index [0] to extract the first element as a string value
    exchange_rate = float(
        re.findall(
            r"[-+]?(?:\d*\.\d+|\d+)",
            XE.select("span[class*=faded-digits]")[0].parent.text
        )[0]
    )

    print(
        f"\n\n1 MYR = {exchange_rate} USD (1 USD = {1 / exchange_rate} MYR) on {local_datetime.strftime('%A, %-d %B %Y')}"
    )

    # --------------------------------------------- #
    # URL of FoodPanda API for Mcdonald's Malaysia  #
    # --------------------------------------------- #

    url = "https://my.fd-api.com/api/v5/vendors/m6ig?include=menus,bundles,multiple_discounts&language_id=1&opening_type=delivery&basket_currency=MYR"

    # -------------------------------------- #
    # Parsing the data into Dictionary List  #
    # -------------------------------------- #

    # Initialising the list object [] to hold dictionaries {}
    product_list = []

    parsed_json = json.loads(session.get(url, headers=json_headers).content)["data"]

    print("\n\n----+----")
    print(f'McDo Outlet: {parsed_json["name"]}')
    print(f'Address: {parsed_json["address"]} {parsed_json["address_line2"]}'.strip())
    print(f'Order Page: {parsed_json["web_path"]}')
    print("----+----\n\n")

    submenus = parsed_json["menus"][0]["menu_categories"]
    for submenu in submenus:
        products = submenu["products"]
        for food in products:
            product = {}
            product["Date"] = local_datetime.strftime("%Y/%m/%d")
            product["Day"] = local_datetime.strftime("%a")
            product["Territory"] = "Malaysia"
            product["Menu Item"] = food["name"]
            product["Price (MYR)"] = "%.2f" % float(food["product_variations"][0]["price"])
            product["Price (USD)"] = round((float(product["Price (MYR)"]) * exchange_rate), 2)
            product["Category"] = submenu["name"]
            product["Menu"] = parsed_json["menus"][0]["name"]
            product_list.append(product)

    # ---------------------------------------------------- #
    # Constructing the Dataframe and Exporting it to File  #
    # ---------------------------------------------------- #

    product_list_df = pd.DataFrame(product_list)
    product_list_df.drop_duplicates(
        keep="first", inplace=True, ignore_index=True
    )
    product_list_df.index = pd.RangeIndex(
        start=1, stop=(len(product_list_df.index) + 1), step=1)

    print(product_list_df)

    timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

    output_file = str(timestamp + " mcd-req-my.csv")
    output_dir = Path("./scraped-data")

    # Create directory as required; won't raise an error if directory already exists
    output_dir.mkdir(parents=True, exist_ok=True)

    product_list_df.to_csv((output_dir / output_file),
                           float_format="%.2f", encoding="utf-8")

    print(f'''\n\nExported to file:
            https://github.com/schmwong/APAC-McDelivery-Menu-Logger/tree/main/mcd-bs4-my/scraped-data/{output_file.replace(" ", "%20")}\n\n ============ \n\n\n\n\n\n''')

# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-bs4-my.csv"

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
