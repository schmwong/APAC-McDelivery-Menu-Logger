import requests as r
from bs4 import BeautifulSoup as BS
import pandas as pd
import datetime as dt
import re


current_date = dt.datetime.now()


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
XE = BS(session.get("https://www.xe.com/currencyconverter/convert/?Amount=1&From=MYR&To=USD", headers=my_headers).content, "lxml")

# Scraping the text from the selected element (CSS selector)
# Extracting only the number from the text string and converting it to a float value (decimal number) 
# findall() and select() methods return a list, indicate index [0] to extract the first element as a string value
exchange_rate = float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", XE.select("p.result__BigRate-sc-1bsijpp-1.iGrAod")[0].text)[0])


# --------------------------------------- #
# List of URLS of Webpages to be Scraped  #
# --------------------------------------- #

start_URLs = [     
    "https://www.mcdelivery.com.my/my/browse/menu.html?daypartId=9&catId=74&locale=en", # Regular Menu
		"https://www.mcdelivery.com.my/my/browse/menu.html?daypartId=10&catId=74&locale=en"  # Breakfast Menu
]

# Populated by scraping href values of anchor tags
URL_list = []

# -------------------------------------- #
# Parsing the data into Dictionary List  #
# -------------------------------------- #

# Initialising the list object [] to hold dictionaries {}
product_list = []


# Outer loop iterates through first category page of each menu type to get links to subsequent categories
for url in start_URLs:
	first_page = BS(session.get(url, headers=my_headers).content,"lxml")
	links = ("https://www.mcdelivery.com.my/my/browse/menu.html" + a["href"] + "&locale=en" for a in (first_page.select("li.secondary-menu-item:not([class*='selected']) a[href]")))
	URL_list.extend(links)

	# Inner loop scrapes the menu data from first category page
	for products in first_page.select("div.product-card"):
		product = {}
		product["Date"] = current_date.strftime("%Y/%m/%d")
		product["Day"] = current_date.strftime("%a")
		product["Territory"] = "Malaysia"
		product["Menu Item"] = products.select("h5.product-title")[0].text
		product["Price (MYR)"] = float((re.findall(r"[-+]?(?:\d*\.\d+|\d+)",products.select("span.starting-price")[0].text)[0]))
		product["Price (USD)"] = round((product["Price (MYR)"] * exchange_rate), 2)
		product["Category"] = first_page.select("ol.breadcrumb > li.active")[0].text
		product["Menu"] = first_page.select("li.primary-menu-item.selected > a > span")[0].text
		product_list.append(product)


# Outer Loop iterates through list of generated URLs
for url in URL_list:
	next_page = BS(session.get(url, headers=my_headers).content,"lxml")

  # Inner loop iterates through elements on all other pages
	for products in next_page.select("div.product-card"):
		product = {}
		product["Date"] = current_date.strftime("%Y/%m/%d")
		product["Day"] = current_date.strftime("%a")
		product["Territory"] = "Malaysia"
		product["Menu Item"] = products.select("h5.product-title")[0].text
		product["Price (MYR)"] = float((re.findall(r"[-+]?(?:\d*\.\d+|\d+)",products.select("span.starting-price")[0].text)[0]))
		product["Price (USD)"] = round((product["Price (MYR)"] * exchange_rate), 2)
		product["Category"] = next_page.select("ol.breadcrumb > li.active")[0].text
		product["Menu"] = next_page.select("li.primary-menu-item.selected > a > span")[0].text
		product_list.append(product)


# ---------------------------------------------------- #
# Constructing the Dataframe and Exporting it to File  #
# ---------------------------------------------------- #

product_list_df = pd.DataFrame(product_list)

print(product_list_df)

timestamp = str(current_date.strftime("[%Y-%m-%d %H:%M:%S]"))

product_list_df.to_csv(f'./scraped-data/{str(timestamp + " mcd-bs4-my.csv")}', float_format="%.2f", encoding="utf-8")

# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-bs4-my.csv"