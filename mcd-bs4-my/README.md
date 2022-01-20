### Malaysia Changelog

- Built upon the original script used for [Singapore]("https://github.com/schmwong/APAC-McDelivery-Menu-Logger/blob/main/mcd-bs4-sg/mcd-bs4-sg.py").
- URL list is populated by extracting `href` values from the starting pages.
- Written in Python 3.8.2.
-	Libraries:
	-	**bs4** : Beautiful Soup 4
	-	**pandas**
	-	**datetime**
	-	**requests**
	-	**re** : Regular Expressions

---

### 0.0.1 (2022-01-20)

***Initial Development***

1. Added the `&locale=en` query parameter to each URL to ensure the data is scraped in English.
2. Corrected CSS selector for scraping links: changed from <br>
`ul.secondary-menu-item:not(:first-child) a[href]` <br> 
to `li.secondary-menu-item:not([class*='selected']) a[href]`
3. Updated the Xe.com URL to correctly scrape the MYR to USD exchange rate.
4. Created an automated Github Workflow to run the scraper once a day ([scrape-my-auto.yml](https://github.com/schmwong/APAC-McDelivery-Menu-Logger/blob/main/.github/workflows/scrape-my-auto.yml)).