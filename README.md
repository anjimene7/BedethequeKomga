# Bedetheque metadata scraper for Komga

## Introduction

This Script gets a list of every BDs available on your Komga instance,
looks it up one after another on [Bedetheque](https://www.bedetheque.com/) and gets the metadata for the specific series.
This metadata then gets converted to be compatible to Komga and then gets sent to the server instance and added to the BDs entry.

## Features

### Completed
- [X] Add Metadata to BD Series and books
- [X] Automatically skip entries which are locked on Komga
- [X] Optional processing range: ①All book series; ②Book series in the specified library; ③Book series in the specified collection
- [X] Retrieve metadata using a proxy automaticaly
- [X] Detailed log file create at each run
- [X] Refresh only BD by Status. By default, only ONGOING and HIATUS
- [X] Adding Metadata to a specific series (and their underlying books)

### TODO




## Requirements

- A Komga instance with access to the admin account
- Either Windows/Linux/MAc or alternatively Docker
- Python installed if using Windows, Linux or Mac natively

## refresh metadata

1. Install the requirements using `pip install -r requirements.txt`
2. Rename `config.template.py` to `config.py` and edit the url, email and password to match the ones of your komga instance (User needs to have permission to edit the metadata).

    `KOMGA_LIBRARY_LIST` Processes the book series in the specified library. You can get it by clicking the library (https://komgaURL/libraries/**02A5TD2KH8SQW**/series) on the komga interface, in the form of:`'0B79XX3NP97K9'` (and sometime for old entries, just some numbers). When filling in, `''` wrap in English quotation marks and `,` separate with English commas. and `KOMGA_COLLECTION_LIST` and `KOMGA_SERIE_LIST` cannot be used at the same time

    `KOMGA_COLLECTION_LIST` Processes the book series in the specified collection. You can get it by clicking Favorite (https://komgaURL/collections/**0BEVBQDGY77SA**) on the komga interface, in the form of: `'0B79XX3NP97K9'` (and sometime for old entries, just some numbers). When filling in, `''` wrap in English quotation marks and `,` separate with English commas. and `KOMGA_LIBRARY_LIST` and `KOMGA_SERIE_LIST` cannot be used at the same time

    `KOMGA_SERIE_LIST` Processes the book series specified. You can get it by clicking the serie (https://komgaURL/series/**02A5244DQGRDE**) on the komga interface, in the form of:`'0B79XX3NP97K9'` (and sometime for old entries, just some numbers). When filling in, `''` wrap in English quotation marks and `,` separate with English commas. and `KOMGA_LIBRARY_LIST` and `KOMGA_COLLECTION_LIST`cannot be used at the same time

    Leave the three of them empty to process everything


    `KOMGA_STATUS` Processes the book series in the specified status. By default, books are added to Komga in "En cours" (ONGOING) Status. On this script, by default, only refresh ONGOING and HIATUS (suspendu) status. But it can be forced to perform it for `'ONGOING'`, `'HIATUS'`, `'ENDED'` or `'ABANDONED'`, seperated by a coma `,`.

3. Run the script using `python refreshMetadata.py` Note: Locked field will be automatically skipped

**NB:**

The script first retrieve a list of proxies before interrogating bedetheque, to limit the chance of being blacklisted with too many calls.
However, this method is not perfect. Please don't use it on a large library at once. Be respectful of bedetheque bandwitch ;)

## Issues & Pull Requests

Welcome to submit new rules, issues, features...

## thank you

Part of the code and ideas of this project come from [chu-shen/BangumiKomga](https://github.com/chu-shen/BangumiKomga), thank you here!

Also thanks to the following excellent projects:：
- [gotson/komga](https://github.com/gotson/komga)
- [aubustou/bedetheque_scraper](https://github.com/aubustou/bedetheque_scraper)
