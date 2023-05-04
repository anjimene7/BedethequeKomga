# Mandatory fields - Komga informations
KOMGA_BASE_URL = "http://IP:PORT"
KOMGA_EMAIL = "email"
KOMGA_EMAIL_PASSWORD = "password"

# Mandatory fields - Status of the series to update
# By default, 'ONGOING', 'HIATUS' to limit the requests to Bedetheque
KOMGA_STATUS = ['ONGOING', 'HIATUS'] # Accept ONGOING HIATUS ABANDONED and ENDED

# Optionnal fields. If empty, will refresh all the books on komga
# Only on these 2 fields can be completed. Of both are, it will generate an error
KOMGA_LIBRARY_LIST = [] # retrieve library value from library URL in Komga
KOMGA_COLLECTION_LIST = [] # retrieve collection value from collection URL in Komga

# Optionnal. Set this to True to refresh only series (not books of a series)
SERIES_ONLY = False
