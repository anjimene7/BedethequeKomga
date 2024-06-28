# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# Description: Komga API(https://github.com/gotson/komga/blob/master/komga/docs/openapi.json)
# ------------------------------------------------------------------
import os.path

import requests
import pytesseract
from archivefile import ArchiveFile
from PIL import Image
import re
from log import logger
import cv2
from pyzbar.pyzbar import decode
from typing import Optional

class KomgaApi:
    def __init__(self, base_url, username, password):
        # store the base URL and authentication information for use in other methods
        if base_url[-1] == '/':
            base_url = base_url[:-1]
        self.base_url = base_url + '/api/v1'
        self.auth = (username, password)

    def get_all_series(self, parameters=None, serie_id = None):
        '''
        Retrieves all series in the komga comic.

        https://github.com/gotson/komga/blob/master/komga/docs/openapi.json#L4859
        '''
        url = f'{self.base_url}/series'
        if serie_id is not None:
            url += f'/{serie_id}'
        if parameters:
            url += f'?{parameters}&size=50000'
        else:
            url += '?size=50000'
        # make a GET request to the URL to retrieve all series
        response = requests.get(url, auth=self.auth, timeout=15)
        # return the response as a JSON object
        return response.json()

    def get_all_collections(self, id=None):
        url = f'{self.base_url}/collections'
        if id:
            url += f'/{id}'
        url += '?size=50000'
        response = requests.get(url, auth=self.auth, timeout=15)
        # return the response as a JSON object
        return response.json()

    def get_series_with_libaryid(self, library_id):
        '''
        Retrieves all series in a specified library in the komga comic.

        https://github.com/gotson/komga/blob/master/komga/docs/openapi.json#L4875
        '''
        return self.get_all_series(f'library_id={library_id}')

    def get_series_with_collection(self, collection_id):
        '''
        Retrieves all series with a specified collection in the komga comic.
        '''
        return self.get_all_series(f'collection_id={collection_id}')

    def get_serie_with_serieid(self, serie_id):
        '''
        Retrieves the serie with a specified serie id in the komga comic.
        '''
        return self.get_all_series(serie_id = serie_id)

    def get_series_with_read_status(self, read_status):
        '''
        Retrieves all series with a specified read status in the komga comic.

        Status options: "UNREAD", "READ", "IN_PROGRESS"
        '''
        return self.get_all_series(f'read_status={read_status}')

    def get_series_with_readlist(self, readlist_id):
        '''
        Retrieves all series with a specified readlist in the komga comic.
        '''
        response = requests.get(f'{self.base_url}/readlists/{readlist_id}', auth=self.auth, timeout=15)
        # return the response as a JSON object
        return response.json()

    def get_series_links_bedetheque(self) -> dict[str, str]:
        all_series = self.get_all_series()['content']
        all_series_links = {}
        for x in all_series:
            for l in x['metadata']['links']:
                if l['label'].lower() == 'www.bedetheque.com':
                    url = l['url']
                    all_series_links.update({x['id']: url})
        return all_series_links

    def get_series_books(self, series_id):
        '''
        Retrieves all books in a specified series in the komga comic.

        https://github.com/gotson/komga/blob/master/komga/docs/openapi.json#L5373
        '''
        # make a GET request to the URL to retrieve all books in a given series
        response = requests.get(
            f'{self.base_url}/series/{series_id}/books?size=50000', auth=self.auth, timeout=15)
        # return the response as a JSON object
        return response.json()

    def get_serie_collection(self, series_id):
        response = requests.get(f'{self.base_url}/series/{series_id}/collections', auth=self.auth, timeout=15)
        # return the response as a JSON object
        return response.json()

    def create_collection(self, name, id):
        metadata = {"name": name,
                    "ordered": False,
                    "seriesIds": [id]
                    }
        response = requests.post(f'{self.base_url}/collections', auth=self.auth, timeout=15, json=metadata)
        # return the response as a JSON object
        if response.status_code == 200:
            return response.json()['id']
        else:
            return None

    def get_or_create_collection(self, name, id) -> Optional[str]:
        existing_collections = self.get_all_collections()['content']
        existing_collection_id = None
        for x in existing_collections:
            if x['name'].lower() == name.lower():
                existing_collection_id = x['id']
        if existing_collection_id:
            return existing_collection_id
        else:
            logger.info(f"Creating collection {name}")
            return self.create_collection(name, id)

    def add_serie_to_collection(self, serie_id, collection_id, dry_run=True):
        url = f'{self.base_url}/collections/{collection_id}'
        metadata_full = self.get_all_collections(collection_id)
        if metadata_full and "seriesIds" in metadata_full and serie_id in metadata_full["seriesIds"]:
            logger.info(f"Series already part of {metadata_full['name']}")
        else:
            metadata_full["seriesIds"].append(serie_id)

        if dry_run:
            return True
        else:
            metadata = {key: metadata_full[key] for key in metadata_full.keys() & {'name', 'ordered', 'seriesIds'}}
            response = requests.patch(url, auth=self.auth, json=metadata, timeout=15)
        # return True if the status code indicates success, False otherwise
        return response.status_code == 204

    def update_collections_metadata(self, serie_id, bedetheque_metadata, dry_run=True):
        if bedetheque_metadata["status"].lower() == "one shot":
            collection_id = self.get_or_create_collection("Oneshot", serie_id)
            logger.info(f"Adding oneshot {serie_id} to collection {collection_id}")
            self.add_serie_to_collection(serie_id, collection_id, dry_run)
        if bedetheque_metadata['collection']:
            collection_id = self.get_or_create_collection(bedetheque_metadata['collection'], serie_id)
            if not collection_id:
                logger.warning(f"Could not create collection for {bedetheque_metadata['collection']}")
                return False
            logger.info(f"Adding {serie_id} to collection {collection_id}")
            self.add_serie_to_collection(serie_id, collection_id, dry_run)
        elif bedetheque_metadata['related_series']:
            series = self.get_series_links_bedetheque()
            collections = self.get_all_collections()['content']
            which_collection = {}
            # Is series already in an existing collection?
            for col in collections:
                if serie_id in col['seriesIds']:
                    which_collection.update({col['id']: col['name']})
            if not which_collection:
                for rel_ser_name, rel_ser_url in bedetheque_metadata['related_series'].items():
                    rel_ser_id = [k for k, v in series.items() if v == rel_ser_url]
                    if rel_ser_id:
                        rel_collections = self.get_serie_collection(rel_ser_id[0])
                        if rel_collections:
                            which_collection.update({rel_collections[0]['id']: rel_collections[0]['name']})

            if not which_collection:
                #new_collection_name = input(f"Related series found for {bedetheque_metadata['url']}, please name the collection: ")
                #if not new_collection_name:
                #    return True
                return True
            else:
                new_collection_name = list(which_collection.values())[0]
            collection_id = self.get_or_create_collection(new_collection_name, serie_id)
            if not collection_id:
                logger.warning(f"Could not create collection for {new_collection_name}")
                return False
            logger.info(f"Adding {bedetheque_metadata['title']} to collection {new_collection_name}")
            self.add_serie_to_collection(serie_id, collection_id, dry_run)
        else:
            return True

    def update_series_metadata(self, series_id, metadata, dry_run=True):
        '''
        Updates the metadata of a specified comic series.
        '''
        # make a PATCH request to the URL to update the metadata for a given series
        url = f'{self.base_url}/series/{series_id}/metadata'
        if dry_run:
            self.write_to_file(metadata['title'], [x['url'] for x in metadata['links'] if x['label'] == 'www.bedetheque.com'][0], series_id)
            return True
        else:
            response = requests.patch(url, auth=self.auth, json=metadata, timeout=15)
        # return True if the status code indicates success, False otherwise
        return response.status_code == 204

    def update_book_metadata(self, book_id, metadata, dry_run=True):
        '''
        Updates the metadata of a specified comic book.

        https://github.com/gotson/komga/blob/master/komga/docs/openapi.json#L2935
        '''
        # make a PATCH request to the URL to update the metadata for a given book
        url = f'{self.base_url}/books/{book_id}/metadata'
        if dry_run:
            return True
        else:
            response = requests.patch(url, auth=self.auth, json=metadata, timeout=15)
        # return True if the status code indicates success, False otherwise
        return response.status_code == 204

    def get_isbn_from_book(self, book_id, tmpdirname) -> dict:
        '''
        Extracts the file to analyze it and fetch isbn
        '''
        isbn_regex = '(?P<isbn>(978.*|2.*))'
        results = []
        barcode = None
        url = f'{self.base_url}/books/{book_id}'
        response = requests.get(url, auth=self.auth, timeout=15)
        if response.status_code == 200:
            path = response.json().get('url')
            path = path.replace('/data', '/media/data_storage/Reading/Comics/curated')
        else:
            return results
        if os.path.exists(path):
            with ArchiveFile(path) as archive:
                archive.extractall(destination=tmpdirname)
                for dirpath, _, files in os.walk(tmpdirname):
                    files_slices = sorted(files)[-5:] + sorted(files)[:5]
                    for file in files_slices:
                        if file.endswith(('.jpg', '.jpeg', '.png')) and os.path.getsize(os.path.join(dirpath, file)) > 0:
                            logger.debug(f"Processing {file}")
                            img = cv2.imread(os.path.join(dirpath, file))
                            detected_img = decode(img)
                            if detected_img:
                                if len(detected_img) > 1:
                                    logger.warning(f"More than 1 barcode found! Keeping first one")
                                barcode = detected_img[0].data.decode('utf-8')
                                break
                            text_output = pytesseract.image_to_string(Image.open(os.path.join(dirpath, file)))
                            regex_search = re.search(isbn_regex, text_output, flags=re.IGNORECASE)
                            if regex_search:
                                logger.debug(f"Match found on page: {file}")
                                match = regex_search.group('isbn').strip()
                                logger.debug(f"Found a match: {match}")
                                match_cleaned = re.sub('[\s\-\.]+', '', match)
                                results.append(match_cleaned)
        # Refine results
        final_results = {'string_match': [], 'barcode': []}
        for r in results:
            r_search = re.search('.*([0-9]{10,13}).*', r)
            if r_search:
                final_results.setdefault('string_match', []).append(r_search.group(1))
        if barcode:
            final_results.setdefault('barcode', []).append(barcode)
        return final_results

    def delete_collections(self):
        collections = self.get_all_collections()['content']
        url = f'{self.base_url}/collections/'
        for col in collections:
            if len(col['seriesIds']) < 3:
                final_url = url + col['id']
                logger.info(f"Deleting {col['name']} collection as it has {len(col['seriesIds'])} < 4 elements")
                response = requests.delete(final_url, auth=self.auth, timeout=15)



    def write_to_file(self, metadata_title, url, series_id):
        with open(f'{os.path.dirname(os.path.realpath(__file__))}/id_series.csv', 'r+') as f:
            url = url
            title = self.get_serie_with_serieid(series_id)['name']
            line_to_write = f"{title}|{metadata_title}|{series_id}|{url}"
            for line in f:
                if line_to_write in line:
                    break
            else:  # not found, we are at the eof
                f.write(f"{line_to_write}\n")  # append missing data

class seriesMetadata:
    '''
    Class to represent Komga series metadata fields.

    See https://github.com/gotson/komga/blob/master/komga/docs/openapi.json#L10449 for fields.
    '''

    def __init__(self):
        self.title = ""
        self.status = ""
        self.summary = ""
        self.publisher = ""
        self.genres = "[]"
        self.links = "[]"
        self.totalBookCount = 1  # must be greater than 0

        self.isvalid = False


class bookMetadata:
    '''
    Class to represent Komga book metadata fields.
    '''

    def __init__(self):
        self.title = ""
        self.summary = ""
        self.number = 0
        # self.numberSort = 0
        self.authors = "[]"
        self.releaseDate = None
        self.links = "[]"
        self.isbn = ""

        self.isvalid = False
