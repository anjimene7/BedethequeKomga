import requests
from bs4 import BeautifulSoup

def get_proxies():
    url = "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=$5000"
    response = requests.get(url)
    proxies = response.text.strip().split("\r\n")
    return [{"http": "http://" + proxy} for proxy in proxies]

def get_comic_series_metadata(comic_url = None, comic_series_name = None, comic_tome_number = None, proxies = get_proxies()):
    url = None
    success = False
    metadata = None

    if comic_url is not None:
        url = f"{comic_url}"
    elif comic_series_name is not None & comic_tome_number is not None:
        url = None # TODO @Inervo : retrieve URL from series name and tome number
    else:
        raise Exception("Failed to retrieve metadata url")

    for proxy in proxies:
        try:
            page = requests.get(url, proxies=proxy, timeout=5) # proxies=proxy
            soup = BeautifulSoup(page.content, "html.parser")
            title = soup.find("div", class_="bandeau-info serie").h1.text.strip()
            status = soup.find("div", class_="bandeau-info serie").find("i", class_="icon-info-sign").parent.text
            nbrOfAlbums = soup.find("div", class_="bandeau-info serie").find("i", class_="icon-book").parent.text.strip(' albums')
            #author = soup.find("a", title="Auteur").text
            #artist = soup.find("a", title="Dessinateur").text
            #publisher = soup.find("a", title="Editeur").text
            genres = soup.find("div", class_="bandeau-info serie").find("span", class_="style").text.split(", ")
            metadata = {
                "title": title,
                "status": status,
                "nbrOfAlbums": nbrOfAlbums,
                #"author": author,
                #"artist": artist,
                #"publisher": publisher,
                "genres": genres
            }
            success = True
            break
        except:
            continue
    if not success:
        raise Exception("Failed to retrieve metadata using all proxies")
    return metadata

if __name__ == "__main__":
    comic_url = "https://www.bedetheque.com/serie-77563-BD-Ogre-Lion.html"  # replace with the ID of the comic you're interested in
    metadata = get_comic_series_metadata(comic_url)
    print(metadata)