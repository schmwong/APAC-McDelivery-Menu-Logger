import requests as r
from bs4 import BeautifulSoup as BS
import pandas as pd
import datetime as dt
import pytz
import re
import traceback


# local_datetime = pytz.timezone("Asia/Singapore").localize(dt.datetime.utcnow())

# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Asia/Singapore"))


# Set headers to make HTTP request to seem to be from a normal browser
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
	XE = BS(session.get("https://www.xe.com/currencyconverter/convert/?Amount=1&From=SGD&To=USD",
	        headers=my_headers).content, "lxml")
	
	# Scraping the text from the selected element (CSS selector)
	# Extracting only the number from the text string and converting it to a float value (decimal number)
	# findall() and select() methods return a list, indicate index [0] to extract the first element as a string value
	exchange_rate = float(re.findall(
	    r"[-+]?(?:\d*\.\d+|\d+)", XE.select("p.result__BigRate-sc-1bsijpp-1.iGrAod")[0].text)[0])
	
	
	# ------------------------------------------- #
	# List of URLS of all Webpages to be Scraped  #
	# ------------------------------------------- #
	
	URL_list = [     # Regular Menu
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=21&catId=29",  # Promotion Meals
	    # Chicken McCrispy®
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=21&catId=63",
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=21&catId=66",  # Sharing
	    # Ala Carte & Value Meals
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=21&catId=30",
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=21&catId=31",  # Sides
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=21&catId=32",  # Desserts
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=21&catId=33",  # Beverages
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=21&catId=34",  # For the Family
	                 # Breakfast Menu
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=22&catId=29",  # Promotion Meals
	    # Breakfast & Value Meals
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=22&catId=30",
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=22&catId=31",  # Sides
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=22&catId=32",  # Desserts
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=22&catId=33",  # Beverages
	    "https://www.mcdelivery.com.sg/sg/browse/menu.html?daypartId=22&catId=34"  # For the Family
	]
	
	
	# -------------------------------------- #
	# Parsing the data into Dictionary List  #
	# -------------------------------------- #
	
	# Initialising the dictionary list object
	product_list = []
	
	
	# Outer loop iterates through list of webpages
	for url in URL_list:
	    response = session.get(url, headers=my_headers)
	    soup = BS(response.content, "lxml")
	
	    # Inner loop iterates through elements on each webpage
	    for products in soup.select("div.product-card"):
	        product = {}
	        product["Date"] = local_datetime.strftime("%Y/%m/%d")
	        product["Day"] = local_datetime.strftime("%a")
	        product["Territory"] = "Singapore"
	        product["Menu Item"] = products.select("h5.product-title")[0].text
	        product["Price (SGD)"] = float((re.findall(
	            r"[-+]?(?:\d*\.\d+|\d+)", products.select("span.starting-price")[0].text)[0]))
	        product["Price (USD)"] = round(
	            (product["Price (SGD)"] * exchange_rate), 2)
	        product["Category"] = soup.select("ol.breadcrumb > li.active")[0].text
	        product["Menu"] = soup.select(
	            "li.primary-menu-item.selected > a > span")[0].text
	        product_list.append(product)
	
	
	# ---------------------------------------------------- #
	# Constructing the Dataframe and Exporting it to File  #
	# ---------------------------------------------------- #
	
	product_list_df = pd.DataFrame(product_list)
	product_list_df.index = pd.RangeIndex(
	    start=1, stop=(len(product_list_df.index) + 1), step=1)
	
	print(product_list_df)
	
	timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))
	
	product_list_df.to_csv(
	    f'./scraped-data/{str(timestamp + " mcd-bs4-sg.csv")}', float_format="%.2f", encoding="utf-8")
	
	# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-bs4-sg.csv"


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
