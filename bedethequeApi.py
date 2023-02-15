import requests
import re
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
        logger.warning("No serie found from bedetheque for %s from url %s", comic_series_name, serie_url)
        return None
    if not (block_title := block.find("a", class_="titre")):
        logger.warning("No serie found from bedetheque for %s from url %s", comic_series_name, serie_url)
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
        comic_series_name_cleaned = re.sub(pattern, replacement, comic_series_name)
    return comic_series_name_cleaned

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
    metadata = None
    couleurs = []
    dessins = []
    scenarios = []
    lettrages = []
    couvertures = []

    soup = soup = get_soup(comic_url, proxy = proxy)
    title = soup.find("a", itemprop="url")['title']
    booknumber = soup.find("span", class_="numa").parent.text.strip().split('.')[0]
    summary =  soup.find("meta", attrs={'name': 'description'})['content']
    if soup.find("span", class_="metier", string="(Scénario)") is not None:
        scenarioUnmatchedIndex = soup.find_all("span", class_="metier", string="(Scénario)")
        for scenario in scenarioUnmatchedIndex:
            scenarios.append(scenario.previous_sibling.previous_sibling.text.strip().split(','))
    if soup.find("span", class_="metier", string="(Dessin)") is not None:
        dessinUnmatchedIndex = soup.find_all("span", class_="metier", string="(Dessin)")
        for dessin in dessinUnmatchedIndex:
            dessins.append(dessin.previous_sibling.previous_sibling.text.strip().split(','))
    if soup.find("span", class_="metier", string="(Couleurs)") is not None:
        couleurUnmatchedIndex = soup.find_all("span", class_="metier", string="(Couleurs)")
        for couleur in couleurUnmatchedIndex:
            couleurs.append(couleur.previous_sibling.previous_sibling.text.strip().split(','))
    if soup.find("span", class_="metier", string="(Lettrage)") is not None:
        lettragesUnmatchedIndex = soup.find_all("span", class_="metier", string="(Lettrage)")
        for lettrage in lettragesUnmatchedIndex:
            lettrages.append(lettrage.previous_sibling.previous_sibling.text.strip().split(','))
    if soup.find("span", class_="metier", string="(Couverture)") is not None:
        couverturesUnmatchedIndex = soup.find_all("span", class_="metier", string="(Couverture)")
        for couverture in couverturesUnmatchedIndex:
            couvertures.append(couverture.previous_sibling.previous_sibling.text.strip().split(','))
    metadata = {
        "title": title,
        "booknumber": booknumber,
        "summary": summary,
        "scenarios": scenarios,
        "dessins": dessins,
        "couleurs": couleurs,
        "lettrages": lettrages,
        "couvertures": couvertures,
        "url": comic_url
    }
    return metadata

# if __name__ == "__main__":
#     series_url = f"https://www.bedetheque.com/serie-1757-BD-Lanfeust-des-Etoiles.html"  # replace with the ID of the series you're interested in
#     comic_url = f"https://www.bedetheque.com/BD-Kookaburra-K-Tome-2-La-planete-aux-illusions-68828.html"  # replace with the ID of the comic you're interested in
#     proxy = bedethequeApiProxies()
#     metadata = None


#     metadata = get_comic_series_metadata(series_url, proxy = proxy)
#     # metadata=find_series_url("lanfeust") # don't work yet
#     #metadata = get_comic_book_metadata(comic_url, proxy = proxy)

#     print(metadata)

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
            response = requests.get(url)
        except requests.exceptions.RequestException():
            logger.warning("Failed to get page with the proxies")
            chooseToContinue = input("Failed to get page with the proxies. Do you want to try without using a proxy (risk of ban from bedetheque) (Y/N): ")
            if chooseToContinue == 'y' or chooseToContinue == 'Y':
                logger.warning("Continuing without a proxy")
                return None
            logger.error("Choose to not continue without a proxy")
            raise Exception("Failed to retrieve proxies")
        proxies = response.text.strip().split("\r\n")
        logger.info("proxys retreived")
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
