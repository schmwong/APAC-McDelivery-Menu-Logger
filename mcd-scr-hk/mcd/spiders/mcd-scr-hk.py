''' ====================================================== ''''''
| Menu data retrieved via GET request to Foodpanda API endpoint |
'''''' ====================================================== '''

# pip3 install scrapy
# pip3 install pandas
# pip3 install pytz
# pip3 install path
# pip3 install pathlib2

# cd /Users/user/Desktop/DKit1\ -\ Paul/scrapy-env
# source bin/activate
# cd mcd
# scrapy crawl hk


import scrapy  # version ^2.6.1 at time of writing
import json
import pandas as pd
import datetime as dt
import pytz
from pathlib import Path
import traceback


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Asia/Hong_Kong"))



class McdScrHkSpider(scrapy.Spider):

	name = "mcd-scr-hk"


	''' ====================================================== ''''''
    Step 1: Send GET request to fetch HTML webpage from Xe.com
    '''''' ------------------------------------------------------ '''

	def start_requests(self):
		
		try:
			url = "https://www.xe.com/currencyconverter/convert/?Amount=1&From=HKD&To=USD"
			yield scrapy.Request(url, method="GET", callback=self.parse_fx)
			
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


	''' ====================================================== ''''''
	Step 2: Parse exchange rate and store float value into global
		variable, then send GET request to the Foodpanda API
		to retrieve menu data as JSON
	'''''' ------------------------------------------------------ '''

	def parse_fx(self, response):

		# exchange rate is stored in two parts, across two HTML elements
		# parsing the CSS selectors return string values, which are concatenated,
		# and the resulting string is stored as a float (decimal) value, to be used in later mathematical operations
		exchange_rate = float(
			response.css("p.result__BigRate-sc-1bsijpp-1.iGrAod::text").get() +
			response.css("span.faded-digits::text").get()
		)


		url = "https://hk.fd-api.com/api/v5/vendors/q8hc?include=menus,bundles,multiple_discounts&language_id=1&dynamic_pricing=0&opening_type=delivery&basket_currency=HKD"

		headers = {
			':authority': 'hk.fd-api.com',
			'accept': '''application/json,application/xhtml+xml,application/xml;q=0.9,
			image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9''',
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
			'user-agent': '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.
			36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36''',
		}

		try:
			yield scrapy.Request(
				url, headers=headers, method="GET", callback=self.parse_products,
				meta={"fx": exchange_rate}
			)

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


	''' ====================================================== ''''''
	Step 3: Parse and store product data into a DataFrame,
		then clean, sort, and export
	'''''' ------------------------------------------------------ '''

	def parse_products(self, response):

		parsed_json = json.loads(response.body)["data"]
		exchange_rate = response.meta["fx"]

		try:
			outlet = parsed_json["name"]
			address = parsed_json["address"]
			order_page = parsed_json["web_path"]
			
		except:
			print(f"\n\n---------\nMcDonald's & McCafé (Admiralty Centre) is currently offline.")
			print("https://www.foodpanda.hk/restaurant/q8hc/mcdonalds-and-mccafe-admiralty-centre\n\n\n")
			print(f"{traceback.format_exc()}\n---------\n")

		else:
			product_list = []
			submenus = parsed_json["menus"][0]["menu_categories"]

			for submenu in submenus:
				# ------------
				products = submenu["products"]
				# |
				for food in products:
					# ---------
					product = {}
					product["Menu Item"] = food["name"]
					product["Price (HKD)"] = "%.2f" % float(food["product_variations"][0]["price"])
					product["Price (USD)"] = round((float(product["Price (HKD)"]) * exchange_rate), 2)
					product["Category"] = submenu["name"]
					product["Menu"] = parsed_json["menus"][0]["name"]
					product_list.append(product)
					# ---------
				# ------------


			product_list_df = pd.DataFrame(product_list)

			
			print("\n\n----+----")
			print("McDo Outlet: " + outlet)
			print("Address: " + address)
			print()
			print("Order Page: " + order_page)
			print("----+----\n\n")


			# ------
			# These operations have to be completed explicitly,
			# i.e. df = df.<method()>
			# ---
			duplicates = product_list_df[
				product_list_df.duplicated()
			]
			if duplicates.empty == False:
				count = len(duplicates)
				print(f"\n\n\nDuplicates:\n{duplicates}\n\n")
				print(f"\nDropping {count} duplicates (keeping first occurrences)\n\n")
				
			product_list_df.drop_duplicates(
				keep="first", inplace=True, ignore_index=True
			)
			# ---
			# |
			# ---
			# product_list_df = product_list_df.sort_values(
			# 	by=["Category"],
			# 	ascending=True, na_position="last"
			# )
			# ---
			# ------


			# ------
			# successively insert 3 new columns from the left
			product_list_df.insert(
				loc=0,
				column="Territory",
				value="Hong Kong",
			)
			product_list_df.insert(0, "Day", local_datetime.strftime("%a"))
			product_list_df.insert(0, "Date", local_datetime.strftime("%Y/%m/%d"))
			# ------


			product_list_df.index = pd.RangeIndex(
				start=1, stop=(len(product_list_df.index) + 1), step=1
			)


			print("\n\n\n ============ \n\n")
			print(
				f"""1 HKD = {exchange_rate} USD (1 USD = {1/exchange_rate} HKD)
				on {local_datetime.strftime('%A, %-d %B %Y')}"""
			)
			print("\n\n\n", product_list_df)
			# print("\n\n\n", product_list_df.to_string())


			timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))
			
			output_file = str(timestamp + " mcd-scr-hk.csv")
			output_dir = Path("./scraped-data")
			
			# Create directory as required; won't raise an error if directory already exists
			output_dir.mkdir(parents=True, exist_ok=True)
			
			product_list_df.to_csv((output_dir / output_file),
								   float_format="%.2f", encoding="utf-8")

			print(f'''\n\nExported to file:
				  https://github.com/schmwong/APAC-McDelivery-Menu-Logger/tree/main/mcd-scr-hk/scraped-data/{output_file.replace(" ", "%20")}\n\n ============ \n\n\n\n\n\n''')
			
			# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-scr-hk.csv"