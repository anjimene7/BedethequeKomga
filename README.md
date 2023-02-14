# Bedetheque metadata scraper for Komga - Work in progress!! Not yet usable

## Introduction

This Script gets a list of every BDs available on your Komga instance,
looks it up one after another on [Bedetheque](https://www.bedetheque.com/) and gets the metadata for the specific series.
This metadata then gets converted to be compatible to Komga and then gets sent to the server instance and added to the BDs entry.

## Features

### completed

See [DESIGN](DESIGN.md) for processing logic

### TODO

- [ ] Manga Series Add Metadata
- [ ] Adding Metadata to a Single Manga
- [ ] Automatically skip entries with refreshed metadata
- [ ] Optional processing range: ①All book series; ②Book series in the specified library; ③Book series in the specified collection


## Requirements

- A Komga instance with access to the admin account
- Either Windows/Linux/MAc or alternatively Docker
- Python installed if using Windows, Linux or Mac natively

## refresh metadata

1. Install the requirements using `pip install -r requirements.txt`
2. Rename `config.template.py` to `config.py` and edit the url, email and password to match the ones of your komga instance (User needs to have permission to edit the metadata).

    `FORCE_REFRESH_LIST` Book series to force refresh to avoid automatic skipping. You can get it by clicking the book series (corresponding link) on the komga interface, in the form of: `'0B79XX3NP97K9'`. When filling in, `''`wrap in English quotation marks and `,` separate with English commas. 

    `KOMGA_LIBRARY_LIST` Processes the book series in the specified library. You can get it by clicking the library (corresponding link) on the komga interface, in the form of:`'0B79XX3NP97K9'`. When filling in, `''` wrap in English quotation marks and `,` separate with English commas. and `KOMGA_COLLECTION_LIST` cannot be used at the same time

    `KOMGA_COLLECTION_LIST` Processes the book series in the specified collection. You can get it by clicking Favorite (corresponding link) on the komga interface, in the form of: `'0B79XX3NP97K9'`. When filling in, `''` wrap in English quotation marks and `,` separate with English commas. and `KOMGA_LIBRARY_LIST` cannot be used at the same time

3. Run the script using `python refreshMetadata.py` Note: Processed series and books will be automatically skipped

**Tips:**

If there is no need to refresh series that have failed:
- You can modify it `upsert_series_record` to `0` `1`
- Or modify the database yourself

## Issues & Pull Requests

Welcome to submit new rules, issues, features...

## thank you

Part of the code and ideas of this project come from [chu-shen/BangumiKomga](https://github.com/chu-shen/BangumiKomga), thank you here!

Also thanks to the following excellent projects:：
- [gotson/komga](https://github.com/gotson/komga)
- [aubustou/bedetheque_scraper](https://github.com/aubustou/bedetheque_scraper)
