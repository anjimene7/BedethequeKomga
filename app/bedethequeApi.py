import re
import os
import requests
import time
from bs4 import BeautifulSoup
from log import logger
import logging
from fuzzywuzzy import fuzz, process
from typing import Optional
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyisbn
logging.getLogger("pyppeteer.launcher").disabled = True

def find_best_url_match(comic_series_name, proxy, wait_delay):
    #comic_series_name = re.sub('((An\s+([0-9]+\s+[-:]+\s+)+)|(Explora - ))', '', comic_series_name, flags=re.IGNORECASE)
    all_results = []
    elements = comic_series_name.split(' ')
    counter = 0
    while counter <= len(elements) - 1:
        if len(elements[counter]) <= 2:
            counter += 1
            continue
        series_to_find = remove_accents(elements[counter])
        counter += 1
        searchurl = f'https://www.bedetheque.com/bandes_dessinees_{series_to_find.lower()}.html'
        logger.info(f"Will search for {searchurl}")
        soup = get_soup(searchurl, proxy = proxy, wait_delay = wait_delay)
        list_results = soup.find("div", class_="widget-magazine")
        if list_results:
            results = []
            for result in list_results.find_all("li"):
                series_title = result.find("a").text.strip()
                series_title_without_parenthesis = re.sub(' \([a-z0-9_\-/]+\)', '', series_title, flags=re.IGNORECASE)
                series_url = result.find("a")["href"]
                series_ratio = fuzz.ratio(comic_series_name, series_title_without_parenthesis)
                results.append({"title": series_title, "url": series_url, "ratio": series_ratio})
            all_results.extend(results)
    return all_results

def find_series_url(comic_series_name, proxy = None, wait_delay = None) -> Optional[str]:
    url = None
    logger.info("No url in komga for serie %s, searching bedetheque by name", comic_series_name)
    if re.search('((les|le|la)\s+|(l\'))', comic_series_name, re.IGNORECASE):
        comic_series_name = re.sub('((les|le|la)\s+|(l\'))', '', comic_series_name, flags=re.IGNORECASE)
    all_matches_url = find_best_url_match(comic_series_name, proxy, wait_delay)
    all_matches_url = sorted(all_matches_url, key=lambda x: x['ratio'], reverse=True)
    logger.debug(all_matches_url)
    perfect_matches = list(filter(lambda x: x['ratio']==100, all_matches_url))
    idx_choice = 0
    if len(perfect_matches) > 1:
        logger.warning(f"There are more than 1 perfect matches for {comic_series_name}: {perfect_matches}")
        all_matches_url = []
        #idx_choice = int(input("Please select which one to keep (0-indexed)"))
    if all_matches_url:
        result = all_matches_url[idx_choice]
        if result:
            if result['ratio'] < 80:
                logger.warning(f"Match has a score <90 ({result['ratio']}). PLease double check -> {comic_series_name} : {result['title']}")
                #url = input('Please input URL of series: ')
                url = None
            else:
                url = result['url']
        ratio = result['ratio']
    else:
        #url = input('Could not find series, please input url: ')
        url = None
        ratio = 100

    if not url:
        logger.info("No serie link found for " + comic_series_name)
        return None
    else:
        logger.info(f"Url found (series) (score: {ratio}) for {comic_series_name}, {url}")
    return url

def find_comic_url(comic_name, comic_booknumber, serie_url, proxy = None, wait_delay = None) -> Optional[str]:
    logger.info("No url in komga for tome %s, searching bedetheque by name", comic_name)
    soup = get_soup(serie_url, proxy = proxy, wait_delay = wait_delay)
    if albums := soup.find("div", class_="tab_content_liste_albums"):
        best_matches = process.extract(comic_name, [x.find("a").text.strip() for x in albums.find_all("li")], limit=20)
        if best_matches[0][1] < 90:
            logger.info(f"Best matches: ")
            for idx, xx in enumerate(best_matches):
                print(idx, xx)
            my_input = input(f"Select which 0-index album to get: ")
            if not my_input:
                logger.warning(f"Match was not kept")
                return None
            else:
                my_input = int(my_input)
            best_match = best_matches[my_input]
        else:
            best_match = best_matches[0]
        for album in albums.find_all("li"):
            if album.find("a").text.strip() == best_match[0]:
                url_to_return = album.find("a")["href"]
                logger.info(f"Url found (tome) (score: {best_match[1]}) %s: %s", comic_name, url_to_return)
                return url_to_return
        #for album in albums.find_all("li"):
        #    if int(float(album.find("label").text.strip().removesuffix(".").lower())) == int(float(comic_booknumber)):
        #        url_to_return = album.find("a")["href"]
        #        logger.info("Url found (tome) %s: %s", comic_name, url_to_return)
        #        return url_to_return
    if not (block := soup.find("div", class_="album-main")):
        logger.warning("No serie found from bedetheque for %s from url %s", comic_name, serie_url)
        return None
    if not (block_title := block.find("a", class_="titre")):
        logger.warning("No serie found from bedetheque for %s from url %s", comic_name, serie_url)
        return None
    logger.info("Url found (tome) %s, %s", comic_name, block_title["href"])
    return block_title["href"]

def get_number_of_albums(soup:BeautifulSoup) -> int:
    total_book_number = 0
    if False: #albums := soup.find("div", class_="tab_content_liste_albums"):
        for album in albums.find_all("li"):
            if album.find("label").text.strip().removesuffix(".").isdigit():
                total_book_number += 1
    else:
        total_book_number = soup.find("div", class_="bandeau-info serie").find("i", class_="icon-book").parent.text.strip(' albums')
    return total_book_number

def get_soup(url: str, proxy = None, wait_delay = None) -> BeautifulSoup:
    page = None
    session = HTMLSession()
    session.cookies.update(
        {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Host": "www.bedetheque.com",
            "Referer": "https://www.bedetheque.com/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0",
        }
    )
    if proxy is not None:
        currentProxy = proxy.getNextProxy()
        while True:
            try:
                if not currentProxy and proxy:
                    proxy.refreshProxies()
                    time.sleep(30)
                    currentProxy = proxy.getNextProxy()
                    #chooseToContinue = input("Failed to get page with the proxies. Do you want to try without using a proxy (risk of ban from bedetheque) (Y/N): ")
                    #if chooseToContinue.lower() == 'y':
                    #    logger.warning("Continuing without a proxy")
                    #else:
                    #    logger.error("Choose to not continue without a proxy. Exiting")
                    #    exit()
                page = session.get(url, proxies=currentProxy, timeout=15)
                break
            except requests.exceptions.RequestException as e:
                logger.warning("Failed to get page with the current proxy : %s, removing it and trying with the next one", currentProxy)
                currentProxy = proxy.removeProxyAndGetNew(currentProxy)
    else:
        try:
            page = session.get(url, timeout=15)
        except requests.exceptions.RequestException as e:
            logger.warning("Failed to get page, continuing to the next one")
        if wait_delay:
            time.sleep(wait_delay)
    if page is None:
        return BeautifulSoup("", "html.parser")
    page.html.render(timeout=20)
    session.close()
    return BeautifulSoup(page.html.raw_html, "html.parser")

def remove_accents(comic_series_name) -> str:
    for pattern, replacement in [
        ("[àáâãäåâÀÁÂÄÅÃÂ]", "a"),
        ("[èéêëÉÈÊË]", "e"),
        ("[çÇ]", "c"),
        ("[ìíîïÍÌÎÏ]", "i"),
        ("[òóôõöÓÒÔÖÕ]", "o"),
        ("[ùúûüÚÙÛÜ]", "u"),
        ("[œŒ]", "oe"),
    ]:
        comic_series_name = re.sub(pattern, replacement, comic_series_name)
    return comic_series_name

# Python code to check if a given ISBN is valid or not.
def isValidISBN(isbn):
    isbn = isbn.replace('-', '').replace(' ', '')
    if isbn.isdigit():
        isbn_object = pyisbn.Isbn(isbn)
        if len (isbn_object.isbn) == 10:
            final_isbn = isbn_object.convert(code='978')
        else:
            final_isbn = isbn_object.isbn
        return final_isbn
    else:
        return False

def get_comic_series_metadata(url: str, proxy = None, wait_delay = None):
    soup = get_soup(url, proxy = proxy, wait_delay = wait_delay)
    if not soup.find("div", class_="bandeau-info serie"):
        logger.error("Error reading url %s", url)
        return None
    title = soup.find("div", class_="bandeau-info serie").h1.text.strip()
    status = soup.find("div", class_="bandeau-info serie").find("i", class_="icon-info-sign").parent.text.strip()
    totalBookCount = get_number_of_albums(soup)
    publisher = soup.find("label", string="Editeur : ")
    if publisher:
        publisher = publisher.next_sibling.text.strip()
    related_series = soup.find("div", class_="tab_content serie-liee")
    related_series_results = {}
    if related_series:
        for result in related_series.find_all("li"):
            related_series_title = result.find("a")["title"]
            related_series_url = result.find("a")["href"]
            related_series_results.update({related_series_title: related_series_url})
    if soup.find("label", string="Collection : ") and len(soup.findAll("label", string="Collection : ")) == totalBookCount:
        collection = soup.find("label", string="Collection : ").next_sibling.text.strip().title()
    else:
        collection = None
    if soup.find("div", class_="bandeau-info serie").find("span", class_="style"):
        genres = soup.find("div", class_="bandeau-info serie").find("span", class_="style").text.split(", ")
    else:
        genres = None
    summary = soup.find("div", class_="bandeau-boutons-serie").previous_sibling.previous_sibling.text.strip()
    metadata = {
        "title": title,
        "status": status,
        "totalBookCount": totalBookCount,
        "publisher": publisher,
        "genres": genres,
        "summary": summary,
        "url": url,
        "collection": collection,
        "related_series": related_series_results
    }
    return metadata

def get_comic_book_url_from_isbn(driver, comic_isbn: str, proxy = None, wait_delay = None) -> Optional[str]:
    webdriver.DesiredCapabilities.CHROME['proxy'] = {
        "httpProxy": proxy,
        "ftpProxy": proxy,
        "sslProxy": proxy,
        "noProxy": None,
        "proxyType": "MANUAL",
        "class": "org.openqa.selenium.Proxy",
        "autodetect": False
    }
    url = f"https://www.bedetheque.com/search/albums?RechISBN={comic_isbn}"
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[8]/div[2]/div[2]/div[1]/div/div/div[2]/div[1]/div/form/div[5]/input')))
    element.click()
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    list_results = soup.find("div", class_="widget-magazine")
    results = []
    if list_results:
        for result in list_results.find_all("li"):
            comic_url = result.find("a")["href"]
            results.append(comic_url)
    if not results:
        return None
    if len(results) > 1:
        logger.warning(f"Found more than 1 URL for the requested ISBN ({comic_isbn}) : {results}")
    return results[0]


def get_comic_book_metadata(comic_url: str, proxy = None, wait_delay = None):
    title = ''
    isbn = ''
    releaseDate = ''
    booknumber = 0
    metadata = None
    couleurs = []
    dessins = []
    scenarios = []
    lettrages = []
    couvertures = []

    soup = get_soup(comic_url, proxy = proxy, wait_delay = wait_delay)
    if not soup.find("meta", attrs={'name': 'description'}):
        logger.error("Error reading url %s", comic_url)
        return None
    summary = soup.find("meta", attrs={'name': 'description'})['content'].strip().replace("\n", " ")

    if not (content := soup.find("div", class_="tab_content_liste_albums")):
        return None
    infos = content.find_all("li")
    for info in infos:
        if not (block := info.find("label")):
            continue

        match block.text.strip():
            case "Titre :" as key:
                title = info.text.removeprefix(key).strip()
            case "Tome :" as key:
                booknumber = info.text.removeprefix(key).strip()
            case "Scénario :" as key:
                scenarios.append(info.text.strip().removeprefix(key).strip("\r\n ").split(','))
                while ((next_block := info.find_next_sibling("li"))
                    and next_block.find("label")
                    and not next_block.find("label").text.strip()):
                    scenarios.append(next_block.text.strip().removeprefix(key).strip("\r\n ").split(','))
                    info = next_block
            case "Dessin :" as key:
                dessins.append(info.text.strip().removeprefix(key).strip("\r\n ").split(','))
                while ((next_block := info.find_next_sibling("li"))
                    and next_block.find("label")
                    and not next_block.find("label").text.strip()):
                    dessins.append(next_block.text.strip().removeprefix(key).strip("\r\n ").split(','))
                    info = next_block
            case "Couleurs :" as key:
                couleurs.append(info.text.strip().removeprefix(key).strip("\r\n ").split(','))
                while ((next_block := info.find_next_sibling("li"))
                    and next_block.find("label")
                    and not next_block.find("label").text.strip()):
                    couleurs.append(next_block.text.strip().removeprefix(key).strip("\r\n ").split(','))
                    info = next_block
            case "Lettrage :" as key:
                lettrages.append(info.text.strip().removeprefix(key).strip("\r\n ").split(','))
                while ((next_block := info.find_next_sibling("li"))
                    and next_block.find("label")
                    and not next_block.find("label").text.strip()):
                    lettrages.append(next_block.text.strip().removeprefix(key).strip("\r\n ").split(','))
                    info = next_block
            case "Couverture :" as key:
                couvertures.append(info.text.strip().removeprefix(key).strip("\r\n ").split(','))
                while ((next_block := info.find_next_sibling("li"))
                    and next_block.find("label")
                    and not next_block.find("label").text.strip()):
                    couvertures.append(next_block.text.strip().removeprefix(key).strip("\r\n ").split(','))
                    info = next_block
            case "Dépot légal :" as key:
                release_date_pattern = re.compile(
                    r"\(Parution le (?P<day>\d+)/(?P<month>\d+)/(?P<year>\d+)\)"
                )
                if (block := info.find("span")) and (
                    match := release_date_pattern.search(info.text.strip())):
                    releaseDate = match.group("year") + "-" + match.group("month") + "-" + match.group("day")
                else:
                    releaseDate = ''
            case "EAN/ISBN :" as key:
                output_isbn = isValidISBN(info.text.removeprefix(key).strip())
                if not output_isbn:
                    isbn = ''
                else:
                    isbn = output_isbn

    metadata = {
        "title": title,
        "booknumber": booknumber,
        "summary": summary,
        "scenarios": scenarios,
        "dessins": dessins,
        "couleurs": couleurs,
        "lettrages": lettrages,
        "couvertures": couvertures,
        "url": comic_url,
        "isbn": isbn,
        "releaseDate": releaseDate
    }
    return metadata

class bedethequeApiProxies:
    '''
    Class to represent the proxy settings.
    '''
    def __init__(self):
        self.refreshProxies()

    def refreshProxies(self):
        self.proxyIndex = 0
        self.proxies = []
        with open(f'{os.path.dirname(os.path.realpath(__file__))}/proxies_list.txt', 'r') as f:
            for line in f.readlines():
                ip = line.split(';')[0].strip()
                pp = line.split(';')[1].strip()
                self.proxies.append({pp: ip})

    def getNextProxy(self):
        if len(self.proxies) == self.proxyIndex:
            self.proxyIndex = 0
        if len(self.proxies)==0:
            return None
        proxy = self.proxies[self.proxyIndex]
        self.proxyIndex += 1
        if self.proxyIndex == len(self.proxies):
            self.proxyIndex = 0
        return proxy

    def removeProxyAndGetNew(self, proxy):
        logger.warning("proxy %s dooesn't work, removing it and trying the next one", proxy)
        self.proxies.remove(proxy)
        if len(self.proxies) == self.proxyIndex:
            return self.getNextProxy()
        return self.proxies[self.proxyIndex]
