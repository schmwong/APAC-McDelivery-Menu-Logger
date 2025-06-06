# pip install playwright
# pip install pytest
# pip install pytest-playwright
# apt install xvfb
# playwright install firefox
# xvfb-run -- pytest -vs --headed --browser firefox mcd-pwp-sg.py

import sys

sys.dont_write_bytecode = True

from playwright.sync_api import Page, expect
import datetime as dt
import pytz
import re
import pandas as pd
from pathlib import Path


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Asia/Singapore"))
timestamp = str(local_datetime.strftime("[%Y-%m-%d %H：%M：%S]"))

exchange_rate: float
fx_statement: str
restaurant_name: str
restaurant_address: str
price_list: list = []


def test_get_exchange_rate(page: Page):
    page.context.tracing.start(
        name=f'{timestamp} mcd-sg-fx-trace',
        screenshots=True,
        snapshots=True
    )
    page.goto("https://www.xe.com/currencyconverter/convert/?Amount=1&From=SGD&To=USD")
    page.wait_for_load_state("domcontentloaded")
    global exchange_rate
    exchange_rate = float(
        re.findall(
            r"[-+]?(?:\d*\.\d+|\d+)",
            page.locator("//span[contains(@class,'faded-digits')]/..").inner_text()
        )[0]
    )
    global fx_statement
    fx_statement = (f"\n1 SGD = {exchange_rate} USD (1 USD = {1 / exchange_rate} SGD)"
                    f" on {local_datetime.strftime('%A, %-d %B %Y')}.")
    print(fx_statement)
    page.evaluate("fx_statement => console.log(fx_statement)", fx_statement)
    page.context.tracing.stop(path=f'{timestamp} mcd-sg1-fx-trace.zip')


def test_get_prices(page: Page):
    page.context.tracing.start(
        name=f'{timestamp} mcd-sg-prices-trace',
        title="Maccas Menu Prices from FoodPanda",
        screenshots=True,
        snapshots=True
    )
    page.goto("https://www.foodpanda.sg/restaurant/p8kd/mcdonalds-marine-cove")
    page.get_by_test_id("vendor-info-more-info-btn").click()
    global restaurant_name
    restaurant_name = page.locator("h2#vendor-info-modal-vendor-name").inner_text().strip()
    print(f"\nMaccas Outlet: {restaurant_name}")
    page.evaluate("restaurant_name => console.log('Maccas Outlet: ', restaurant_name)", restaurant_name)
    global restaurant_address
    restaurant_address = page.locator("div.mx-md h1").inner_text().strip()
    print(f"Outlet Address: {restaurant_address}")
    page.evaluate("restaurant_address => console.log('Outlet Address: ', restaurant_address)", restaurant_address)
    page.locator("button[aria-label='Close']").click()

    categories = page.locator("div#category-tabs button[role='tab']").all()
    print(f"\n{len(categories)} categories found")
    for i, category in enumerate(categories):
        category.click()
        category_tab_text = "".join(category.all_inner_texts())
        print(f"{i + 1}. {category_tab_text}")
        page.evaluate("category_tab_text => console.log(category_tab_text)", category_tab_text)

    submenus = page.locator("div.dish-category-section").all()
    assert len(categories) == len(submenus)

    for submenu, category in zip(submenus, categories):
        category.click()
        top_label = category.all_inner_texts()[0]
        num_bracket = str(re.search(r"\(\d+\)", top_label).group())
        num = re.search(r"\d+", num_bracket).group()
        category_name = re.search(r"([^(\d+\)]*)", top_label).group().strip()
        expect(submenu.locator("h2")).to_have_text(category_name)
        # assert submenu.locator("h2").inner_text().strip() == category_name
        print("\n", num, " items in ", category_name)
        page.evaluate("([n, category_name]) => console.log(n, ' items in ', category_name)", [num, category_name])

        items = submenu.locator("ul.dish-list-grid > li.product-tile").all()
        for i, item in enumerate(items):
            item_name = item.locator("h3").inner_text()
            item_price = item.locator("p[data-testid=menu-product-price]").inner_text()
            print(f"{i + 1}. {item_name}: {item_price}")
            page.evaluate("([name, price]) => console.log(name, ': ', price)", [item_name, item_price])
            product = {}
            product["Menu Item"] = item_name
            product["Price (SGD)"] = float(
                re.findall(r"[-+]?(?:\d*\.\d+|\d+)", item_price)[0]
            )
            product["Price (USD)"] = round((product["Price (SGD)"] * exchange_rate), 2)
            product["Category"] = category_name
            product["Menu"] = "Regular"
            global price_list
            price_list.append(product)

    page.context.tracing.stop(path=f'{timestamp} mcd-sg2-prices-trace.zip')


def test_export_data(page: Page):
    global price_list, restaurant_name, restaurant_address
    page.context.tracing.start(
        name=f'{timestamp} mcd-sg-df-trace',
        title="Create DataFrame from scraped menu data",
        screenshots=True,
        snapshots=True
    )
    df = pd.DataFrame(price_list)
    # successively insert 3 new columns from the left
    df.insert(
        loc=0,
        column="Territory",
        value="Singapore",
    )
    df.insert(0, "Day", local_datetime.strftime("%a"))
    df.insert(0, "Date", local_datetime.strftime("%Y/%m/%d"))
    df.index = pd.RangeIndex(
        start=1, stop=(len(df.index) + 1), step=1
    )
    print(df)

    output_file = str(timestamp + " mcd-pwp-sg.csv")
    output_dir = Path("./scraped-data")

    # Create directory as required; won't raise an error if directory already exists
    output_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        (output_dir / output_file),
        float_format="%.2f",
        encoding="utf-8"
    )
    # Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-pwp-sg.csv"

    df_str = df.to_string()

    print()
    print(df_str)

    page.evaluate("restaurant_name => console.log('Maccas Outlet: ', restaurant_name)", restaurant_name)
    page.evaluate("restaurant_address => console.log('Outlet Address: ', restaurant_address)", restaurant_address)
    page.evaluate("fx_statement => console.log(fx_statement)", fx_statement)
    page.evaluate("df_str => console.log(df_str)", df_str)

    page.context.tracing.stop(path = f'{timestamp} mcd-sg3-df-trace.zip')

