import traceback

import processMetadata
from env import InitEnv
from log import logger
from bedethequeApi import bedethequeApiProxies, find_series_url, get_comic_series_metadata, \
                            find_comic_url, get_comic_book_metadata, get_comic_book_url_from_isbn
from selenium import webdriver
from traceback import format_exc
import tempfile
from typing import Optional
from random import shuffle
import os

def refresh_series_metadata(env):
    '''
    Refresh book series metadata
    '''
    dry_run = env.dry_run
    komga = env.komga
    all_series = env.all_series
    proxy = None
    if env.use_proxies:
        proxy = bedethequeApiProxies()
    else:
        logger.warning("Mode No proxy requested, delay between each request = %d seconds", env.wait_delay)

    # Loop through each book series
    nbr_serie_to_update = 0
    for serie in all_series:
        if serie['metadata']['status'] in env.status_to_update:
            nbr_serie_to_update += 1
    logger.info(f"Start updating {nbr_serie_to_update} series")
    nbr_serie_updated = 0
    #shuffle(all_series)
    for serie in all_series:
        nbr_serie_updated += 1
        with open(f'{os.path.dirname(os.path.realpath(__file__))}/already_done.txt', 'r+') as f:
            if serie['id'] in [x.strip() for x in f.readlines()]:
                logger.info(f"{serie['id']} already in txt file, continue")
                continue

        if not serie['metadata']['status'] in env.status_to_update:
            continue
        logger.info("####################################")
        serie_title = serie['metadata']['title']
        serie_id = serie['id']
        if not (serie_name := serie['metadata']['title']):
            serie_name = serie['name']
        with open(f'{os.path.dirname(os.path.realpath(__file__))}/id_series.csv') as ff:
            for line in ff.readlines():
                if serie_id in line:
                    logger.info(f"{serie_name} already in csv file, continue")
                    continue
        logger.info(f"Processing series {serie_title}")

        serie_url = None
        with open(f'{os.path.dirname(os.path.realpath(__file__))}/id_series.csv', 'r') as ff:
            for line in ff.readlines():
                if serie_id in line:
                    serie_url = line.split('|')[3].strip()
        #serie_url = find_url(serie, serie_name, proxy)
        if not serie_url:
            logger.warning(f"Could not find serie url, please populate it manually in Komga.")
            with open(f'{os.path.dirname(os.path.realpath(__file__))}/id_series.csv', 'r+') as f:
                komga.write_to_file('', '', serie_id)
            continue

        bedetheque_metadata = get_comic_series_metadata(serie_url, proxy=proxy, wait_delay=env.wait_delay)
        if bedetheque_metadata is None:
            logger.warning(f"Incorrect metadata for {serie_name}, skipping")
            continue

        # Prepare the metadata
        processedMetadata = processMetadata.prepareKomgaSeriesMetadata(bedetheque_metadata, serie['metadata'], serie_url)
        if processedMetadata.isvalid is False:
            logger.warning(f"Failed to update series {serie_name}")
            continue

        serie_data = {
            "status": processedMetadata.status,
            "summary": processedMetadata.summary,
            "publisher": processedMetadata.publisher,
            "genres": processedMetadata.genres,
            "title": processedMetadata.title,
            "links": processedMetadata.links,
            "tags": processedMetadata.tags,
            "totalBookCount": processedMetadata.totalBookCount
        }

        # Update the metadata for the series on komga
        if komga.update_series_metadata(serie_id, serie_data, dry_run):
            logger.info("Successfully updated series %d/%d -  %s", nbr_serie_updated, nbr_serie_to_update, serie_name)
            komga.update_collections_metadata(serie_id, bedetheque_metadata, dry_run)
        else:
            logger.warning("Failed to update series %s", serie_name)
            continue

        # call the refresh on the books of this serie
        if not env.series_only:
            refresh_book_metadata(None, komga, serie_id, serie_url, proxy=proxy, wait_delay=env.wait_delay, dry_run=dry_run)

        with open(f'{os.path.dirname(os.path.realpath(__file__))}/already_done.txt', 'a+') as f:
            f.write(f"{serie_id}\n")

    komga.delete_collections()
    logger.info("Refresh successfully terminated")

def refresh_book_metadata(driver, komga, series_id, serie_url, proxy = None, wait_delay = None, dry_run = True):
    '''
    Refresh Book Metadata
    '''
    # Get all books in the series on komga
    all_books = komga.get_series_books(series_id)

    # Loop through each book in the series on komga
    for book in all_books['content']:
        logger.info(f"Processing book {book['metadata']['title']}")

        book_id = book['id']
        with open(f'{os.path.dirname(os.path.realpath(__file__))}/already_done.txt', 'r+') as f:
            if book_id in [x.strip() for x in f.readlines()]:
                logger.info(f"{book_id} already in txt file, continue")
                continue
        if not (book_name := book['metadata']['title']):
            book_name = book['name']

        book_isbn = book['metadata'].get('isbn', None)
        if not book_isbn and False:
            with tempfile.TemporaryDirectory() as tmpdirname:
                try:
                    book_isbns = komga.get_isbn_from_book(book_id, tmpdirname)
                except Exception as e:
                    logger.error(f"Could not extract ISBN for {book_name}: {format_exc()}")
                else:
                    values_isbn = book_isbns['barcode']
                    values_str_match = book_isbns['string_match']
                    if not values_isbn and not values_str_match:
                        logger.warning(f"Could not find ISBN for {book_name}")
                    elif values_isbn:
                        if len(values_isbn) > 1:
                            logger.warning(f"Found more than one match for ISBN (barcode) for {book_name}: {values_isbn}. Keeping first one")
                        book_isbn = values_isbn[0]
                        logger.info(f"Found ISBN (barcode) from images for {book_name}: {book_isbn}")
                    else:
                        if len(values_str_match) > 1:
                            logger.warning(f"Found more than one match for ISBN (string match) for {book_name}: {values_str_match}. Keeping first one")
                        book_isbn = values_str_match[0]
                        logger.info(f"Found ISBN (string match) from images for {book_name}: {book_isbn}")

        book_url = None
        # Get the bedetheque link if it exists
        for link in book['metadata']['links']:
            if link['label'].lower() == "www.bedetheque.com":
                book_url = link['url']
                break
        if book_url is None:
            if serie_url is None:
                logger.warning("No URL found for %s, skipping metadata refresh for this book", book_name)
                continue
            #book_url = get_comic_book_url_from_isbn(driver, book['metadata']['isbn'])
            book_url = find_comic_url(book_name, book['metadata']['number'], serie_url, proxy = proxy, wait_delay = wait_delay)

        #get the metadata for the series from bedetheque
        if book_url is None:
            logger.warning("No URL found for %s, skipping metadata refresh for this book", book_name)
            continue
        bedetheque_metadata = get_comic_book_metadata(book_url, proxy = proxy, wait_delay = wait_delay)

        #checking we have no issue with the metadata
        if bedetheque_metadata is None:
            logger.warning("Incorrect URL found for %s, trying to look for the URL", book_name)
            book_url = find_comic_url(book_name, book['metadata']['number'], serie_url, proxy = proxy, wait_delay = wait_delay)
            if book_url is None:
                logger.warning("No URL found for %s, skipping metadata refresh for this book", book_name)
                continue
            bedetheque_metadata = get_comic_book_metadata(book_url, proxy = proxy, wait_delay = wait_delay)
            if bedetheque_metadata is None:
                logger.error("Error while parsing URL %s found for %s, skipping metadata refresh for this book", book_url, book_name)
                continue

        # Prepare the metadata
        processedMetadata = processMetadata.prepareKomgaBookMetadata(bedetheque_metadata, book['metadata'], book_url)

        if processedMetadata.isvalid is False:
            logger.warning("Failed to prepare book metadata. Book: %s", book_name)
            continue

        book_data = {
            "authors": processedMetadata.authors,
            "summary": processedMetadata.summary,
            "title": processedMetadata.title,
            "isbn": processedMetadata.isbn,
            "number": processedMetadata.number,
            "links": processedMetadata.links,
            "releaseDate": processedMetadata.releaseDate
            # "numberSort": processedMetadata.numberSort
        }

        # Update the metadata for the series on komga
        if komga.update_book_metadata(book_id, book_data, dry_run):
            logger.info("Successfully updated book %s", book_name)
            logger.info("------------------------------------")
            with open(f'{os.path.dirname(os.path.realpath(__file__))}/already_done.txt', 'a+') as f:
                f.write(f"{book_id}\n")
        else:
            logger.warning("Failed to updated book %s", book_name)
            logger.warning("Failed to updated book %s", book_name)
            logger.info("------------------------------------")
            break

def find_url(serie, serie_name, proxy) -> Optional[str]:
    serie_url = None
    # Get the bedetheque link if it exists already in Komga
    for link in serie['metadata']['links']:
        if link['label'].lower() == "www.bedetheque.com":
            serie_url = link['url']
            break
    if serie_url is None:
        serie_url = find_series_url(serie_name, proxy=proxy, wait_delay=env.wait_delay)
    return serie_url


if __name__ == "__main__":
    #driver = webdriver.Remote(
    #    command_executor='http://127.0.0.1:4444/wd/hub',
    #    options=webdriver.ChromeOptions()
    #)
    try:
        env = InitEnv()
        if not os.path.exists(f'{os.path.dirname(os.path.realpath(__file__))}/id_series.csv'):
            os.mknod(f'{os.path.dirname(os.path.realpath(__file__))}/id_series.csv')
        refresh_series_metadata(env)
    except Exception as e:
        logger.error(f"Got exception {e}: {traceback.print_exc()}")
    finally:
    #    driver.close()
        print()
