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
local_datetime = dt.datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
tomorrow = (local_datetime + dt.timedelta(days=1)).strftime("%d/%m/%Y")

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

mcd_vn_home = "https://mcdelivery.vn/vn/home.html"
mcd_vn_guest_address = "https://mcdelivery.vn/vn/guest_address.html"
mcd_menu = "https://mcdelivery.vn/vn/menu.html"


# --------------------------------------- #
# Getting the Live Exchange Rate from Xe  #
# --------------------------------------- #

def scrape_exchange_rate():
    page.goto("https://www.xe.com/currencyconverter/convert/?Amount=1&From=VND&To=USD")
    _exchange_rate = float(
        re.findall(
            r"[-+]?(?:\d*\.\d+|\d+)",
            page.locator("//span[contains(@class, 'faded-digits')]/..").inner_text()
        )[0]
    )
    print(
        f"1 VND = {_exchange_rate} USD (1 USD = {1 / _exchange_rate} VND) "
        f"on {local_datetime.strftime('%A, %-d %B %Y')}"
    )
    return _exchange_rate


# ------------------------------------------------------ #
# Setting the Delivery Address on McDelivery Guest Page  #
# ------------------------------------------------------ #

delivery_address = (
    ("City", "select", "TP Hồ Chí Minh"),
    ("District", "select", "Quận 1"),
    ("Area", "select", "Phường Đa Kao"),
    ("Street", "select", "Đường Điện Biên Phủ"),
    ("HouseNo", "input", "1")
)


# Function to fill form field and assert that it correctly displays the text
def fill_address_field(
        text: str,
        select_field=None,
        input_field=None,
        display_field=None,
        button=None,
        blocking_element=None
):
    if button is not None:
        if blocking_element is not None:
            expect(page.locator(blocking_element)).to_be_enabled()
        page.locator(button).click()
    if select_field is not None:
        expect(page.locator(select_field).locator("xpath=..")).to_be_visible()
        page.locator(select_field).get_by_text(text, exact=True).click()
    if input_field is not None:
        page.locator(input_field).type(text)
        page.keyboard.press("Enter")
    if display_field is not None:
        expect(page.locator(display_field)).to_have_text(text)


def set_delivery_address():
    page.goto(mcd_vn_guest_address)
    page.wait_for_load_state("domcontentloaded")
    expect(page.locator("form.form_deliveryaddress")).to_be_visible()
    for address_line in delivery_address:
        if address_line[1] == "select":
            fill_address_field(
                select_field=f"div#wos{address_line[0]}_chosen ul.chosen-results > li",
                text=address_line[2],
                display_field=f"div#wos{address_line[0]}_chosen span",
                button=f"div#wos{address_line[0]}_chosen > a b",
                blocking_element=f"select#wos{address_line[0]}"
            )
            continue
        fill_address_field(
            input_field=f"input#wos{address_line[0]}",
            text=address_line[2]
        )
    # Form submission redirects to homepage
    page.wait_for_url(mcd_vn_home)
    page.wait_for_load_state("domcontentloaded")
    expect(
        page.locator("a#form_select_address_delivery_address-button > span.ui-selectmenu-status")
    ).to_have_text(
        f"{delivery_address[-1][2]} {delivery_address[-2][2]}, {delivery_address[-3][2]}, "
        f"{delivery_address[-4][2]}, {delivery_address[-5][2]}"
    )


# ------------------------------------------------------------------------------------- #
# Setting the Delivery Date and Time for Access to Different Menus (Callable Function)  #
# ------------------------------------------------------------------------------------- #

delivery_date_time = {
    "date": tomorrow,
    "time": {
        "05:45",  # Breakfast
        "16:00",  # Regular
    }
}


def open_advance_order_form():
    advance_order_button = page.locator("p.action-advance-order > a")
    expect(advance_order_button).to_have_text("Order in Advance")
    advance_order_button.click()
    expect(page.locator("form[action='/vn/selection/menu.html']")).to_be_visible()


def set_delivery_date_time(date: str, time: str):
    page.locator("label[for=form_deliveryoptions_datetime_later]").click()
    date_field = page.locator("a#form_deliveryoptions_date-button > span.ui-selectmenu-status")
    date_field.click()
    date_dropdown = page.locator("ul#form_deliveryoptions_date-menu")
    expect(date_dropdown).to_be_visible()
    date_dropdown.locator("> li > a[role=option]").get_by_text(date).click()
    expect(date_field).to_have_text(date)
    time_field = page.locator("a#form_deliveryoptions_time-button > span.ui-selectmenu-status")
    time_field.click()
    time_dropdown = page.locator("ul#form_deliveryoptions_time-menu")
    expect(time_dropdown).to_be_visible()
    time_dropdown.locator("> li > a[role=option]").get_by_text(time).click()
    expect(time_field).to_have_text(time)
    # print(f"\nSetting delivery date and time to: {date} {time}")
    page.locator("form#form_deliveryoptions  button[type=submit]").click()
    page.wait_for_url(mcd_menu)
    page.wait_for_load_state("domcontentloaded")


# ------------------------------------------------------#
#  Looping through Menus and Categories to Scrape Data  #
# ----------------------------------------------------- #

def scrape_category_urls() -> dict[str, str]:
    menu = page.locator("li.primary-menu-item.selected > a > span").inner_text()
    categories = {
        f"{a.locator(' > span').inner_text()}": f"{mcd_menu}{a.get_attribute('href')}"
        for a in page.locator("li.secondary-menu-item > a").all()
    }
    print(f"\n{menu} menu has {len(categories)} categories:")
    for index, category in enumerate(categories):
        print(index + 1, category, f"   {categories[category]}")
    print()
    return categories


'''
>>> Breakfast menu has 9 categories:
1 Promotions    https://mcdelivery.vn/vn/menu.html?daypartId=2&catId=1
2 BIC w. Korean BBQ & Cheese Sauce    https://mcdelivery.vn/vn/menu.html?daypartId=2&catId=22
3 Combo    https://mcdelivery.vn/vn/menu.html?daypartId=2&catId=10018
4 Happy Meals    https://mcdelivery.vn/vn/menu.html?daypartId=2&catId=6
5 Main menu    https://mcdelivery.vn/vn/menu.html?daypartId=2&catId=9
6 Beverages    https://mcdelivery.vn/vn/menu.html?daypartId=2&catId=5
7 McCAFÉ    https://mcdelivery.vn/vn/menu.html?daypartId=2&catId=8
8 Dessert    https://mcdelivery.vn/vn/menu.html?daypartId=2&catId=4
9 Condiment    https://mcdelivery.vn/vn/menu.html?daypartId=2&catId=17

'''


def scrape_menu_items(category_url):
    category_products = []
    page.goto(category_url)
    page.wait_for_load_state("domcontentloaded")
    category_name = page.locator("ol.breadcrumb > li.active").inner_text()
    product_cards = page.locator("div.product-card").all()
    print(f"\nCategory <{category_name}> has {len(product_cards)} products:")
    for index, card in enumerate(product_cards):
        product = dict()
        product["Date"] = local_datetime.strftime("%Y/%m/%d")
        product["Day"] = local_datetime.strftime("%a")
        product["Territory"] = "Vietnam"
        product["Menu Item"] = card.locator("h5.product-title").inner_text()
        # Regex for currencies in large denominations with "," thousands separator
        product["Price (VND)"] = float(
            re.findall(
                r"[-+]?(?:\d*,\d+|\d+)",
                card.locator("span.starting-price").inner_text()
            )[0].replace(",", "")
        )
        product["Price (USD)"] = round(
            (product["Price (VND)"] * exchange_rate),
            2
        )
        product["Category"] = page.locator("ol.breadcrumb > li.active").inner_text()
        product["Menu"] = page.locator("li.primary-menu-item.selected > a > span").inner_text()
        # print(index + 1, product)
        category_products.append(product)
    return category_products


def scrape_all_products():
    _product_list = []
    for timeslot in delivery_date_time["time"]:
        set_delivery_date_time(
            date=delivery_date_time["date"],
            time=timeslot
        )
        # print(f'\nDelivery set to: {page.locator("div.how-long-to-deliver > span").inner_text()}')
        category_urls = [value for key, value in scrape_category_urls().items()]
        for url in category_urls:
            _product_list.extend(scrape_menu_items(url))
        page.locator("a.action-edit-datetime").click()
        expect(page.locator("form[action='/vn/selection/menu.html']")).to_be_visible()
    return _product_list


# ---------------------------------------------------------------------------------------------------- #
# Main Section to Call Other Functions before closing the Browser Session and Exporting Data to File   #
# ---------------------------------------------------------------------------------------------------- #

if __name__ == "__main__":
    with sync_playwright() as pw:
        browser = pw.firefox.launch(headless=True)
        page = browser.new_page(no_viewport=True)
        exchange_rate = scrape_exchange_rate()
        set_delivery_address()
        open_advance_order_form()
        product_list = scrape_all_products()
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
        print(product_list_df)

        timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))

        output_file = str(timestamp + " mcd-pwp-vn.csv")
        output_dir = Path("./scraped-data")

        # Create directory as required; won't raise an error if directory already exists
        output_dir.mkdir(parents=True, exist_ok=True)

        product_list_df.to_csv(
            (output_dir / output_file),
            float_format="%.2f",
            encoding="utf-8"
        )

        # Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-pwp-vn.csv"
