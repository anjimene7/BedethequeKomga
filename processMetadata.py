# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# Description: Handles komga bd metadata
# ------------------------------------------------------------------


from komgaApi import seriesMetadata, bookMetadata


def __setGenres(preparedKomgaMetadata, bedetheque_metadata, komga_metadata):
    if not komga_metadata['genresLock']:
        preparedKomgaMetadata.genres = bedetheque_metadata['genres']
    else:
        preparedKomgaMetadata.genres = komga_metadata['genres']


def __setStatus(preparedKomgaMetadata, bedetheque_metadata, komga_metadata):
    if not komga_metadata['statusLock']:
        runningLang = ["Série en cours"]
        abandonedLang = ["Série abandonnée"]
        endedLang = ["Série finie"]
        suspendedLang = ['Série suspendue']

        status = "ONGOING"

        if bedetheque_metadata["status"].strip() in runningLang:
            status = "ONGOING"
        elif bedetheque_metadata["status"].strip() in abandonedLang:
            status = "ABANDONED"
        elif bedetheque_metadata["status"].strip() in endedLang:
            status = "ENDED"
        elif bedetheque_metadata["status"].strip() in suspendedLang:
            status = "HIATUS"

        preparedKomgaMetadata.status = status
    else:
        preparedKomgaMetadata.status = komga_metadata['status']

def __prepareAuthors(authors, bedetheque_author, role):
    for author in authors:
        if author['role'] == role:
            authors.remove(author)
    bedetheque_author.reverse()
    author = ''
    for bedetheque_author_split in bedetheque_author:
        author += bedetheque_author_split.strip() + ' '
    authors.append({"name": author.strip(), "role": role})
    return authors

def __setAuthors(preparedKomgaMetadata, bedetheque_metadata, komga_metadata):
    '''
    basic format = {'name':'value','role':'role type'}
    The role types are:
        writer
        inker
        translator
        editor
        cover
        letterer
        colorist
        penciller
        Custom role type value
    '''
    if not komga_metadata['authorsLock']:
        authors = komga_metadata['authors'].copy()

        for scenario in bedetheque_metadata["scenarios"]:
            authors = __prepareAuthors(authors, scenario, "writer")
        for penciller in bedetheque_metadata["dessins"]:
            authors = __prepareAuthors(authors, penciller, "penciller")
        for colorist in bedetheque_metadata["couleurs"]:
            authors = __prepareAuthors(authors, colorist, "colorist")
        for cover in bedetheque_metadata["couvertures"]:
            authors = __prepareAuthors(authors, cover, "cover")
        for letterer in bedetheque_metadata["lettrages"]:
            authors = __prepareAuthors(authors, letterer, "letterer")

        preparedKomgaMetadata.authors = authors
    else:
        preparedKomgaMetadata.authors = komga_metadata['authors']

def __setTotalBookCount(preparedKomgaMetadata, bedetheque_metadata, komga_metadata):
    if not komga_metadata['totalBookCountLock']:
        preparedKomgaMetadata.totalBookCount = bedetheque_metadata['totalBookCount']
    else:
        preparedKomgaMetadata.totalBookCount = komga_metadata['totalBookCount']

def __setBookNumber(preparedKomgaMetadata, bedetheque_metadata, komga_metadata):
    if not komga_metadata['numberLock']:
        preparedKomgaMetadata.number = bedetheque_metadata['booknumber']
    else:
        preparedKomgaMetadata.number = komga_metadata['number']
    # if not komga_metadata['numberSortLock']:
    #     preparedKomgaMetadata.numberSort = bedetheque_metadata['booknumber'] // TODO: verify if used on bedetheque, otherwise just uncomment
    # else:
    #     preparedKomgaMetadata.numberSort = komga_metadata['numberSort']

def __setPublisher(preparedKomgaMetadata, bedetheque_metadata, komga_metadata):
    if not komga_metadata['publisherLock']:
        preparedKomgaMetadata.publisher = bedetheque_metadata['publisher']
    else:
        preparedKomgaMetadata.publisher = komga_metadata['publisher']


def __setTitle(preparedKomgaMetadata, bedetheque_metadata, komga_metadata):
    if not komga_metadata['titleLock']:
        preparedKomgaMetadata.title = bedetheque_metadata["title"]
    else:
        preparedKomgaMetadata.title = komga_metadata['title']


def __setSummary(preparedKomgaMetadata, bedetheque_metadata, komga_metadata):
    if not komga_metadata['summaryLock']:
        preparedKomgaMetadata.summary = bedetheque_metadata["summary"]
    else:
        preparedKomgaMetadata.summary = komga_metadata['summary']

def __setISBN(preparedKomgaMetadata, bedetheque_metadata, komga_metadata):
    if not komga_metadata['isbnLock']:
        preparedKomgaMetadata.isbn = bedetheque_metadata["isbn"]
    else:
        preparedKomgaMetadata.isbn = komga_metadata['isbn']

def __setReleaseDate(preparedKomgaMetadata, bedetheque_metadata, komga_metadata):
    if not komga_metadata['releaseDateLock']:
        preparedKomgaMetadata.releaseDate = bedetheque_metadata["releaseDate"]
    else:
        preparedKomgaMetadata.releaseDate = komga_metadata['releaseDate']


def __setLinks(preparedKomgaMetadata, url, komga_metadata):
    if not komga_metadata['linksLock']:
        links = komga_metadata['links'].copy()
        for komgalink in komga_metadata['links']:
            if komgalink['label'] == "www.bedetheque.com":
                if komgalink['url'] != url:
                    links.remove(komgalink)
                else:
                    break
        else:
            links.append({"label": "www.bedetheque.com", "url": url})
        preparedKomgaMetadata.links = links
    else:
        preparedKomgaMetadata.links = komga_metadata['links']


def prepareKomgaSeriesMetadata(bedetheque_metadata, komga_metadata, serie_url):
    # init
    preparedKomgaSeriesMetadata = seriesMetadata()

    # link
    __setLinks(preparedKomgaSeriesMetadata, serie_url, komga_metadata)

    # summary
    __setSummary(preparedKomgaSeriesMetadata, bedetheque_metadata, komga_metadata)

    # status
    __setStatus(preparedKomgaSeriesMetadata, bedetheque_metadata, komga_metadata)

    # genres
    __setGenres(preparedKomgaSeriesMetadata, bedetheque_metadata, komga_metadata)

    # totalBookCount
    __setTotalBookCount(preparedKomgaSeriesMetadata, bedetheque_metadata, komga_metadata)

    # publisher
    __setPublisher(preparedKomgaSeriesMetadata, bedetheque_metadata, komga_metadata)

    # title
    __setTitle(preparedKomgaSeriesMetadata, bedetheque_metadata, komga_metadata)

    preparedKomgaSeriesMetadata.isvalid = True
    return preparedKomgaSeriesMetadata


def prepareKomgaBookMetadata(bedetheque_metadata, komga_metadata, book_url):
    preparedKomgaBooksMetadata = bookMetadata()

    # title
    __setTitle(preparedKomgaBooksMetadata, bedetheque_metadata, komga_metadata)

    # link
    __setLinks(preparedKomgaBooksMetadata, book_url, komga_metadata)

    # booknumber
    __setBookNumber(preparedKomgaBooksMetadata, bedetheque_metadata, komga_metadata)

    # summary
    __setSummary(preparedKomgaBooksMetadata, bedetheque_metadata, komga_metadata)

    # authors
    __setAuthors(preparedKomgaBooksMetadata, bedetheque_metadata, komga_metadata)

    # releaseDate
    __setReleaseDate(preparedKomgaBooksMetadata, bedetheque_metadata, komga_metadata)

    # isbn
    __setISBN(preparedKomgaBooksMetadata, bedetheque_metadata, komga_metadata)

    preparedKomgaBooksMetadata.isvalid = True
    return preparedKomgaBooksMetadata
