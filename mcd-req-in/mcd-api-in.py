import sys
sys.dont_write_bytecode = True

import urllib.request
from html.parser import HTMLParser
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import re
import json
from csv import DictWriter, DictReader
from pathlib import Path
import traceback
from time import time


# Reflects local date and time (IST)
local_datetime = datetime.now(timezone.utc).replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Kolkata"))
local_date = local_datetime.strftime("%Y/%m/%d")
local_day = local_datetime.strftime("%a")


class ParseXeRate(HTMLParser):
  def __init__(self, from_currency: str, to_currency: str):
    super().__init__()
    self.found_element = False
    self.text_content = ""
    self.url = f"https://www.xe.com/currencyconverter/convert/?Amount=1&From={from_currency}&To={to_currency}"
    self.headers = {
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,image/apng,*/*;q=0.8"
    }
    self.req = urllib.request.Request(self.url, headers=self.headers)
    # Get the HTML page
    with urllib.request.urlopen(self.req) as response:
      self.page = response.read().decode("utf-8")
    # Feed the page to the parser and loop each element through the class methods
    self.feed(self.page)

  def handle_starttag(self, tag, attrs):
    if (tag == "p") and (("class", "result__BigRate-sc-1bsijpp-1 iGrAod") in attrs):
      self.found_element = True
    elif (tag == "span") and (("class", "faded-digits") in attrs):
      self.found_element = True
    else:
      self.found_element = False

  def handle_data(self, data):
    if (self.found_element):
      self.text_content += data


def fetch_mcd_json() -> list[dict]:
  mcd_url = "https://be.mcdelivery.co.in/product/get-menu?store_id=1&business_model_id=4"
  json_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "3600",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    "Accept": "application/json; charset=utf-8"
  }
  req = urllib.request.Request(mcd_url, headers=json_headers)
  with urllib.request.urlopen(req) as response:
    menu_items = json.loads(response.read())
    return menu_items
  


def output_filename() -> str:
  timestamp = str(local_datetime.strftime("[%Y-%m-%d %H:%M:%S]"))
  return str(timestamp + " mcd-api-in.csv")


def filepath(filename) -> Path:
  output_dir = Path(Path.cwd() / "scraped-data")
  output_dir.mkdir(parents=True, exist_ok=True)
  return Path(output_dir / filename)


def write_mcd_csv(menu_items, exchange_rate, filepath):
  with open(filepath, "w") as csvfile:
    fieldnames = ["", "Date", "Day", "Territory", "Menu Item", "Price (INR)", "Price (USD)", "Category"]
    writer = DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for i, item in enumerate(menu_items, start=1):
      row = {
        "": i,
        "Date": local_date,
        "Day": local_day,
        "Territory": "India",
        "Menu Item": item["item_name"].replace("\t", ""),
        "Price (INR)": f'{item["item_price"]["discount_price"]:.2f}',
        "Price (USD)": f'{round((item["item_price"]["discount_price"] * exchange_rate), 2):.2f}',
        "Category": item["category_name"]
      }
      writer.writerow(row)


def print_mcd_csv(filepath: Path):
  with open(filepath, "r") as csvfile:
    reader = DictReader(csvfile)
    # Read all rows into a list of dictionaries
    rows = list(reader)
    # Get the keys (column names) from the first row
    keys = reader.fieldnames
    # Get the maximum length of each column
    max_lengths = [max(len(row[key]) for row in rows + [{key: key}]) for key in keys]
    # Print the headers
    for key, max_length in zip(keys, max_lengths):
        print(f"{key:{max_length}}", end="  ")
    print()
    # Print the separator line
    def print_separator_line(char='-'):
        for max_length in max_lengths:
          print(char * max_length, end='  ')
        print()
    print_separator_line()
    # Print the data rows
    for row in rows:
        for key, max_length in zip(keys, max_lengths):
          print(f'{row[key]:{max_length}}', end='  ')
        print()
    print_separator_line()



if __name__ == "__main__":
  try:
    start = time()
    xe_parser = ParseXeRate("INR", "USD")
    fx_inr_usd = float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", xe_parser.text_content)[0])
    print(f"\nParse FX time: {round((time() - start), 6)} seconds")
    print(f"1 INR = {fx_inr_usd} USD on {local_datetime.strftime('%A, %-d %B %Y')}\n")
    data = fetch_mcd_json()
    print(f"Fetch JSON time: {round((time() - start), 6)} seconds")
    print(f"Write CSV time: {round((time() - start), 6)} seconds\n")
    output_file = output_filename()
    output_filepath = filepath(output_file)
    write_mcd_csv(data, fx_inr_usd, output_filepath)
    print_mcd_csv(output_filepath)
    print(f'''\n\nExported to file:
				  https://github.com/schmwong/APAC-McDelivery-Menu-Logger/tree/main/mcd-req-in/scraped-data/{output_file.replace(" ", "%20")}\n\n ============ \n\n\n\n\n\n''')
    
  except Exception:
    print(f"\n\n---\nOne or more errors occurred:\n\n{traceback.format_exc()}\n---\n\n")


# Output filename format: "[YYYY-MM-DD hh:mm:ss] mcd-api-in.csv"
