import requests as r
from bs4 import BeautifulSoup as BS
import pandas as pd
import datetime as dt
import pytz
import re
from pathlib import Path  # install pathlib2 instead of pathlib
import traceback
from time import time


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Asia/Bangkok"))


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

  start = time()
	
  # --------------------------------------- #
  # Getting the Live Exchange Rate from XE  #
  # --------------------------------------- #
	
  # Getting the correct XE webpage (all elements)
  XE = BS(session.get("https://www.xe.com/currencyconverter/convert/?Amount=1&From=THB&To=USD",
          headers=my_headers).content, "lxml")
	
	# Scraping the text from the selected element (CSS selector)
	# findall() and select() methods return a list, indicate index [0] to extract the first element as a string value
	# Extracting only the number from the text string and converting it to a float value (decimal number)
  exchange_rate = float(re.findall(
	    r"[-+]?(?:\d*\.\d+|\d+)", XE.select("p.result__BigRate-sc-1bsijpp-1.iGrAod")[0].text)[0])
  
  print(f"\nParse FX time: {round((time() - start), 6)} seconds")
  print(f"1 THB = {exchange_rate} USD on {local_datetime.strftime('%A, %-d %B %Y')}\n")
	
	
  # --------------------------------------- #
  # List of URLS of Webpages to be Scraped  #
  # --------------------------------------- #

  start_url = "https://www.mcdonalds.co.th/mcDelivery/nonMember/category/promotion&lang=en"

  first_page = BS(session.get(url=start_url, headers=my_headers).content, "lxml")

  # `select()` method returns a list of all elements with the specified CSS selector
  # Scraping anchor elements in the nav bar list using Dictionary Comprehension:
  # {(category name in inner text: URL of the category page) for category in nav bar list}
  categories = {
    a.get_text().strip(): a["href"]
    for a in (first_page.select("a.category-item"))
  }

	
	# -------------------------------------- #
	# Parsing the data into Dictionary List  #
	# -------------------------------------- #
	
	# Initialising the list object [] to hold dictionaries {}
  product_list = []


  # Outer For Loop gets sends a request to each category page to get the html soup
  for category_name, category_url in categories.items():
    category_page = BS(session.get(url=category_url, headers=my_headers).content, "lxml")
    
    # Middle For Loop iterates through each product in the category page
    for products in category_page.select("div.food-container > div.grid"):
        
      for i, price in enumerate(products.select("div.selling-price"), start=0):
        label = products.select("div.price div.grid-label")[i].text
        product = {}
        product["Date"] = local_datetime.strftime("%Y/%m/%d")
        product["Day"] = local_datetime.strftime("%a")
        product["Territory"] = "Thailand"
        # If condition for variations between single ("Price") and double price tags ("A-la-carte" and "Set")
        if (label.lower() == "price"):
          product["Menu Item"] = products.select("div.name")[0].text
        else:
          product["Menu Item"] = f'{products.select("div.name")[0].text} {label}'
        thb = float("".join(re.findall(r"\d+", price.text)))
        product["Price (THB)"] = f"{thb:.2f}"
        product["Price (USD)"] = f"{(thb * exchange_rate):.2f}"
        product["Category"] = category_name
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
	
  print(f"Scrape time: {round((time() - start), 6)} seconds\n")
  print(product_list_df)

  timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

  output_file = str(timestamp + " mcd-bs4-th.csv")
  output_dir = Path("./scraped-data")

  # Create directory as required; won't raise an error if directory already exists
  output_dir.mkdir(parents=True, exist_ok=True)

  product_list_df.to_csv((output_dir / output_file),
                          float_format="%.2f", encoding="utf-8")
  
  print(f"\nWrite CSV time: {round((time() - start), 6)} seconds\n")
  print(f'\n\nExported to file:\nhttps://github.com/schmwong/APAC-McDelivery-Menu-Logger/tree/main/mcd-bs4-th/scraped-data/{output_file.replace(" ", "%20")}\n\n ============ \n\n\n\n\n\n')

  # Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-bs4-th.csv"


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
