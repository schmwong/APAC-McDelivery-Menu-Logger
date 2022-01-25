import requests as r
from bs4 import BeautifulSoup as BS
import pandas as pd
import datetime as dt
import pytz
import re
from pathlib import Path # install pathlib2 instead of pathlib



# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Asia/Bangkok"))


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
XE = BS(session.get("https://www.xe.com/currencyconverter/convert/?Amount=1&From=THB&To=USD", headers=my_headers).content, "lxml")

# Scraping the text from the selected element (CSS selector)
# findall() and select() methods return a list, indicate index [0] to extract the first element as a string value
# Extracting only the number from the text string and converting it to a float value (decimal number) 
exchange_rate = float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", XE.select("p.result__BigRate-sc-1bsijpp-1.iGrAod")[0].text)[0])


# --------------------------------------- #
# List of URLS of Webpages to be Scraped  #
# --------------------------------------- #

start_URLs = [     
    "https://www.mcdonalds.co.th/mcDelivery/nonMember/category/promotion&lang=en" # All menus are on one page
]

# Populated by scraping href values of anchor tags
URL_list = []


breakfast_page = BS(session.get("https://www.mcdonalds.co.th/mcDelivery/nonMember/category/breakfast", headers=my_headers).content, "lxml")

# Used in If statements to verify if menu item is on the breakfast menu
breakfast_list = []

for food in breakfast_page.select("div.name"):
	breakfast_list.extend(food)

breakfast_list = [a.text for a in breakfast_list]

# -------------------------------------- #
# Parsing the data into Dictionary List  #
# -------------------------------------- #

# Initialising the list object [] to hold dictionaries {}
product_list = []


# Outer For Loop iterates through first category page of each menu type to get links to subsequent categories
for url in start_URLs:
	first_page = BS(session.get(url, headers=my_headers).content,"lxml")
	links = (a["href"] for a in (first_page.select("ul.food-head-list > div.desktop > li:not([class*='selected']) a[href]")))
	URL_list.extend(links)

	# Middle For Loop iterates through each menu item
	for products in first_page.select("div.food-container > div.grid"):
		i = 1 # for selecting specific price tags in (CSS ":nth-child()" selector), and to limit the While Loop's iterations

		# Inner For Loop iterates for each price tag of the menu item
		for prices in products.select("div.selling-price"):	

			# Nested While loop controls the number of iterations for each price tag
			while i <= len(products.select("div.selling-price")):
				
				product = {}
				product["Date"] = local_datetime.strftime("%Y/%m/%d")
				product["Day"] = local_datetime.strftime("%a")
				product["Territory"] = "Thailand"
				# If condition for variations between single ("Price") and double price tags ("A-la-carte" and "Set") 
				if "Price" in products.select("div.price div.grid-label")[0].text:
					product["Menu Item"] = products.select("div.name")[0].text
				else:
					product["Menu Item"] = ((products.select("div.name")[0].text) + f" " + f"(" + (products.select(f".price > div:nth-child({i}) > div.grid-label")[0].text) + f")")
				product["Price (THB)"] = round(float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)",products.select(f".price > div:nth-child({i}) > div.selling-price")[0].text)[0]), 2)
				product["Price (USD)"] = round((product["Price (THB)"] * exchange_rate), 2)
				product["Category"] = first_page.select("div.food-container > div.section-head")[0].text.strip()
				if ("Breakfast" in product["Category"]) or (product["Menu Item"] in breakfast_list):
					product["Menu"] = "Breakfast"
				else:
					product["Menu"] = "Regular"
				product_list.append(product)
				
				break
			
			i += 1


# Second Outer For Loop iterates through list of generated URLs
for url in URL_list:
	next_page = BS(session.get(url, headers=my_headers).content,"lxml")

  	# Middle For Loop iterates through each menu item
	for products in next_page.select("div.food-container > div.grid"):
		i = 1 # for selecting specific price tags in (CSS ":nth-child()" selector), and to limit the While Loop's iterations

		# Inner For Loop iterates for each price tag of the menu item
		for prices in products.select("div.selling-price"):	

			# Nested While loop controls the number of iterations
			while i <= len(products.select("div.selling-price")):
				
					product = {}
					product["Date"] = local_datetime.strftime("%Y/%m/%d")
					product["Day"] = local_datetime.strftime("%a")
					product["Territory"] = "Thailand"
					# If condition for variations between single ("Price") and double price tags ("A-la-carte" and "Set") 
					if "Price" in products.select("div.price div.grid-label")[0].text:
						product["Menu Item"] = products.select("div.name")[0].text
					else:
						product["Menu Item"] = ((products.select("div.name")[0].text) + f" " + f"(" + (products.select(f".price > div:nth-child({i}) > div.grid-label")[0].text) + f")")
					product["Price (THB)"] = round(float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)",products.select(f".price > div:nth-child({i}) > div.selling-price")[0].text)[0]), 2)
					product["Price (USD)"] = round((product["Price (THB)"] * exchange_rate), 2)
					product["Category"] = next_page.select("div.food-container > div.section-head")[0].text.strip()
					if ("Breakfast" in product["Category"]) or (product["Menu Item"] in breakfast_list):
						product["Menu"] = "Breakfast"
					else:
						product["Menu"] = "Regular"
					product_list.append(product)
					
					break
			
			i += 1


# ---------------------------------------------------- #
# Constructing the Dataframe and Exporting it to File  #
# ---------------------------------------------------- #

product_list_df = pd.DataFrame(product_list)
product_list_df.drop_duplicates(subset=None, keep='last', inplace=True, ignore_index=True)
product_list_df.reset_index(drop=True, inplace=True)
# product_list_df.index = pd.RangeIndex(start=1, stop=len(product_list_df) , step=1)

print(product_list_df)

timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

output_file = str(timestamp + " mcd-bs4-th.csv")
output_dir = Path("./scraped-data")

# Create directory as required; won't raise an error if directory already exists
output_dir.mkdir(parents=True, exist_ok=True)

product_list_df.to_csv((output_dir / output_file), float_format="%.2f", encoding="utf-8")

# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-bs4-th.csv"