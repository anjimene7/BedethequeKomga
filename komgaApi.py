# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# Description: Komga API(https://github.com/gotson/komga/blob/master/komga/docs/openapi.json)
# ------------------------------------------------------------------


import requests


class KomgaApi:
    def __init__(self, base_url, username, password):
        # store the base URL and authentication information for use in other methods
        self.base_url = base_url + '/api/v1'
        self.auth = (username, password)

    def get_all_series(self, parameters=None):
        '''
        Retrieves all series in the komga comic.

        https://github.com/gotson/komga/blob/master/komga/docs/openapi.json#L4859
        '''
        url = f'{self.base_url}/series'
        if parameters:
            url += f'?{parameters}&size=50000'
        else:
            url += '?size=50000'
        # make a GET request to the URL to retrieve all series
        response = requests.get(url, auth=self.auth)
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
        response = requests.get(
            f'{self.base_url}/readlists/{readlist_id}', auth=self.auth)
        # return the response as a JSON object
        return response.json()

    def get_series_books(self, series_id):
        '''
        Retrieves all books in a specified series in the komga comic.

        https://github.com/gotson/komga/blob/master/komga/docs/openapi.json#L5373
        '''
        # make a GET request to the URL to retrieve all books in a given series
        response = requests.get(
            f'{self.base_url}/series/{series_id}/books?size=50000', auth=self.auth)
        # return the response as a JSON object
        return response.json()

    def update_series_metadata(self, series_id, metadata):
        '''
        Updates the metadata of a specified comic series.
        '''
        # make a PATCH request to the URL to update the metadata for a given series
        response = requests.patch(
            f'{self.base_url}/series/{series_id}/metadata', auth=self.auth, json=metadata)
        # return True if the status code indicates success, False otherwise
        return response.status_code == 204

    def update_book_metadata(self, book_id, metadata):
        '''
        Updates the metadata of a specified comic book.

        https://github.com/gotson/komga/blob/master/komga/docs/openapi.json#L2935
        '''
        # make a PATCH request to the URL to update the metadata for a given book
        response = requests.patch(
            f'{self.base_url}/books/{book_id}/metadata', auth=self.auth, json=metadata)
        # return True if the status code indicates success, False otherwise
        return response.status_code == 204


class seriesMetadata:
    '''
    Class to represent Komga series metadata fields. 

    See https://github.com/gotson/komga/blob/master/komga/docs/openapi.json#L10449 for fields. 
    '''

    def __init__(self):
        self.title = ""
        self.status = ""  # 状态
        self.summary = ""  # 概要
        self.publisher = ""  # 出版商
        self.genres = "[]"  # 流派
        self.tags = "[]"    # 标签
        self.alternateTitles = "[]"  # 别名
        self.ageRating = 12  # 分级
        self.links = "[]"  # 链接
        self.totalBookCount = 1  # must be greater than 0

        self.isvalid = False


class bookMetadata:
    '''
    Class to represent Komga book metadata fields.
    '''

    def __init__(self):
        self.title = ""
        self.summary = ""
        self.number = 0  # 序号
        self.isbn = ""
        self.authors = "[]"  # 作者
        self.tags = "[]"    # 标签
        self.releaseDate = None  # 发布日期
        self.links = "[]"  # 链接
        self.numberSort = 0  # 短序号

        self.isvalid = False
