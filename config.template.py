# Mandatory fields - Komga informations
KOMGA_BASE_URL = "http://IP:PORT"
KOMGA_EMAIL = "email"
KOMGA_EMAIL_PASSWORD = "password"

# Mandatory fields - Status of the series to update
# By default, 'ONGOING', 'HIATUS' to limit the requests to Bedetheque
KOMGA_STATUS = ['ONGOING', 'HIATUS'] # Accept ONGOING HIATUS ABANDONED and/or ENDED

# Optionnal fields. If empty, will refresh all the books on komga
# Only on these 3 fields can be completed. If more than 1 is, it will generate an error
KOMGA_LIBRARY_LIST = [] # retrieve library value from library URL in Komga. Exemple : ['0D10T0X04WXY9', '0D10GBGK4WJZW']
KOMGA_COLLECTION_LIST = [] # retrieve collection value from collection URL in Komga. Exemple : ['0D10T0X04WXY9', '0D10GBGK4WJZW']
KOMGA_SERIE_LIST = [] # retrieve serie value from serie URL in Komga. Exemple : ['0D10T0X04WXY9', '0D10GBGK4WJZW']

# Optionnal. Set this to True to refresh only series (not books of a series)
SERIES_ONLY = False

# Optionnal. Do not use proxies, but a delay between each request. Default:7 (seconds)
WAIT_DELAY = 7
USE_PROXIES = True
