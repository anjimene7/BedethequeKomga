import requests, re

regex = r"([0-9]+(?:\.[0-9]+){3}:[0-9]+).*"
c = requests.get("https://spys.me/proxy.txt")
test_str = c.text
a = re.finditer(regex, test_str, re.MULTILINE)
with open("proxies_list.txt", 'w') as file:
    for i in a:
        full = i.group().split(' ')
        ip = full[0]
        protocol = full[1].split('-')
        if len(protocol) == 2:
            pp = 'http'
        elif len(protocol) == 3:
            pp = 'https'
        print(f"{ip};{pp}", file=file)
