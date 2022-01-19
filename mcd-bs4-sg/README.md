## Singapore Changelog

- This is my first automated webscraping project.
- Written in Python 3.8.2.
-	Libraries:
	-	**bs4** : Beautiful Soup 4
	-	**pandas**
	-	**datetime**
	-	**requests**
	-	**re** : Regular Expressions
- Webpage URLs were manually added instead of extracting `href` values from the starting URL.

---

### 0.0.2 (2022-01-19)

***New***

1. Created scraper to get the live SGD to USD exchange rate from Xe.com.
2. Created and successfully test-run manually triggered Github Workflow file ([scrape-sg-manual.yml](https://github.com/schmwong/APAC-McDelivery-Menu-Logger/blob/main/.github/workflows/scrape-sg-manual.yml)).


***Improved***

1. Edited and expanded Dictionary:
	1. New layout containing 9 fields: <br> { `Date`, `Day`, `Territory`, `Menu Item`, `Price (SGD)`, `Price (USD)`, `Category`, `Menu` }
	2. Added 2 datetime fields: `Date` in *yyyy-mm-dd*, and `Day` in *ddd* format.
	3. Added `Territory` field to enable filtering by Country / Territory in future projects.
	4. Changed name of `Name` field to `Menu Item`.
	5. Changed name of `Price` field to `Price (SGD)`.
	6.  Added `Price (USD)` field, using the live exchange rate for currency conversion.

2. Timestamp with `[yyyy-mm-dd HH:MM:SS]` format added as prefix to `.csv` filename.

### 0.0.1 (2022-01-18)

***Initial Development***

1. Started with the initial draft on Jupyter Notebook.
2. Set HTTP request headers.
3. Changed CSS selector for inner loop of scraper to `"div.product-card"`.
4. Tested parsers `lxml` and `html5lib` before deciding on `lxml`.
5. Built Dictionary (i.e. associative array) containing 4 fields: `Name`, `Price`, `Category`, `Menu`.
6. Tested DataFrame (i.e. table) construction and saving to `.csv` file.