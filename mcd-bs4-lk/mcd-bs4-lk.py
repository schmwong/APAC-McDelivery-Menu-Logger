import requests as r
from bs4 import BeautifulSoup as BS
import pandas as pd
import datetime as dt
import pytz
import re
from pathlib import Path # install pathlib2 instead of pathlib



# Reflects local time (SLST)
local_datetime = dt.datetime.now(pytz.timezone("Asia/Colombo"))


# Set headers to make HTTP request to seem to be from a normal browser
my_headers = {
    "Access-Control-Allow-Origin":"*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "3600",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36", 
    "Accept": "text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,image/apng,*/*;q=0.8"
}
              
session = r.Session()


# --------------------------------------- #
# Getting the Live Exchange Rate from XE  #
# --------------------------------------- #

# Getting the correct XE webpage (all elements)
XE = BS(session.get("https://www.xe.com/currencyconverter/convert/?Amount=1&From=LKR&To=USD", headers=my_headers).content, "lxml")

# Scraping the text from the selected element (CSS selector)
# Extracting only the number from the text string and converting it to a float value (decimal number) 
# findall() and select() methods return a list, indicate index [0] to extract the first element as a string value
exchange_rate = float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", XE.select("p.result__BigRate-sc-1bsijpp-1.iGrAod")[0].text)[0])


# --------------------------------------- #
# List of URLS of Webpages to be Scraped  #
# --------------------------------------- #

start_URLs = [     
    "https://www.mcdelivery.lk/lk/browse/menu.html?daypartId=1&catId=2", # Regular Menu
		"https://www.mcdelivery.lk/lk/browse/menu.html?daypartId=2&catId=2"  # Breakfast Menu
]

# Populated by scraping href values of anchor tags
URL_list = []

# -------------------------------------- #
# Parsing the data into Dictionary List  #
# -------------------------------------- #

# Initialising the list object [] to hold dictionaries {}
product_list = []


# Outer For Loop iterates through first category page of each menu type to get links to subsequent categories
for url in start_URLs:
	first_page = BS(session.get(url, headers=my_headers).content,"lxml")
	links = ("https://www.mcdelivery.lk/lk/browse/menu.html" + a["href"] for a in (first_page.select("li.secondary-menu-item:not([class*='selected']) a[href]")))
	URL_list.extend(links)

	# Inner For Loop scrapes the menu data from first category page
	for products in first_page.select("div.product-card"):
		product = {}
		product["Date"] = local_datetime.strftime("%Y/%m/%d")
		product["Day"] = local_datetime.strftime("%a")
		product["Territory"] = "Sri Lanka"
		product["Menu Item"] = products.select("h5.product-title")[0].text
		# Regex for currencies in large denominations with "," thousands separator
		product["Price (LKR)"] = float((re.findall(r"[-+]?(?:\d*\,\d+|\d+)",products.select("span.starting-price")[0].text)[0]).replace(",", ""))
		product["Price (USD)"] = round((product["Price (LKR)"] * exchange_rate), 2)
		product["Category"] = first_page.select("ol.breadcrumb > li.active")[0].text
		product["Menu"] = first_page.select("li.primary-menu-item.selected > a > span")[0].text
		product_list.append(product)


# Second Outer For Loop iterates through list of generated URLs
for url in URL_list:
	next_page = BS(session.get(url, headers=my_headers).content,"lxml")

	# Second Inner For Loop iterates through elements on all other pages
	for products in next_page.select("div.product-card"):
		product = {}
		product["Date"] = local_datetime.strftime("%Y/%m/%d")
		product["Day"] = local_datetime.strftime("%a")
		product["Territory"] = "Sri Lanka"
		product["Menu Item"] = products.select("h5.product-title")[0].text
		# Regex for currencies in large denominations with "," thousands separator
		product["Price (LKR)"] = float((re.findall(r"[-+]?(?:\d*\,\d+|\d+)",products.select("span.starting-price")[0].text)[0]).replace(",", ""))
		product["Price (USD)"] = round((product["Price (LKR)"] * exchange_rate), 2)
		product["Category"] = next_page.select("ol.breadcrumb > li.active")[0].text
		product["Menu"] = next_page.select("li.primary-menu-item.selected > a > span")[0].text
		product_list.append(product)


# ---------------------------------------------------- #
# Constructing the Dataframe and Exporting it to File  #
# ---------------------------------------------------- #

product_list_df = pd.DataFrame(product_list)
product_list_df.drop_duplicates(subset=None, keep='last', inplace=True, ignore_index=True)
product_list_df.reset_index(drop=True, inplace=True)

print(product_list_df)

timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

output_file = str(timestamp + " mcd-bs4-lk.csv")
output_dir = Path("./scraped-data")

# Create directory as required; won't raise an error if directory already exists
output_dir.mkdir(parents=True, exist_ok=True)

product_list_df.to_csv((output_dir / output_file), float_format="%.2f", encoding="utf-8")

# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-bs4-lk.csv"