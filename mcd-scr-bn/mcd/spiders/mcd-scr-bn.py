''' ====================================================== ''''''
| Menu data retrieved via GET requests to GoMamam API endpoints |
'''''' ====================================================== '''

# pip3 install scrapy
# pip3 install pandas
# pip3 install pytz
# pip3 install path
# pip3 install pathlib2
# scrapy crawl mcd-scr-au


import scrapy  # version ^2.6.1 at time of writing
import json
import pandas as pd
import datetime as dt
import pytz
from pathlib import Path
import traceback


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Asia/Brunei"))

product_list_consolidated = []



class McdScrBnSpider(scrapy.Spider):
	
	name = "mcd-scr-bn"


	''' ====================================================== ''''''
	Step 1: Send GET request to fetch HTML webpage from Xe.com
	'''''' ------------------------------------------------------ '''

	def start_requests(self):

		try:
			url = "https://www.xe.com/currencyconverter/convert/?Amount=1&From=BND&To=USD"
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
		variable, then send GET requests to  GoMamam API to
		retrieve product information of all menu items
	'''''' ------------------------------------------------------ '''

	def parse_fx(self, response):

		# exchange rate is stored in two parts, across two HTML elements
		# parsing the CSS selectors return string values, which are concatenated,
		# and the resulting string is stored as a float (decimal) value, to be used in later mathematical operations
		exchange_rate = float(
			response.css("p.result__BigRate-sc-1bsijpp-1.iGrAod::text").get() +
			response.css("span.faded-digits::text").get()
		)


		urls =[
			# Lambak Outlet
			"https://apiv4.ordering.co/v400/en/gomamam/business/mcdonalds?location=4.965233800000001,114.9514923&type=1",
			
			# Jerudong Outlet
			"https://apiv4.ordering.co/v400/en/gomamam/business/mcdonaldsjerudong?location=4.9380373,114.8339538&type=1",
			
			# Gadong Outlet
			"https://apiv4.ordering.co/v400/en/gomamam/business/mcdonaldsgadong?location=4.906765099999999,114.9163599&type=1"
		]

		headers = {
			'authority': 'apiv4.ordering.co',
			'accept': 'application/json, text/plain, */*',
			'accept-language': 'en-GB,en;q=0.9',
			'dnt': '1',
			'origin': 'https://www.gomamam.com',
			'referer': 'https://www.gomamam.com/',
			'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
			'sec-ch-ua-mobile': '?0',
			'sec-ch-ua-platform': '"macOS"',
			'sec-fetch-dest': 'empty',
			'sec-fetch-mode': 'cors',
			'sec-fetch-site': 'cross-site',
			'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36',
			'x-app-x': 'WEBSITE',
			'x-front-version-x': '4.31.2.3',
		}

		store_paths = {
			"Lambak Outlet": "/mcdonalds",
			"Jerudong Outlet": "/mcdonaldsjerudong",
			"Gadong Outlet": "/mcdonaldsgadong"
		}

		for (url, store_name, store_path) in zip(urls, store_paths.keys(), store_paths.values()):
			try:
				yield scrapy.Request(
					url, headers=headers, method="GET", callback=self.parse_products,
					meta=dict(
						fx=exchange_rate,
						store=store_name,
						slug=store_path
					)
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

		exchange_rate = response.meta["fx"]
		order_page = f"https://www.gomamam.com{response.meta['slug']}"

		try:
			parsed_json = json.loads(response.body)["result"]
			outlet = parsed_json["name"]
			address = parsed_json["address_notes"]
			tel = int(parsed_json["phone"])
			email = parsed_json["email"]

		except:
			print(f"\n\n---------\n{response.meta['store']} is currently offline.")
			print(order_page, "\n\n\n")
			print(f"{traceback.format_exc()}\n---------\n")

		else:
			product_list = []
			menu = parsed_json["categories"]

			for category in menu:
				# ---------------------
				category_name = category["name"].strip()
				# |
				for food in category["products"]:
					# ------------------
					if food["price"] != 0 and food["name"] != "Sauces":
						# ---------------
						product = {}
						product["id"] = food["id"]
						product["Menu Item"] = " ".join(
							(food["name"].replace("sauce", "Sauce").replace("\r", "")).replace(" (UNAVAILABLE)", "").split()
						)
						product["Price (BND)"] = "%.2f" % food["price"]
						product["Price (USD)"] = round((float(product["Price (BND)"]) * exchange_rate), 2)
						product["Category"] = category_name
						product_list.append(product)
						# ---------------
					# |
					else:
						# ---------------
						options = food["extras"][0]["options"]
						# |
						for option in options:
							# ------------
							if option["name"] == "Option" or option["name"] == "Size":
								# ---------
								suboptions = option["suboptions"]
								# |
								for suboption in suboptions:
									# ------
									if suboption["price"] != 0:
										# ---
										product = {}
										product["id"] = food["id"]
										product["Menu Item"] = " ".join(
											(f'{food["name"]} — {suboption["name"]}').replace(" (UNAVAILABLE)", "").split()
										)
										product["Price (BND)"] = "%.2f" % suboption["price"]
										product["Price (USD)"] = round((float(product["Price (BND)"]) * exchange_rate), 2)
										product["Category"] = category_name
										product_list.append(product)
										# ---
									# |
									elif food["name"] == "Sauces":
										# ---
										product = {}
										product["id"] = food["id"]
										product["Menu Item"] = " ".join(
											(f'{food["name"]} — {suboption["name"]}').replace(" (UNAVAILABLE)", "").split()
										)
										product["Price (BND)"] = "%.2f" % food["price"]
										product["Price (USD)"] = round((float(product["Price (BND)"]) * exchange_rate), 2)
										product["Category"] = category_name
										product_list.append(product)
										# ---
									# ------
								# ---------
							# ------------
						# ---------------
					# ------------------
				# ---------------------


			product_list_df = pd.DataFrame(product_list)

			print("\n\n----+----")
			print("McDo Outlet: " + outlet)
			print("Address: " + address)
			print(f"Tel: {tel}  |  Email: {email}")
			print()
			print("Order Page: " + order_page)
			print()
			print(product_list_df)
			print("----+----\n\n")

			product_list_consolidated.extend(product_list)

			product_list_consolidated_df = pd.DataFrame(product_list_consolidated)


			# ------
			# These operations have to be completed explicitly,
			# i.e. df = df.<method()>
			# ---
			duplicates = product_list_consolidated_df[
				product_list_consolidated_df.duplicated(
					subset=["Menu Item", "Price (BND)", "Category"]
				)
			]
			if duplicates.empty == False:
				count = len(duplicates)
				print(f"\n\n\nDuplicates:\n{duplicates}\n\n")
				print(f"\nDropping {count} duplicates (keeping first occurrences)\n\n")
				
			product_list_consolidated_df.drop_duplicates(
				subset=["Menu Item", "Price (BND)", "Category"],
				keep="first", inplace=True, ignore_index=True
			)
			# ---

			# ---
			category_sort = {
				"Regular Value Meal": 1,
				"Happy Meal": 2,
				"Sides": 3,
				"Dessert": 4
			}
			product_list_df = product_list_df.sort_values(
				by=["Category", "id"], key=lambda x: x.map(category_sort),
				ascending=True, na_position="last"
			)
			# ---

			# Comment out this line when debugging
			product_list_df = product_list_df.drop(columns=["id"], axis=1)
			# ------

			product_list_df.index = pd.RangeIndex(
				start=1, stop=(len(product_list_df.index) + 1), step=1
			)

			
			# successively insert 3 new columns from the left
			product_list_df.insert(
				loc=0,
				column="Territory",
				value="Brunei",
			)
			product_list_df.insert(0, "Day", local_datetime.strftime("%a"))
			product_list_df.insert(0, "Date", local_datetime.strftime("%Y/%m/%d"))


			print("\n\n\n ============ \n\n")
			print(
				f"""1 BND = {exchange_rate} USD (1 USD = {1/exchange_rate} BND)
				on {local_datetime.strftime('%A, %-d %B %Y')}"""
			)
			print("\n\n\n", product_list_consolidated_df, "\n\n ============ \n\n\n")
			# print("\n\n\n", product_list_consolidated_df.to_string(), "\n\n ============ \n\n\n")


			timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))
			
			output_file = str(timestamp + " mcd-scr-bn.csv")
			output_dir = Path("./scraped-data")
			
			# Create directory as required; won't raise an error if directory already exists
			output_dir.mkdir(parents=True, exist_ok=True)
			
			product_list_df.to_csv((output_dir / output_file),
								   float_format="%.2f", encoding="utf-8")
			
			# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-scr-bn.csv"