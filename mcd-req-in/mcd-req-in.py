import requests
from bs4 import BeautifulSoup as BS  # only for parsing XE exchange rate
import pandas as pd
import datetime as dt
import pytz
import re
from pathlib import Path  # install pathlib2 instead of pathlib


# ################################################ #
#  Dynamic Site Scraping Using Requests Module:    #
#               ------------------                 #
# 	- HTML scraping returns empty values           #
#   - Observe Fetch/XHR activity in the            #
#      browser's DevTools Network tab              #
#   - Use XHR to get data via API endpoints        #
# ################################################ #


# Reflects local date and time (IST)
local_datetime = dt.datetime.now(pytz.timezone("Asia/Kolkata"))


# Set headers to make HTTP request to seem to be from a normal browser
json_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "3600",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    "Accept": "application/json; charset=utf-8"
}

my_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "3600",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,image/apng,*/*;q=0.8"
}


session = requests.Session()


# --------------------------------------- #
# Getting the Live Exchange Rate from XE  #
# --------------------------------------- #

# Getting the correct XE webpage (all elements)
XE = BS(session.get("https://www.xe.com/currencyconverter/convert/?Amount=1&From=INR&To=USD",
        headers=my_headers).content, "lxml")

# Scraping the text from the selected element (CSS selector)
# Extracting only the number from the text string and converting it to a float value (decimal number)
# findall() and select() methods return a list, indicate index [0] to extract the first element as a string value
exchange_rate = float(re.findall(
    r"[-+]?(?:\d*\.\d+|\d+)", XE.select("p.result__BigRate-sc-1bsijpp-1.iGrAod")[0].text)[0])


# --------------------------------------- #
# List of URLS of Webpages to be Scraped  #
# --------------------------------------- #

# Contains details of all Categories in a JSON object (as seen in DevTools > Network > XHR)
start_URL = "https://services.mcdelivery.co.in/api/product/category?OrderType=R&OrderTime=0&isLoggedIn=false&businessModelID=18&storeID=1"

# Populated by scraping categoryId key values from JSON object
category_id_list = []


# -------------------------------------- #
# Parsing the data into Dictionary List  #
# -------------------------------------- #

# Returns the JSON object as a Python dictionary
category_details = session.get(start_URL, headers=json_headers).json()


# Parsing the categoryId from the nested dictionaries
category_groups = category_details["data"]["category"]

for category_group in category_groups:
    for category in category_group["categoryGroup"]:
        category_id_list.append(category["categoryId"])


'''
length: 21
[{'id': 4607, 'title': 'New Launches'}, {'id': 4597, 'title': 'Trending'}, {'id': 4604, 'title': 'Deals'}, {'id': 4674, 'title': 'Gourmet Burgers'}, {'id': 4823, 'title': 'Gourmet Burger Meal'}, {'id': 4776, 'title': 'McSavers'}, {'id': 4779, 'title': 'NY Party Combos'}, {'id': 4600, 'title': 'Recommended'}, {'id': 2106, 'title': 'McBreakfast'}, {'id': 4316, 'title': 'Stay Home Combos'}, {'id': 1778, 'title': 'McBreakfast Meals'}, {'id': 3899, 'title': 'Meals'}, {'id': 667, 'title': 'Happy Meals'}, {'id': 4610, 'title': 'Family Meals'}, {'id': 659, 'title': 'Burgers & Wraps'}, {'id': 4611, 'title': 'Fries & Sides'}, {'id': 690, 'title': 'Desserts'}, {'id': 702, 'title': 'Beverages'}, {'id': 4612, 'title': 'Keep It Hot'}, {'id': 4613, 'title': 'Keep It Chill'}, {'id': 4814, 'title': 'Grab a Bite'}]
'''


# Initialising the list object [] to hold menu dictionaries {} we are about to create
product_list = []


# Getting menu data from all endpoints and adding it to product_list
# Outer For Loop gets menu data from each endpoint as a Python dictionary (from JSON response)
for id in category_id_list:
    endpoint = f"https://services.mcdelivery.co.in/Api/product/custommenu?CategoryID={id}"

    menu = session.get(endpoint, headers=json_headers).json()

    # Inner For Loop iterates for each menu item
    for products in menu["data"]:
        product = {}
        product["Date"] = local_datetime.strftime("%Y/%m/%d")
        product["Day"] = local_datetime.strftime("%a")
        product["Territory"] = "India"
        product["Menu Item"] = products["Title"].strip()
        # Price value already as float type in JSON object
        product["Price (INR)"] = products["DiscountedPrice"]
        product["Price (USD)"] = round(
            (product["Price (INR)"] * exchange_rate), 2)
        product["Category"] = products["CategoryName"]
        if ("Breakfast" or "McBreakfast") in product["Category"]:
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

timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

output_file = str(timestamp + " mcd-req-in.csv")
output_dir = Path("./scraped-data")

# Create directory as required; won't raise an error if directory already exists
output_dir.mkdir(parents=True, exist_ok=True)

product_list_df.to_csv((output_dir / output_file),
                       float_format="%.2f", encoding="utf-8")

# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-bs4-in.csv"
