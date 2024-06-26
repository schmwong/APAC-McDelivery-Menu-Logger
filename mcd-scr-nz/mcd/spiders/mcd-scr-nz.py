''' ====================================================== ''''''
|  Menu data scraped from script element on UberEats order page |
|    (previously via POST request to UberEats API endpoint)     |
'''''' ====================================================== '''

# pip3 install scrapy
# pip3 install pandas
# pip3 install pytz
# pip3 install path
# pip3 install pathlib2
# scrapy crawl mcd-scr-nz


import scrapy  # version ^2.6.1 at time of writing
from playwright.async_api import expect
from scrapy_playwright.page import PageMethod
import json
import pandas as pd
import datetime as dt
import pytz
from pathlib import Path
import traceback
import re
from pprint import pprint

# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Pacific/Auckland"))


class McdScrNzSpider(scrapy.Spider):
    name = 'mcd-scr-nz'
    allowed_domains = [
        'xe.com',
        'ubereats.com'
    ]

    ''' ====================================================== ''''''
    Step 1: Send GET request to fetch HTML webpage from Xe.com
    '''''' ------------------------------------------------------ '''

    def start_requests(self):

        try:
            url = "https://www.xe.com/currencyconverter/convert/?Amount=1&From=NZD&To=USD"
            yield scrapy.Request(url, method="GET", callback=self.parse_fx)

        except Exception:
            print(
                f'''\n\n
                ---
                One or more errors occurred:
                
                {traceback.format_exc()}
                ---
                \n\n
                '''
            )

    ''' ====================================================== ''''''
    Step 2: Parse exchange rate and store float value into global
        variable, then send POST request to the Uber Eats API
        to retrieve menu data as JSON
    '''''' ------------------------------------------------------ '''

    def parse_fx(self, response):

        try:
            # exchange rate is stored in two parts, across two HTML elements (one in the parent, one in the child
            # element)
            # XPath selector locates child element then selects its immediate parent (because the child
            # element has a constant class attribute value)
            # parsing the xpath here returns the text values of the selected element and all its children,
            # regex is used to extract only numerical portions of the parsed text,
            # and the resulting string is stored as a float (decimal) value, to be used in later mathematical
            # operations.
            exchange_rate = float(
                re.findall(
                    r"[-+]?(?:\d*\.\d+|\d+)",
                    response.xpath("//span[contains(@class,'faded-digits')]/..//text()").get()
                )[0]
            )

            print(
                f"1 NZD = {exchange_rate} USD (1 USD = {1 / exchange_rate} NZD) on {local_datetime.strftime('%A, %-d %B %Y')}"
            )
            print()

            url = "https://www.ubereats.com/nz/store/mcdonalds-point-chevalier/1h7CdIIqR-GG5jVOuHqoFA"

            headers = {
                'authority': 'www.ubereats.com',
                'method': 'GET',
                'path': '/nz/store/mcdonalds-point-chevalier/1h7CdIIqR-GG5jVOuHqoFA',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                          '*/*;q=0.8',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'accept-language': 'en-GB,en;q=0.9',
                # 'content-type': 'application/json',
                'dnt': '1',
                'origin': 'https://www.ubereats.com',
                'referer': 'https://www.ubereats.com',
                # 'referer': 'https://www.ubereats.com/nz/store/mcdonalds-point-chevalier/1h7CdIIqR-GG5jVOuHqoFA',
                # 'referer': 'https://www.ubereats.com/nz/store/mcdonalds-frankton/mNH7d7B5Sq-uVm3qkSmthw',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/102.0.5005.61 Safari/537.36'
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
                url=url,
                headers=headers,
                method="GET",
                callback=self.parse_products,
                meta={
                    "req_h": headers,
                    "fx": exchange_rate,
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        # PageMethod("route", "**/*.{png,jpg,jpeg}, lambda route: route.abort()"),
                        # PageMethod("click", "div#menu-switcher"),
                        # PageMethod("wait_for_load_state", "domcontentloaded"),
                        # PageMethod("click", "div[data-baseweb=popover] ul > li[aria-label=Breakfast] a"),
                        PageMethod("evaluate", "document.body.style.zoom=0.5;"),
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight/5)"),
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight/5)"),
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight/5)"),
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight/5)"),
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight/5)"),
                        PageMethod("wait_for_load_state", "domcontentloaded"),

                        # PageMethod("click", "div.ak.eu > button > svg"),
                        # PageMethod(
                        #     "click",
                        #     "div[data-baseweb=popover] nav[data-baseweb='side-navigation'] > ul > li > a:"
                        # )
                    ]
                }
            )



        except Exception:
            print(
                f'''\n\n
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

    async def parse_products(self, response):

        try:
            async def scroller(target_elements):
                for element in target_elements:
                    await element.click()
                for element in reversed(target_elements):
                    await element.click()

            async def open_close(_card):
                close_button = page.locator("div[data-baseweb=modal] button[data-baseweb][aria-label=Close]")
                await _card.click()
                await page.locator("div[data-baseweb=modal] select").focus()
                await close_button.click()

            async def wait_for_lazy_loading_elements(_locator):
                element_count = await _locator.count()
                while True:
                    await _locator.last.scroll_into_view_if_needed()
                    await _locator.last.focus()
                    await open_close(_locator.last.locator("a"))
                    print(f"Locator count: {element_count}")
                    print(f"Focusing on element {_locator.last}")
                    if element_count == await _locator.count():
                        break
                    await _locator.locator(f":nth-child({element_count + 1})").last.wait_for()
                    print(f"Focusing on element {_locator.last}")
                    element_count = await _locator.count()
                    print(f"Locator count: {element_count}")

            page = response.meta["playwright_page"]
            # Switching to Breakfast Menu and rendering the page

            menu_switcher = page.locator("div#menu-switcher")
            current_menu = menu_switcher.locator("div[data-baseweb='typo-labelmedium']")
            await menu_switcher.click()
            await expect(page.locator("div[data-baseweb=popover] ul")).to_be_visible()
            await page.locator("div[data-baseweb=popover] ul > li[aria-label='Lunch & Dinner'] a").click()
            await expect(current_menu).to_contain_text("Lunch & Dinner")
            menu = await current_menu.inner_text()

            product_list = []
            category_headers = await page.locator("div.li h3").all()
            await scroller(category_headers)
            # page = await page.content()
            category_groups = await page.locator("div.li").all()
            print()
            print("---")
            print(f"{len(category_groups)} categories in {menu} menu.")

            for (i, group) in enumerate(category_groups):
                await scroller(category_headers)
                # await scroller(category_headers)
                if i == len(category_groups):
                    await category_groups[i - 1].locator("h3").scroll_into_view_if_needed()
                    await category_groups[i - 1].locator("h3").click()
                else:
                    await category_groups[i + 1].locator("h3").scroll_into_view_if_needed()
                    await category_groups[i + 1].locator("h3").click()
                await wait_for_lazy_loading_elements(group.locator("li[data-test*=store-item]"))
                category_name = await group.locator("h3").inner_text()
                product_cards = await group.locator("li[data-test*=store-item]").all()
                print()
                print(f"{i + 1}) {category_name} has {len(product_cards)} items:")
                for (j, card) in enumerate(product_cards):
                    # await open_close(card.locator("a"))
                    name = await card.locator("span[data-testid='rich-text']").nth(0).inner_text()
                    price = await card.locator("span[data-testid='rich-text']").nth(1).inner_text()
                    product = {}
                    product["Name"] = name
                    product["Price"] = price
                    product["Category"] = category_name
                    product["Menu"] = menu
                    product_list.append(product)
                    print(f"{j + 1}. {product}")

            """
            parsed_json = json.loads(
                response.xpath("//main[@id='main-content']/script[@type='application/ld+json']")
            )
            headers = response.meta["req_h"]
            exchange_rate = response.meta["fx"]
    
            outlet = parsed_json["name"]

            address = f'{parsed_json["address"]["streetAddress"]}, \
            {parsed_json["address"]["addressLocality"]} \
            {parsed_json["address"]["postalCode"]}, \
            {parsed_json["address"]["addressCountry"]}'
            
            order_page = headers["referer"]
    
    
            section_dict = {}
            menu_sections = parsed_json["hasMenu"]["hasMenuSection"]
    
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
            """


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
