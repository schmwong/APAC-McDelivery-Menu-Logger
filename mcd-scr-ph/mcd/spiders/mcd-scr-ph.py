''' ====================================================== ''''''
| Menu data retrieved via sequential requests to API endpoints |>
'''''' ====================================================== '''

# pip3 install scrapy
# pip3 install pandas
# pip3 install pytz
# pip3 install path
# pip3 install pathlib2
# scrapy crawl mcd-scr-ph


import scrapy  # version ^2.6.1 at time of writing
import json
import pandas as pd
import datetime as dt
import pytz
from pathlib import Path  # install pathlib2 instead of pathlib
import traceback


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Asia/Manila"))


# Initialise category_dict with previously known values
# found at /customerNewGetProductCategoryListHomeSwimLane at various times of the day
category_dict = {
	11: "McDo Party Box",
	76: "BREAKFAST HOURS",
	77: "LUNCH HOURS",
	78: "PM SNACK HOURS",
	79: "DINNER HOURS",
	80: "AFTER DINNER HOURS",
}


class McdScrPhSpider(scrapy.Spider):
	name = 'mcd-scr-ph'

	# This is a built-in Scrapy function that runs first where we'll override the default headers
  # Documentation: https://doc.scrapy.org/en/latest/topics/spiders.html#scrapy.spiders.Spider.start_requests	

	
	''' ====================================================== ''''''
	Step 1: Send GET request to fetch HTML webpage from Xe.com
	'''''' ------------------------------------------------------ '''

	def start_requests(self):
		
		try:
			url = "https://www.xe.com/currencyconverter/convert/?Amount=1&From=PHP&To=USD"
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
		variable, then send POST request to retrieve GID and 
		Bearer auth token to enable access to CMS endpoints 
		of the haku API
	'''''' ------------------------------------------------------ '''

	def parse_fx(self, response):

		try:
			# exchange rate is stored in two parts, across two HTML elements
			# parsing the CSS selectors return string values, which are concatenated, and 
			# the resulting string is stored as a float (decimal) value, to be used in later mathematical operations
			exchange_rate = float(
				response.css("p.result__BigRate-sc-1bsijpp-1.iGrAod::text").get() +
				response.css("span.faded-digits::text").get()
			)
	
	
			url = "https://haku-prod-api-service.mcdelivery.com.ph/api/v2/auth/authenticate-user"
	
			# Set the headers here. The important part is "application/json"
			headers = {
				":authority": "haku-prod-api-service.mcdelivery.com.ph",
				"accept": "application/json, text/plain, */*",
				"accept-language": "en-GB,en;q=0.9",
				"access-control-allow-origin": "*",
				"content-type": "application/json",
				"dnt": 1,
				"origin": "https://mcdelivery.com.ph",
				"referer": "https://mcdelivery.com.ph/",
				"sec-ch-ua": "' Not A;Brand';v='99', 'Chromium';v='102', 'Google Chrome';v='102'",
				"sec-ch-ua-mobile": "?0",
				"sec-ch-ua-platform": "'macOS'",
				"sec-fetch-dest": "empty",
				"sec-fetch-mode": "cors",
				"sec-fetch-site": "same-site",
				"user-agent": """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.
				36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36""",
			}
	
			body = json.dumps({"user_id": ""})
	
			yield scrapy.Request(
				url, headers=headers, body=body, method="POST",
				callback=self.parse_auth, meta={"fx": exchange_rate}
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
	Step 3: Store the right HTTP request headers and body, then send
		POST requests to retrieve Category IDs and names
	'''''' ------------------------------------------------------ '''

	def parse_auth(self, response):

		try:
			parsed_json = json.loads(response.body)
			access_token = parsed_json.get("access_token")
			gid = parsed_json.get("gid")
			
			print()
			print("access_token: " + access_token)
			print()
			print("gid: " + gid)
			print()
			
			exchange_rate = response.meta["fx"]
	
			urls = [
				"https://haku-prod-cms-service.mcdelivery.com.ph/api/v2/customerNewGetProductCategoryList",
				"https://haku-prod-cms-service.mcdelivery.com.ph/api/v2/customerNewGetProductCategoryListHomeSwimLane"
	    ]
	
			auth_headers = {
				':authority': 'haku-prod-cms-service.mcdelivery.com.ph',
				'accept': 'application/json, text/plain, */*',
				'accept-language': 'en-GB,en;q=0.9',
				'access-control-allow-origin': '*',
				'authorization': f'Bearer {access_token}',
				'content-type': 'application/json',
				'dnt': '1',
				'origin': 'https://mcdelivery.com.ph',
				'referer': 'https://mcdelivery.com.ph/',
				'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
				'sec-ch-ua-mobile': '?0',
				'sec-ch-ua-platform': '"macOS"',
				'sec-fetch-dest': 'empty',
				'sec-fetch-mode': 'cors',
				'sec-fetch-site': 'same-site',
				'user-agent': '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.
				36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36''',
				'x-gid': f'{gid}',
				'x-plat': 'web',
				'x-user-id': '',
			}
	
			body = json.dumps({
				"app_type": "web",
				# CAPITAL TOWN, (Capitol Blvd, Sto Nino  San Fernando Pampanga 2000, San Fernando City)
				# store_id only affects /customerNewGetProductList2 endpoint
				# /customerNewGetProductListDefault takes any value (default is 0)
				"store_id": 1159,
				"user_id": ""
				})
	
			for url in urls:
				yield scrapy.Request(
					url, headers=auth_headers, body=body, method="POST",
					callback=self.parse_categories,
					meta={"headers": auth_headers,
					"body": body, "fx": exchange_rate}
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
	Step 4: Store the Category data into a global dictionary for
		later reference, then send a POST request to retrieve
		product information of all menu items
	'''''' ------------------------------------------------------ '''

	def parse_categories(self, response):

		try:
			category_data = json.loads(response.body).get("data")
	
			for category_datum in category_data:
				category_id = category_datum.get("id")
				category_name = category_datum.get("name")
				category_dict[category_id] = category_name
			
			print()
			print(category_dict)
			print()
	
			exchange_rate = response.meta["fx"]
	
			url_default = "https://haku-prod-cms-service.mcdelivery.com.ph/api/v2/customerNewGetProductListDefault"
			url_default2 = "https://haku-prod-cms-service.mcdelivery.com.ph/api/v2/customerNewGetProductList"
			url_specific = "https://haku-prod-cms-service.mcdelivery.com.ph/api/v2/customerNewGetProductList2"
	
			auth_headers = response.meta["headers"]
			body = response.meta["body"]
			
			yield scrapy.Request(
				url=url_default2, headers=auth_headers, body=body, method="POST",
				callback=self.parse_products,
				meta={"categories": category_dict, "fx": exchange_rate, "url_specific": url_specific, "headers": auth_headers, "body": body}
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
	Step 5: Parse and store product data into a DataFrame, 
		then clean, sort, and export
	'''''' ------------------------------------------------------ '''

	def parse_products(self, response):

		try:
			# Print response status code and message (for debugging)
			status = json.loads(response.body).get("status")
			message = json.loads(response.body).get("message")
			print(
				f"""
				Status: {status}
				Message: {message}
				"""
			)
			# Prepare the required dicts for parsing
			category_dict = response.meta["categories"]
			data = json.loads(response.body).get("data")
			product_list = []
			exchange_rate = response.meta["fx"]
	
			def populate():
				product = {}
				product["sequence_no"] = datum.get("sequence_no")
				product["id"] = datum.get("id")  # for debugging
				product["Menu Item"] = datum.get("name")
				if datum.get("price") is not None:
					# decimal places not formatted correctly with round(), converted 
					# to string to display correctly
					product["Price (PHP)"] = '%.2f' % float(datum.get("price"))
					product["Price (USD)"] = round(
						(float(product["Price (PHP)"]) * exchange_rate), 2
					)
				if len(instances) > 0:
						product["Category"] = category_dict.get(instance.get("category_id"))
						product["category_id"] = instance.get("category_id")  # for debugging
				else:
						product["Category"] = "Add-ons"
						product["category_id"] = "None"
				product["Menu"] = datum.get("food_schedule").get("schedule_name")
				# ignore entries with empty values in menu item and price fields
				if product["Menu Item"] is not None and product["Price (PHP)"] is not None:
						product_list.append(product)
				# print()
				# print(product)
				# print(instance)
	
			for datum in data:
			# for each menu item, gets list of dictionaries containing Category IDs
				instances = datum.get("food_category")
				# iterate by each category id if list is not empty
				# new entry each time the same menu item appears in a different category
				if len(instances) > 0:
					for instance in instances:
						populate()
				else:
						populate()
	
			print()
	
			# pd.set_option('display.max_columns', None)
			product_list_df = pd.DataFrame(product_list)
	
			# successively insert 3 new columns from the left
			product_list_df.insert(
				loc=0,
				column="Territory",
				value="Philippines",
			)
			product_list_df.insert(0, "Day", local_datetime.strftime("%a"))
			product_list_df.insert(0, "Date", local_datetime.strftime("%Y/%m/%d"))
	
			product_list_df.drop_duplicates(subset=None, keep='last', inplace=True, ignore_index=True)
	
			# sort order according to menu webpage at: https://mcdelivery.com.ph/menu/
			# except that McDelivery Exclusives are placed above all else
			category_sort = {
				"McDelivery Exclusives": -1,
				"Featured": 0,
				"Group Meals": 1,
				"Breakfast": 2,
				"Chicken": 3,
				"Burgers": 4,
				"McSpaghetti": 5,
				"Rice Bowls": 6,
				"Desserts & Drinks": 7,
				"McCafé": 8,
				"Fries & Extras": 9,
				"Happy Meal": 10,
				"McDo Party Box": 11,
				"BREAKFAST HOURS": 12,
				"LUNCH HOURS": 13,
				"PM SNACK HOURS": 14,
				"DINNER HOURS": 15,
				"AFTER DINNER HOURS": 16
			}
			
			# ------------ #
			# These operations have to be completed explicitly,
			# i.e. df = df.sort_values
			
			product_list_df = product_list_df.sort_values(
				# by=["category_id", "sequence_no"], ascending=True, na_position="last"
				by=["category_id", "Category", "sequence_no"], key=lambda x: x.map(category_sort), ascending=True, na_position="last"
			)
			
			# comment this line out when debugging
			product_list_df = product_list_df.drop(columns=["sequence_no", "id", "category_id"])
			# product_list_df = product_list_df.style.hide_columns(
			# 	["sequence_no", "id", "category_id"]
			# )
			
			product_list_df.index = pd.RangeIndex(
				start=1, stop=(len(product_list_df.index) + 1), step=1
			)
			# ------------ #
	
	
			print()
			print(
				f"""1 PHP = {exchange_rate} USD (1 USD = {1/exchange_rate} PHP) 
				on {local_datetime.strftime('%A, %-d %B %Y')}"""
			)
			# >> 1 PHP = 0.01891065 USD (1 USD = 52.880255305872616 PHP) on Saturday, 4 June 2022
			print()
			print()
			# print(product_list_df.to_string())
			print(product_list_df)
			print()
	
			timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))
			
			output_file = str(timestamp + " mcd-scr-ph.csv")
			output_dir = Path("./scraped-data")
			
			# Create directory as required; won't raise an error if directory already exists
			output_dir.mkdir(parents=True, exist_ok=True)
			
			product_list_df.to_csv((output_dir / output_file),
			                       float_format="%.2f", encoding="utf-8")
			
			# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-scr-ph.csv"

		
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
			# Using the store specific endpoint if default endpoint does not work
			try:
				def check_meta(key):
					if response.meta[key] is not None:
						return response.meta[key]
					else:
						return None

				url_specific = check_meta("url_specific")
				auth_headers = check_meta("headers")
				body = check_meta("body")

				if (url_specific is not None) and (auth_headers is not None) and (body is not None):
					yield scrapy.Request(
						url=url_specific, headers=auth_headers, body=body, method="POST",
						callback=self.parse_products,
						meta={"categories": category_dict, "fx": exchange_rate}
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
