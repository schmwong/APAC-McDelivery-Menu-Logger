''' ====================================================== ''''''
| Menu data retrieved via POST request to UberEats API endpoint |
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


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Pacific/Auckland"))


class McdScrAuSpider(scrapy.Spider):
	name = 'mcd-scr-nz'
	
	''' ====================================================== ''''''
	Step 1: Send GET request to fetch HTML webpage from Xe.com
	'''''' ------------------------------------------------------ '''

	def start_requests(self):

		url = "https://www.xe.com/currencyconverter/convert/?Amount=1&From=NZD&To=USD"

		yield scrapy.Request(url, method="GET", callback=self.parse_fx)


	''' ====================================================== ''''''
	Step 2: Parse exchange rate and store float value into global
		variable, then send POST request to the Uber Eats API
		to retrieve menu data as JSON
	'''''' ------------------------------------------------------ '''

	def parse_fx(self, response):

	# exchange rate is stored in two parts, across two HTML elements
	# parsing the CSS selectors return string values, which are concatenated,
	# and the resulting string is stored as a float (decimal) value, 
	# to be used in later mathematical operations
		exchange_rate = float(
			response.css("p.result__BigRate-sc-1bsijpp-1.iGrAod::text").get() +
			response.css("span.faded-digits::text").get()
		)

		
		url = "https://www.ubereats.com/api/getStoreV1?localeCode=nz"

		headers = {
			'authority': 'www.ubereats.com',
			'accept': 'application/json, text/plain, */*',
			'accept-language': 'en-GB,en;q=0.9',
			'content-type': 'application/json',
			'dnt': '1',
			'origin': 'https://www.ubereats.com',
			'referer': 'https://www.ubereats.com/nz/store/mcdonalds-point-chevalier/1h7CdIIqR-GG5jVOuHqoFA',
			# 'referer': 'https://www.ubereats.com/nz/store/mcdonalds-frankton/mNH7d7B5Sq-uVm3qkSmthw',
			'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
			'sec-ch-ua-mobile': '?0',
			'sec-ch-ua-platform': '"macOS"',
			'sec-fetch-dest': 'empty',
			'sec-fetch-mode': 'cors',
			'sec-fetch-site': 'same-origin',
			'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36',
			'x-csrf-token': 'x',
    }

		body = json.dumps({
			# McDonald's Point Chevalier, Auckland
			'storeUuid': 'd61ec274-822a-47e1-86e6-354eb87aa814',
			'sfNuggetCount': 24,
			# McDonald's Frankton, Hamilton
			# 'storeUuid': '98d1fb77-b079-4aaf-ae56-6dea9129ad87',
			# 'sfNuggetCount': 25,
		})

		yield scrapy.Request(
			url, headers=headers, body=body, method="POST",
			callback=self.parse_products,
			meta={"req_h": headers, "fx": exchange_rate}
		)


	''' ====================================================== ''''''
	Step 3: Parse and store product data into a DataFrame,
		then clean, sort, and export
	'''''' ------------------------------------------------------ '''

	def parse_products(self, response):
		parsed_json = json.loads(response.body)["data"]
		headers = response.meta["req_h"]
		exchange_rate = response.meta["fx"]

		outlet = parsed_json["title"]
		address = parsed_json["location"]["address"]
		order_page = headers["referer"]


		section_dict = {}
		menu_sections = parsed_json["sections"]

		for menu_section in menu_sections:
			menu_id = menu_section.get("uuid")
			menu_name = menu_section.get("title")
			section_dict[menu_id] = menu_name

		print()
		print(section_dict)
		# >> {'bbe591d5-b476-52c3-b85b-c5e937036f09': 'Breakfast',
		# 'a99d1503-9c56-580d-9214-cc19d0ed6745': 'Lunch & Dinner',
		# '09cbad6d-162a-5223-80b9-01324c55704a': 'Overnight'}
		print()

		
		product_list = []
		menu = parsed_json["catalogSectionsMap"]

		# Outer for loop iterates through each of the three menu sections
		for menu_section in menu:
			menu_name = section_dict.get(menu_section)

			# First nested for loop iterates through each Category
			for category_section in menu[menu_section]:
				products = category_section["payload"]["standardItemsPayload"]["catalogItems"]

				# Inner nested for loop iterates through each food product
				for food in products:
					product = {}
					product["Menu Item"] = food["title"]
					# stored in NZD cent denominations as integer values on the API resource
					product["Price (NZD)"] = round(float(food["price"] / 100), 2)
					product["Price (USD)"] = round(
						(float(product["Price (NZD)"]) * exchange_rate), 2
					)
					product["Category"] = category_section["payload"]["standardItemsPayload"]["title"]["text"]
					product["Menu"] = menu_name
					product_list.append(product)

		
		product_list_df = pd.DataFrame(product_list)

		# successively insert 3 new columns from the left
		product_list_df.insert(
				loc=0,
				column="Territory",
				value="New Zealand",
		)
		product_list_df.insert(0, "Day", local_datetime.strftime("%a"))
		product_list_df.insert(0, "Date", local_datetime.strftime("%Y/%m/%d"))

		product_list_df = product_list_df.sort_values(
			by=["Menu", "Category"], key=lambda x: x.map({"Breakfast": 1, "Lunch & Dinner": 2, "Overnight": 3}), na_position="last"
		)

		product_list_df.index = pd.RangeIndex(
			start=1, stop=(len(product_list_df.index) + 1), step=1
		)


		print()
		print("Maccas Outlet: " + outlet)
		print("Address: " + address)
		print()
		print("Order Page: " + order_page)
		print()
		# >>
		# >> Maccas Outlet: McDonald's® (Point Chevalier)
		# >> Address: 1159 Great North Rd, Point Chevalier, Auckland 1022
		# >>
		# >> Order Page: https://www.ubereats.com/nz/store/mcdonalds-point-chevalier/1h7CdIIqR-GG5jVOuHqoFA
		# >>
		
		print()
		print(
			f"1 NZD = {exchange_rate} USD (1 USD = {1/exchange_rate} NZD) on {local_datetime.strftime('%A, %-d %B %Y')}"
		)
		print()
		# >>
		# >> 1 NZD = 0.64759651 USD (1 USD = 1.5441713853584542 NZD) on Tuesday, 7 June 2022
		# >>

		
		print()
		print(product_list_df)
		# print(product_list_df.to_string())
		print()


		timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

		output_file = str(timestamp + " mcd-scr-nz.csv")
		output_dir = Path("./scraped-data")

		# Create directory as required; won't raise an error if directory already exists
		output_dir.mkdir(parents=True, exist_ok=True)

		product_list_df.to_csv((output_dir / output_file),
			float_format="%.2f", encoding="utf-8")

		# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-scr-nz.csv"
