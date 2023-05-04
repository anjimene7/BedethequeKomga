import processMetadata
from env import InitEnv
from log import logger
from bedethequeApi import bedethequeApiProxies, find_series_url, get_comic_series_metadata, \
                            find_comic_url, get_comic_book_metadata


def refresh_metadata():
    '''
    Refresh book series metadata
    '''
    env = InitEnv()

    komga = env.komga
    all_series = env.all_series
    proxy = None
    if env.use_proxies:
        proxy = bedethequeApiProxies()
    else:
        logger.warning("Mode No proxy requested")
        if env.wait_delay<5:
            chooseToContinue = input("Delay between each request is very low. Are you sure you want to continue (risk of ban) (Y/N): ")
            if chooseToContinue.lower() == 'y':
                logger.warning("Continuing with low delay")
            else:
                logger.error("Choose to not continue. Exiting")
                exit()

    # Loop through each book series
    for serie in all_series:
        serie_id = serie['id']
        if not (serie_name := serie['metadata']['title']):
            serie_name = serie['name']
        serie_url = None

        if not serie['metadata']['status'] in env.status_to_update:
            continue

        # Get the bedetheque link if it exists
        for link in serie['metadata']['links']:
            if link['label'].lower() == "www.bedetheque.com":
                serie_url = link['url']
                break
        if serie_url is None:
            serie_url = find_series_url(serie_name, proxy = proxy, wait_delay = env.wait_delay)

        #get the metadata for the series from bedetheque
        if serie_url is None:
            logger.warning("No URL found for %s, skipping metadata refresh for this serie", serie_name)
            refresh_book_metadata(komga, serie_id, serie_url, proxy = proxy, wait_delay = env.wait_delay)
            continue
        bedetheque_metadata = get_comic_series_metadata(serie_url, proxy = proxy, wait_delay = env.wait_delay)

        #checking we have no issue with the metadata
        if bedetheque_metadata is None:
            logger.warning("Incorrect URL found for %s, trying to look for the URL", serie_name)
            serie_url = find_series_url(serie_name, proxy = proxy, wait_delay = env.wait_delay)
            if serie_url is None:
                logger.warning("No URL found for %s, skipping metadata refresh for this serie", serie_name)
                refresh_book_metadata(komga, serie_id, serie_url, proxy = proxy, wait_delay = env.wait_delay)
                continue
            bedetheque_metadata = get_comic_series_metadata(serie_url, proxy = proxy, wait_delay = env.wait_delay)
            if bedetheque_metadata is None:
                logger.error("Error while parsing URL %s found for %s, skipping metadata refresh for this serie", serie_url, serie_name)
                refresh_book_metadata(komga, serie_id, serie_url, proxy = proxy, wait_delay = env.wait_delay)
                continue

        # Prepare the metadata
        processedMetadata = processMetadata.prepareKomgaSeriesMetadata(
            bedetheque_metadata, serie['metadata'], serie_url)

        if processedMetadata.isvalid is False:
            logger.warning("Failed to update series %s", serie_name)
            continue

        serie_data = {
            "status": processedMetadata.status,
            "summary": processedMetadata.summary,
            "publisher": processedMetadata.publisher,
            "genres": processedMetadata.genres,
            "title": processedMetadata.title,
            "links": processedMetadata.links,
            "totalBookCount": processedMetadata.totalBookCount
        }

        # Update the metadata for the series on komga
        if komga.update_series_metadata(serie_id, serie_data):
            logger.info("Successfully update series %s", serie_name)
        else:
            logger.warning("Failed to update series %s", serie_name)
            continue

        # call the refresh on the books of this serie
        if not env.series_only:
            refresh_book_metadata(komga, serie_id, serie_url, proxy = proxy, wait_delay = env.wait_delay)
    logger.info("Refresh successfully terminated")


def refresh_book_metadata(komga, series_id, serie_url, proxy = None, wait_delay = None):
    '''
    Refresh Book Metadata
    '''
    # Get all books in the series on komga
    all_books = komga.get_series_books(series_id)

    # Loop through each book in the series on komga
    for book in all_books['content']:
        book_id = book['id']
        if not (book_name := book['metadata']['title']):
            book_name = book['name']
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
        if komga.update_book_metadata(book_id, book_data):
            logger.info("Successfully update book %s", book_name)
        else:
            logger.warning("Failed to update book %s", book_name)
            break

refresh_metadata()
