import requests
from bs4 import BeautifulSoup

def get_proxies():
    url = "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=$5000"
    response = requests.get(url)
    proxies = response.text.strip().split("\r\n")
    return [{"http": "http://" + proxy} for proxy in proxies]

def find_series_url(comic_series_name, proxy = None): ## doesn't work yet. TODO
    url = None

    raise Exception("Retrieve url not yet implemented") #TODO
    page = requests.get(f"https://www.bedetheque.com/search/tout", params={"RechTexte": comic_series_name, "RechWhere": "7"},
                        proxies=proxy, timeout=5)
    soup = BeautifulSoup(page.text, "html.parser")
    url = soup.find_all("div", class_="line-title search-line")
    return url

def get_comic_series_metadata(comic_url = None, comic_series_name = None, proxy = None):
    url = None
    metadata = None

    if comic_url is not None:
        url = f"{comic_url}"
    elif comic_series_name is not None:
        raise Exception("Retrieve url from name not yet implemented") #TODO
    else:
        raise Exception("Failed to retrieve metadata url")

    page = requests.get(url, proxies=proxy, timeout=5)
    soup = BeautifulSoup(page.content, "html.parser")
    title = soup.find("div", class_="bandeau-info serie").h1.text.strip()
    status = soup.find("div", class_="bandeau-info serie").find("i", class_="icon-info-sign").parent.text
    nbrOfAlbums = soup.find("div", class_="bandeau-info serie").find("i", class_="icon-book").parent.text.strip(' albums')
    editeur = soup.find("label", string="Editeur : ").next_sibling.text
    genres = soup.find("div", class_="bandeau-info serie").find("span", class_="style").text.split(", ")
    summary = soup.find("div", class_="bandeau-boutons-serie").previous_sibling.previous_sibling.text
    metadata = {
        "title": title,
        "status": status,
        "nbrOfAlbums": nbrOfAlbums,
        "editeur": editeur,
        "genres": genres,
        "summary": summary,
        "url": url
    }
    return metadata

def get_comic_book_metadata(comic_url = None, comic_series_name = None, comic_tome_number = None, proxy = None):
    url = None
    metadata = None
    couleurs = []
    dessins = []
    scenarios = []
    lettrages = []
    couvertures = []

    if comic_url is not None:
        url = f"{comic_url}"
    elif comic_series_name is not None & comic_tome_number is not None:
        raise Exception("Retrieve url from name not yet implemented") #TODO
    else:
        raise Exception("Failed to retrieve metadata url")

    page = requests.get(url, proxies=proxy, timeout=5)
    soup = BeautifulSoup(page.content, "html.parser")
    title = soup.find("a", itemprop="url")['title']
    booknumber = soup.find("span", class_="numa").parent.text.strip().split('.')[0]
    summary =  soup.find("meta", attrs={'name': 'description'})['content']
    if soup.find("span", class_="metier", string="(Scénario)") is not None:
        scenarioUnmatchedIndex = soup.find_all("span", class_="metier", string="(Scénario)")
        for scenario in scenarioUnmatchedIndex:
            scenarios.append(scenario.previous_sibling.previous_sibling.text.strip().split(',')) #scenario = scenarioList[1].strip() + ' ' + scenarioList[0]
    if soup.find("span", class_="metier", string="(Dessin)") is not None:
        dessinUnmatchedIndex = soup.find_all("span", class_="metier", string="(Dessin)")
        for dessin in dessinUnmatchedIndex:
            dessins.append(dessin.previous_sibling.previous_sibling.text.strip().split(',')) # dessin = dessinList[1].strip() + ' ' + dessinList[0]
    if soup.find("span", class_="metier", string="(Couleurs)") is not None:
        couleurUnmatchedIndex = soup.find_all("span", class_="metier", string="(Couleurs)")
        for couleur in couleurUnmatchedIndex:
            couleurs.append(couleur.previous_sibling.previous_sibling.text.strip().split(',')) #couleurs = couleursList[1].strip() + ' ' + couleursList[0]
    if soup.find("span", class_="metier", string="(Lettrage)") is not None:
        lettragesUnmatchedIndex = soup.find_all("span", class_="metier", string="(Lettrage)")
        for lettrage in lettragesUnmatchedIndex:
            lettrages.append(lettrage.previous_sibling.previous_sibling.text.strip().split(',')) #lettrages = lettragesList[1].strip() + ' ' + lettragesList[0]
    if soup.find("span", class_="metier", string="(Couverture)") is not None:
        couverturesUnmatchedIndex = soup.find_all("span", class_="metier", string="(Couverture)")
        for couverture in couverturesUnmatchedIndex:
            couvertures.append(couverture.previous_sibling.previous_sibling.text.strip().split(',')) #couvertures = couverturesList[1].strip() + ' ' + couverturesList[0]
    metadata = {
        "title": title,
        "booknumber": booknumber,
        "summary": summary,
        "scenarios": scenarios,
        "dessins": dessins,
        "couleurs": couleurs,
        "lettrage": lettrages,
        "couvertures": couvertures,
        "url": url
    }
    return metadata

if __name__ == "__main__":
    series_url = f"https://www.bedetheque.com/serie-1757-BD-Lanfeust-des-Etoiles.html"  # replace with the ID of the series you're interested in
    comic_url = f"https://www.bedetheque.com/BD-Kookaburra-K-Tome-2-La-planete-aux-illusions-68828.html"  # replace with the ID of the comic you're interested in
    proxies = get_proxies()
    metadata = None

    for proxy in proxies:
        try:
            #metadata = get_comic_series_metadata(series_url, proxy = proxy)
            metadata=find_series_url("lanfeust", proxy) # don't work yet
            #metadata = get_comic_book_metadata(comic_url, proxy = proxy)
            if metadata is not None:
                break
        except:
            raise Exception("Failed to retrieve metadata using all proxies")
    print(metadata)