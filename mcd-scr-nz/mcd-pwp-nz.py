import sys

sys.dont_write_bytecode = True

import playwright
from playwright.async_api import async_playwright, expect
import asyncio
import datetime as dt
import pytz
import re
import pandas as pd
from pathlib import Path


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Pacific/Auckland"))

xe = "https://www.xe.com/currencyconverter/convert/?Amount=1&From=NZD&To=USD"
ubereats_nz = "https://www.ubereats.com/nz/store/mcdonalds-point-chevalier/1h7CdIIqR-GG5jVOuHqoFA"
menu_switcher = "div#menu-switcher > div[data-baseweb='typo-labelmedium']"
menu_switcher_options = f"div[data-baseweb=popover] ul"
category_groups = "div.li"
category_header = "h3"
product_cards = "li[data-test*=store-item]"


async def scrape_exchange_rate(_page):
    await _page.goto(xe)
    _exchange_rate = float(
        re.findall(
            r"[-+]?(?:\d*\.\d+|\d+)",
            await _page.locator("//span[contains(@class, 'faded-digits')]/..").inner_text()
        )[0]
    )
    print(
        f"1 NZD = {_exchange_rate} USD (1 USD = {1 / _exchange_rate} NZD) "
        f"on {local_datetime.strftime('%A, %-d %B %Y')}"
    )
    return _exchange_rate


async def get_menu_names(_page):
    await _page.locator(menu_switcher).click()
    menus = []
    for option in await _page.locator(menu_switcher_options).locator("li").all():
        await expect(option).to_be_visible()
        menu = await option.get_attribute("aria-label")
        menus.append(menu)
    await _page.locator(menu_switcher).click()
    return menus


async def switch_to_menu(_page, menu_name):
    await _page.locator(menu_switcher).click()
    await expect(_page.locator(menu_switcher_options)).to_be_visible()
    await _page.locator(menu_switcher_options).locator(f"li[aria-label='{menu_name}'] a").click()
    await expect(_page.locator(menu_switcher)).to_contain_text(menu_name)


async def scroller(target_elements):
    async def scroll_and_click(_element):
        await _element.scroll_into_view_if_needed()
        await _element.click()
    for element in target_elements:
        await scroll_and_click(element)
    for element in reversed(target_elements):
        await scroll_and_click(element)


# async def wait_for_lazy_loading_elements(_locator):
#     element_count = await _locator.count()
#     while True:
#         await _locator.last.scroll_into_view_if_needed()
#         if element_count == await _locator.count():
#             break
#         await _locator.locator(f":nth-child({element_count + 1})").last.wait_for()
#         element_count = await _locator.count()
#     return element_count

async def wait_for_lazy_loading_elements(page, product_cards_locator, elements_to_scroll_to, attempts_left):
    element_count = await product_cards_locator.count()
    print(f"Locator count: {element_count}")
    attempts_left -= 1
    while True:
        try:
            await product_cards_locator.last.scroll_into_view_if_needed()
            if element_count == await product_cards_locator.count():
                return element_count
            await product_cards_locator.locator(f":nth-child({element_count + 1})").last.wait_for()
            element_count = await product_cards_locator.count()
        except playwright.async_api.TimeoutError as e:
            if attempts_left > 0:
                attempts_left -= 1
                print(f"Reattempting... [{attempts_left}] tries left.")
                await page.reload()
                await scroller(elements_to_scroll_to)
                await wait_for_lazy_loading_elements(page, product_cards_locator, elements_to_scroll_to, attempts_left)
            else:
                print(e)
                return element_count


async def format_data(_name, _price, _exchange_rate, _category, _menu, _dict_list):
    _product = {}
    _product["Menu Item"] = _name
    _product["Price (NZD)"] = float(
        re.findall(r"[-+]?(?:\d*\.\d+|\d+)", _price)[0]
    )
    _product["Price (USD)"] = round((_product["Price (NZD)"] * _exchange_rate), 2)
    _product["Category"] = _category
    _product["Menu"] = _menu
    _dict_list.append(_product)
    return _dict_list


async def scrape_product_data(_menu, _category, _exchange_rate, _product_cards_locator_list, _dict_list):
    _product_cards = await _product_cards_locator_list
    for (j, _card) in enumerate(_product_cards):
        name = await _card.locator("span[data-testid='rich-text']").nth(0).inner_text()
        price = await _card.locator("span[data-testid='rich-text']").nth(1).inner_text()
        print(f"{j + 1}.", name, price)
        await format_data(name, price, _exchange_rate, _category, _menu, _dict_list)


async def main():
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(args=["--start-maximized"], headless=False)
        page = await browser.new_page(no_viewport=True)
        await page.route(
            "**/*",
            lambda route: route.abort()
            if (
                    route.request.resource_type == "image"
                    or route.request.resource_type == "media"
            )
            else route.continue_(),
        )
        exchange_rate = await scrape_exchange_rate(page)
        await page.goto(ubereats_nz)
        product_list = []
        menus = await get_menu_names(page)
        menus.sort()

        for menu in menus:
            await switch_to_menu(page, menu)
            categories = await page.locator(category_groups).all()
            print("\n---")
            print(f"{len(category_groups)} categories in {menu} menu.")

            for (i, category) in enumerate(categories):
                print()
                await category.locator(category_header).click()
                category_name = await category.locator(category_header).inner_text()
                print(f"{i + 1})", category_name)
                category_header_locators = await page.locator(category_groups).locator(category_header).all()
                await scroller(category_header_locators)
                await wait_for_lazy_loading_elements(page, category.locator(product_cards), category_header_locators, 7)
                await scrape_product_data(
                    menu,
                    category_name,
                    exchange_rate,
                    category.locator(product_cards).all(),
                    product_list,
                )

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
        by=["Menu", "Category"],
        key=lambda x: x.map({"Breakfast": 1, "Lunch & Dinner": 2, "Overnight": 3}),
        na_position="last"
    )

    product_list_df.index = pd.RangeIndex(
        start=1, stop=(len(product_list_df.index) + 1), step=1
    )

    print()
    print(
        f"1 NZD = {exchange_rate} USD (1 USD = {1 / exchange_rate} NZD) on {local_datetime.strftime('%A, %-d %B %Y')}"
    )
    print()
    print(product_list_df)

    timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

    output_file = str(timestamp + " mcd-pwp-nz.csv")
    output_dir = Path("./scraped-data")

    # Create directory as required; won't raise an error if directory already exists
    # output_dir.mkdir(parents=True, exist_ok=True)
    #
    # product_list_df.to_csv(
    #     (output_dir / output_file),
    #     float_format="%.2f",
    #     encoding="utf-8"
    # )
    # Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-pwp-nz.csv"


if __name__ == "__main__":
    asyncio.run(main())

