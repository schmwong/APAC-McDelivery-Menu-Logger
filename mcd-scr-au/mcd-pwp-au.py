# pip install playwright
# apt install xvfb
# playwright install firefox
# xvfb-run -- python3 mcd-pwp-au.py

import sys

sys.dont_write_bytecode = True

import playwright.async_api
from playwright.async_api import async_playwright, expect
import asyncio
import datetime as dt
import pytz
import re
import pandas as pd
from pathlib import Path


# Reflects local time
local_datetime = dt.datetime.now(pytz.timezone("Australia/Melbourne"))

xe = "https://www.xe.com/currencyconverter/convert/?Amount=1&From=AUD&To=USD"
ubereats_au = "https://www.ubereats.com/au/store/mcdonalds-clifton-hill/SIaq6LrDTFemKVajhXM-iA"
menu_switcher = "div#menu-switcher > div[data-baseweb='typo-labelmedium']"
menu_switcher_options = f"div[data-baseweb=popover] ul"
category_groups = "li.bb > div.me"
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
        f"1 AUD = {_exchange_rate} USD (1 USD = {1 / _exchange_rate} AUD) "
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


async def scroller(elements_to_scroll_to):
    async def scroll_and_click(_element):
        await _element.scroll_into_view_if_needed()
        await _element.click()
    for element in elements_to_scroll_to:
        await scroll_and_click(element)
    for element in reversed(elements_to_scroll_to):
        await scroll_and_click(element)


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


async def format_data(name, price, exchange_rate, category, menu, dict_list):
    _product = {}
    _product["Menu Item"] = name
    _product["Price (AUD)"] = float(
        re.findall(r"[-+]?(?:\d*\.\d+|\d+)", price)[0]
    )
    _product["Price (USD)"] = round((_product["Price (AUD)"] * exchange_rate), 2)
    _product["Category"] = category
    _product["Menu"] = menu
    dict_list.append(_product)
    return dict_list


async def scrape_product_data(menu_name, category_name, product_cards_locator, holding_obj, index=0):
    _product_cards = await product_cards_locator.all()
    for (j, _card) in enumerate(_product_cards[index:]):
        name = await _card.locator("span[data-testid='rich-text']").nth(0).inner_text()
        price = await _card.locator("span[data-testid='rich-text']").nth(1).inner_text()
        if price.lower() == "sold out":
            price = await _card.locator("span[data-testid='rich-text']").nth(3).inner_text()
        holding_obj[menu_name][category_name].append((name, price))
        # print(f"{j + 1}.", name, price)
        # await format_data(name, price, exchange_rate, category_name, menu_name, _dict_list)
    for (j, product) in enumerate(holding_obj[menu_name][category_name]):
        name = product[0]
        price = product[1]
        print(f"{j + 1}.", name, price)


async def verify_item_counts(
        page,
        menu_name: str,
        category_name: str,
        product_cards_locator,
        elements_to_scroll_to,
        holding_obj: dict[str, dict[str, tuple]],
        attempts_left
):
    attempts_left -= 1
    _scraped_products = holding_obj[menu_name][category_name]
    await page.reload()
    await scroller(elements_to_scroll_to)
    _new_count = await wait_for_lazy_loading_elements(page, product_cards_locator, elements_to_scroll_to, 7)
    print(f"New Count: {_new_count}")
    print(f"Current Count: {len(_scraped_products)}")
    if len(_scraped_products) == _new_count:
        print(f"{len(_scraped_products)} items. All good.\n")
        return 0
    elif (_new_count - (len(_scraped_products)) > 0) and (attempts_left > 0):
        attempts_left -= 1
        print(f"Attempting to scrape {_new_count - len(_scraped_products)} new items...\n")
        await scrape_product_data(
            menu_name,
            category_name,
            product_cards_locator,
            holding_obj,
            index=len(_scraped_products)
        )
        await verify_item_counts(
            page,
            menu_name,
            category_name,
            product_cards_locator,
            elements_to_scroll_to,
            holding_obj,
            attempts_left
        )
    return 1


items_tmp = {
    "menu1": {
        "category1": [("item1", "price1"), ("item2", "price2")],
        "category2": [("item1", "price1"), ("item2", "price2"), ("item3", "price3")],
    },
    "menu2": {
        "category1": [("item1", "price1")],
        "category2": [("item1", "price1"), ("item2", "price2")],
    },
}


async def main():
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(args=["--start-maximized"], headless=False)
        page = await browser.new_page(no_viewport=True)
        await page.route(
            "**/*",
            lambda route: route.abort()
            if (
                    route.request.resource_type == "image"
                    or route.request.resource_type == "image/webp"
                    or route.request.resource_type == "media"
            )
            else route.continue_(),
        )
        exchange_rate = await scrape_exchange_rate(page)
        await page.goto(ubereats_au)
        menus = await get_menu_names(page)
        menus.sort()
        scraped_items: dict[str, dict] = {menu: {} for menu in menus}

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
                print("First scrape...")
                if category_name not in scraped_items[menu]:
                    scraped_items[menu][category_name] = []
                category_header_locators = await page.locator(category_groups).locator(category_header).all()
                await scroller(category_header_locators)
                await wait_for_lazy_loading_elements(page, category.locator(product_cards), category_header_locators, 7)
                await scrape_product_data(
                    menu,
                    category_name,
                    category.locator(product_cards),
                    scraped_items,
                )

            # for (i, category) in enumerate(categories):
            #     print()
            #     print("Checking item counts...")
            #     await category.locator(category_header).click()
            #     category_name = await category.locator(category_header).inner_text()
            #     category_header_locators = await page.locator(category_groups).locator(category_header).all()
            #     print(f"{i + 1})", category_name)
            #     await verify_item_counts(
            #         page,
            #         menu,
            #         category_name,
            #         category.locator(product_cards),
            #         category_header_locators,
            #         scraped_items,
            #         7
            #     )

    product_list = []
    for menu in scraped_items:
        for category in scraped_items[menu]:
            for item in scraped_items[menu][category]:
                await format_data(
                    name=item[0],
                    price=item[1],
                    exchange_rate=exchange_rate,
                    category=category,
                    menu=menu,
                    dict_list=product_list
                )

    product_list_df = pd.DataFrame(product_list)

    # successively insert 3 new columns from the left
    product_list_df.insert(
        loc=0,
        column="Territory",
        value="Australia",
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
        f"1 AUD = {exchange_rate} USD (1 USD = {1 / exchange_rate} AUD) on {local_datetime.strftime('%A, %-d %B %Y')}"
    )
    print()
    print(product_list_df)

    timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

    output_file = str(timestamp + " mcd-pwp-au.csv")
    output_dir = Path("./scraped-data")

    # Create directory as required; won't raise an error if directory already exists
    output_dir.mkdir(parents=True, exist_ok=True)

    product_list_df.to_csv(
        (output_dir / output_file),
        float_format="%.2f",
        encoding="utf-8"
    )
    # Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-pwp-au.csv"


if __name__ == "__main__":
    asyncio.run(main())
