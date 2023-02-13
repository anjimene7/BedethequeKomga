
import processMetadata
from time import strftime, localtime
from env import *
from log import logger
from bedethequeApi import *


def refresh_metadata(force_refresh_list=[]):
    '''
    Refresh book series metadata
    '''
    env = InitEnv()

    komga = env.komga
    all_series = env.all_series
    proxy = bedethequeApi()

    # Loop through each book series
    for serie in all_series:
        serie_id = serie['id']
        serie_name = serie['name']
        serie_url = None

        force_refresh_flag = serie_id in force_refresh_list
        # # Skip the serie if it's not in the force refresh list // TODO
        # if len(force_refresh_list) > 0 and not force_refresh_flag:
        #     continue

        # Get the bedetheque link if it exists // TODO: find it if it doesn't exists
        for link in serie['metadata']['links']:
            if link['label'].lower() == "www.bedetheque.com":
                serie_url = link['url']
                break

        #get the metadata for the series from bedetheque
        if serie_url is None:
            break
        bedetheque_metadata = get_comic_series_metadata(serie_url, proxy = proxy)

        # Prepare the metadata
        processedMetadata = processMetadata.prepareKomgaSeriesMetadata(
            bedetheque_metadata, serie['metadata'], serie_url)

        if(processedMetadata.isvalid == False):
            logger.warning("Failed to update series " + serie_name)
            break

        serie_data = {
            "status": processedMetadata.status,
            "summary": processedMetadata.summary,
            "publisher": processedMetadata.publisher,
            "genres": processedMetadata.genres,
            "title": processedMetadata.title,
            # "ageRating": processedMetadata.ageRating,
            "links": processedMetadata.links,
            "totalBookCount": processedMetadata.totalBookCount
        }

        # Update the metadata for the series on komga
        isSuccessed = komga.update_series_metadata(serie_id, serie_data)
        if(isSuccessed):
            logger.info("Successfully update series " + serie_name)
        else:
            logger.warning("Failed to update series " + serie_name)
            continue

        # call the refresh on the books of this serie
        refresh_book_metadata(komga, serie_id, force_refresh_flag, proxy = proxy)


def refresh_book_metadata(komga, series_id, force_refresh_flag, proxy = None):
    '''
    Refresh Book Metadata
    '''
    # Get all books in the series on komga
    all_books = komga.get_series_books(series_id)

    # Loop through each book in the series on komga
    for book in all_books['content']:
        book_id = book['id']
        book_name = book['name']
        book_url = None

        # # Skip the book if it's not in the force refresh list // TODO
        # if len(force_refresh_list) > 0 and not force_refresh_flag:
        #     continue

        # Get the bedetheque link if it exists // TODO: find it if it doesn't exists
        for link in book['metadata']['links']:
            if link['label'].lower() == "www.bedetheque.com":
                book_url = link['url']
                break

        #get the metadata for the series from bedetheque
        if book_url is None:
            break
        bedetheque_metadata = get_comic_book_metadata(book_url, proxy = proxy)

        # Prepare the metadata
        processedMetadata = processMetadata.prepareKomgaBookMetadata(bedetheque_metadata, book['metadata'], book_url)

        if(processedMetadata.isvalid == False):
            logger.warning("Failed to prepare book metadata. Book: " + book_name)
            break

        book_data = {
            "authors": processedMetadata.authors,
            "summary": processedMetadata.summary,
            "title": processedMetadata.title,
            # "isbn": processedMetadata.isbn,
            "number": processedMetadata.number,
            "links": processedMetadata.links
            # "releaseDate": processedMetadata.releaseDate,
            # "numberSort": processedMetadata.numberSort
        }

        # Update the metadata for the series on komga
        isSuccessed = komga.update_book_metadata(
            book_id, book_data)
        if(isSuccessed):
            logger.info("Successfully update book " + book_name)
        else:
            logger.warning("Failed to update book " + book_name)
        break

refresh_metadata(FORCE_REFRESH_LIST)
