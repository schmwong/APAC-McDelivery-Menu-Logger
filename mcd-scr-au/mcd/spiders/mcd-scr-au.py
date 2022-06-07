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
local_datetime = dt.datetime.now(pytz.timezone("Australia/Melbourne"))


class McdScrAuSpider(scrapy.Spider):
	name = 'mcd-scr-au'
	
	''' ====================================================== ''''''
	Step 1: Send GET request to fetch HTML webpage from Xe.com
	'''''' ------------------------------------------------------ '''

	def start_requests(self):

		url = "https://www.xe.com/currencyconverter/convert/?Amount=1&From=AUD&To=USD"

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

		
		url = "https://www.ubereats.com/api/getStoreV1?localeCode=au"

		headers = {
			'authority': 'www.ubereats.com',
			'accept': 'application/json, text/plain, */*',
			'accept-language': 'en-GB,en;q=0.9',
			'content-type': 'application/json',
			'dnt': '1',
			'origin': 'https://www.ubereats.com',
			'referer': 'https://www.ubereats.com/au/store/mcdonalds-clifton-hill/SIaq6LrDTFemKVajhXM-iA',
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
			# McDonald's Clifton Hill
			'storeUuid': '4886aae8-bac3-4c57-a629-56a385733e88',
			'sfNuggetCount': 7,
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

		outlet = parsed_json["location"]["address"]
		order_page = headers["referer"]


		section_dict = {}
		menu_sections = parsed_json["sections"]

		for menu_section in menu_sections:
			menu_id = menu_section.get("uuid")
			menu_name = menu_section.get("title")
			section_dict[menu_id] = menu_name

		print()
		print(section_dict)
		# >> {'205c1306-d434-585e-89ff-0288e557c80a': 'Breakfast Menu',
		# 'd4d2836a-fe97-583b-a7c7-f4e6584c99a9': 'Regular Menu',
		# '29ffdae4-d4ac-523a-bd56-49f924c07773': 'Overnight Menu'}
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
					# stored in AUD cent denominations as integer values on the API resource
					product["Price (AUD)"] = round(float(food["price"] / 100), 2)
					product["Price (USD)"] = round(
						(float(product["Price (AUD)"]) * exchange_rate), 2
					)
					product["Category"] = category_section["payload"]["standardItemsPayload"]["title"]["text"]
					product["Menu"] = menu_name
					product_list.append(product)

		
		product_list_df = pd.DataFrame(product_list)

		# successively insert 3 new columns from the left
		product_list_df.insert(
				loc=0,
				column="Territory",
				value="Australia",
		)
		product_list_df.insert(0, "Day", local_datetime.strftime("%a"))
		product_list_df.insert(0, "Date", local_datetime.strftime("%Y/%m/%d"))

		product_list_df.index = pd.RangeIndex(
      start=1, stop=(len(product_list_df.index) + 1), step=1
    )


		print()
		print("Maccas Outlet: " + outlet)
		print()
		print("Order Page: " + order_page)
		print()
		# >>
		# >> Maccas Outlet: Mcdonald'S® (Clifton Hill), 3068, VIC 3068
		# >>
		# >> Order Page: https://www.ubereats.com/au/store/mcdonalds-clifton-hill/SIaq6LrDTFemKVajhXM-iA
		# >>
		print()
		print(
      f"1 AUD = {exchange_rate} USD (1 USD = {1/exchange_rate} AUD) on {local_datetime.strftime('%A, %-d %B %Y')}"
    )
		print()
		# >>
		# >> 1 AUD = 0.72251604 USD (1 USD = 1.3840523180634163 AUD) on Tuesday, 7 June 2022
		# >>

		
		print()
		print(product_list_df)
		# print(product_list_df.to_string())
		print()


		timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

		output_file = str(timestamp + " mcd-scr-au.csv")
		output_dir = Path("./scraped-data")

		# Create directory as required; won't raise an error if directory already exists
		# output_dir.mkdir(parents=True, exist_ok=True)

		product_list_df.to_csv((output_dir / output_file),
													 float_format="%.2f", encoding="utf-8")

		# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-scr-au.csv"
