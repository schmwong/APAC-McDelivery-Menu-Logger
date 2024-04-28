
# pip install playwright
# playwright install firefox
# pip install pandas

import sys

sys.dont_write_bytecode = True

import datetime as dt
import pytz
import re
from playwright.sync_api import sync_playwright, expect
import pandas as pd
from pathlib import Path


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Asia/Kolkata"))

# Set headers to make HTTP request to seem to be from a normal browser
my_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "3600",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/71.0.3578.98 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,image/apng,*/*;q=0.8"
}

mcd_menu = "https://mcdelivery.co.in/menu"


# --------------------------------------- #
# Getting the Live Exchange Rate from Xe  #
# --------------------------------------- #

def scrape_exchange_rate():
    page.goto("https://www.xe.com/currencyconverter/convert/?Amount=1&From=INR&To=USD")
    _exchange_rate = float(
        re.findall(
            r"[-+]?(?:\d*\.\d+|\d+)",
            page.locator("//span[contains(@class, 'faded-digits')]/..").inner_text()
        )[0]
    )
    print(
        f"1 INR = {_exchange_rate} USD (1 USD = {1 / _exchange_rate} INR) "
        f"on {local_datetime.strftime('%A, %-d %B %Y')}"
    )
    return _exchange_rate


# -------------------------------------------------------- #
# Rendering all Product Cards on the McDelivery menu page  #
# -------------------------------------------------------- #

def render_menu_page(_product_cards):
    page.goto(mcd_menu)
    expect(page.locator("div.category span").last).to_be_visible()
    page.locator("div.category span").last.click()
    page.wait_for_load_state("domcontentloaded")
    expect(_product_cards.last).to_be_visible()


# ----------------------------------------------------------------#
#  Clicking into each Product Card to scrape data from the Modal  #
# --------------------------------------------------------------- #

def scrape_product_data(_product_cards):
    _product_list = []
    for index, card in enumerate(_product_cards.all()):
        card.click()
        page.wait_for_load_state("domcontentloaded")
        item_name = page.locator("app-product-viewed h5.itemName").inner_text()
        price = page.locator("div.menu__price-calories > div.menu__price-bar >span.menu__price").inner_text()
        category = page.locator("div.bottom-sheet__heading > h5").inner_text()
        back_button = page.locator("div.bottom-sheet__heading > img")
        print(index+1, item_name)
        print(index+1, price)
        print(index+1, category)
        print()
        product = {}
        product["Date"] = local_datetime.strftime("%Y/%m/%d")
        product["Day"] = local_datetime.strftime("%a")
        product["Territory"] = "India"
        product["Menu Item"] = item_name
        product["Price (INR)"] = float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", price)[0])
        product["Price (USD)"] = round((product["Price (INR)"] * exchange_rate), 2)
        product["Category"] = category
        _product_list.append(product)
        back_button.click()
    return _product_list


# ---------------------------------------------------------------------------------------------------- #
# Main Section to Call Other Functions before closing the Browser Session and Exporting Data to File   #
# ---------------------------------------------------------------------------------------------------- #

if __name__ == "__main__":
    with sync_playwright() as pw:
        browser = pw.firefox.launch(headless=False)
        page = browser.new_page(no_viewport=True)
        exchange_rate = scrape_exchange_rate()
        product_cards = page.locator("div.menu.menus__list-card")
        render_menu_page(product_cards)
        product_list = scrape_product_data(product_cards)
        browser.close()

    # ---------------------------------------------------- #
    # Constructing the Dataframe and Exporting it to File  #
    # ---------------------------------------------------- #

    product_list_df = pd.DataFrame(product_list)
    product_list_df.drop_duplicates(
        subset=None, keep='last', inplace=True, ignore_index=True)
    product_list_df.reset_index(drop=True, inplace=True)
    product_list_df.index = pd.RangeIndex(
        start=1, stop=(len(product_list_df.index) + 1), step=1)

    print()
    print(
        f"1 INR = {exchange_rate} USD (1 USD = {1 / exchange_rate} INR) "
        f"on {local_datetime.strftime('%A, %-d %B %Y')}"
    )
    print()
    print(product_list_df)

    timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

    output_file = str(timestamp + " mcd-pwp-in.csv")
    output_dir = Path("./scraped-data")

    # Create directory as required; won't raise an error if directory already exists
    output_dir.mkdir(parents=True, exist_ok=True)

    product_list_df.to_csv(
        (output_dir / output_file),
        float_format="%.2f",
        encoding="utf-8"
    )

    # Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-pwp-vn.csv"
