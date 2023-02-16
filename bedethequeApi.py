import re
import requests
from bs4 import BeautifulSoup
from log import logger

def find_series_url(comic_series_name, proxy = None) -> str:
    url = None
    logger.info("No url in komga for serie %s, searching bedetheque by name", comic_series_name)
    if " " in comic_series_name:
        series_to_find = remove_accents(comic_series_name).split(" ")[0]
    else:
        series_to_find = remove_accents(comic_series_name)
    searchurl = f'https://www.bedetheque.com/bandes_dessinees_{series_to_find.lower()}.html'
    soup = get_soup(searchurl, proxy = proxy)
    list_results = soup.find("div", class_="widget-magazine")
    if not list_results:
        logger.warning("%s not found on bedetheque", comic_series_name)
        return None
    results = []
    for result in list_results.find_all("li"):
        results.append({"title": result.find("a").text.strip(), "url": result.find("a")["href"]})
    for result in results:
        if result['title'].lower() == comic_series_name.lower():
            url = result['url']
            logger.info("Url found for %s", comic_series_name)
    if not url:
        print("No serie link found for " + comic_series_name)
        print("Found those series :")
        for result in results:
            if result['title'].lower().startswith(comic_series_name.lower()):
                print(result['title'])
        comic_series_name = input("Choose a serie: ")
        if not comic_series_name:
            logger.warning("No serie chosen from bedetheque for %s", comic_series_name)
            return None
        for result in results:
            if result['title'].lower() == comic_series_name.lower():
                url = result['url']
                logger.info("Url found for %s", comic_series_name)
    return url

def find_comic_url(comic_name, comic_booknumber, serie_url, proxy = None) -> str:
    logger.info("No url in komga for tome %s, searching bedetheque by name", comic_name)
    soup = get_soup(serie_url, proxy = proxy)
    if albums := soup.find("div", class_="tab_content_liste_albums"):
        for album in albums.find_all("li"):
            if album.find("label").text.strip().removesuffix(".").lower() == comic_booknumber:
                logger.info("Url found for tome %s", comic_name)
                return album.find("a")["href"]
        for album in albums.find_all("li"):
            if album.find("a").text.strip() == comic_name:
                logger.info("Url found for tome %s", comic_name)
                return album.find("a")["href"]
    if not (block := soup.find("div", class_="album-main")):
        logger.warning("No serie found from bedetheque for %s from url %s", comic_name, serie_url)
        return None
    if not (block_title := block.find("a", class_="titre")):
        logger.warning("No serie found from bedetheque for %s from url %s", comic_name, serie_url)
        return None
    logger.info("Url found for tome %s", comic_name)
    return block_title["href"]

def get_soup(url: str, proxy = None) -> BeautifulSoup:
    session = requests.Session()
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
                page = session.get(url, proxies=currentProxy, timeout=5)
                break
            except requests.exceptions.RequestException():
                logger.warning("Failed to get page with the current proxy : %s, removing it and trying with the next one", currentProxy)
                currentProxy = proxy.removeProxyAndGetNew(currentProxy)
    else:
        logger.warning("Getting soup without proxy")
        page = session.get(url, timeout=5)
    return BeautifulSoup(page.content, "html.parser")

def remove_accents(comic_series_name) -> str:
    for pattern, replacement in [
        ("[àáâãäåÀÁÂÄÅÃ]", "a"),
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
    if len(isbn) != 13:
        return False
    product = (sum(int(ch) for ch in isbn[::2])
               + sum(int(ch) * 3 for ch in isbn[1::2]))
    return product % 10 == 0

def get_comic_series_metadata(url: str, proxy = None):
    metadata = None

    soup = soup = get_soup(url, proxy = proxy)
    title = soup.find("div", class_="bandeau-info serie").h1.text.strip()
    status = soup.find("div", class_="bandeau-info serie").find("i", class_="icon-info-sign").parent.text
    totalBookCount = soup.find("div", class_="bandeau-info serie").find("i", class_="icon-book").parent.text.strip(' albums')
    publisher = soup.find("label", string="Editeur : ").next_sibling.text
    genres = soup.find("div", class_="bandeau-info serie").find("span", class_="style").text.split(", ")
    summary = soup.find("div", class_="bandeau-boutons-serie").previous_sibling.previous_sibling.text
    metadata = {
        "title": title,
        "status": status,
        "totalBookCount": totalBookCount,
        "publisher": publisher,
        "genres": genres,
        "summary": summary,
        "url": url
    }
    return metadata

def get_comic_book_metadata(comic_url: str, proxy = None):
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

    soup = get_soup(comic_url, proxy = proxy)
    summary =  soup.find("meta", attrs={'name': 'description'})['content'].strip().replace("\n", " ")

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
                    match := release_date_pattern.match(info.text.strip())):
                    releaseDate = match.group("year") + "-" + match.group("month") + "-" + match.group("day")
                else:
                    releaseDate = ''
            case "EAN/ISBN :" as key:
                if not isValidISBN(isbn := info.text.removeprefix(key).strip()):
                    isbn = ''

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
        self.proxies = self.__get_proxies()
        self.proxyIndex = 0

    def __get_proxies(self):
        url = "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=$5000"
        try:
            response = requests.get(url, timeout=15)
        except requests.exceptions.RequestException():
            logger.warning("Failed to get page with the proxies")
            chooseToContinue = input("Failed to get page with the proxies. Do you want to try without using a proxy (risk of ban from bedetheque) (Y/N): ")
            if chooseToContinue == 'y' or chooseToContinue == 'Y':
                logger.warning("Continuing without a proxy")
                return None
            logger.error("Choose to not continue without a proxy. Exiting")
            exit()
        proxies = response.text.strip().split("\r\n")
        logger.info("proxys retrieved")
        return [{"http": "http://" + proxy} for proxy in proxies]

    def getNextProxy(self):
        proxy = self.proxies[self.proxyIndex]
        self.proxyIndex += 1
        if self.proxyIndex == len(self.proxies):
            self.proxyIndex = 0
        return proxy

    def removeProxyAndGetNew(self, proxy):
        logger.warning("proxy %s dooesn't work, removing it and trying the next one", proxy)
        self.proxies.remove(proxy)
        return self.proxies[self.proxyIndex]
