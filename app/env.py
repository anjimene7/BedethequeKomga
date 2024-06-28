import komgaApi
from log import logger
from os import getenv

class InitEnv:
    def __init__(self):
        # Initialize the komga API
        self.komga = komgaApi.KomgaApi(getenv('KOMGA_URL'), getenv('KOMGA_EMAIL'), getenv('KOMGA_PASSWORD'))
        self.all_series: list = []
        self.status_to_update = getenv('KOMGA_STATUS', 'ONGOING,HIATUS').split(',')
        self.dry_run = bool(getenv('KOMGA_DRY_RUN', 'true') == 'true')
        if self.dry_run:
            logger.info("Dry run is enabled. Will not update any metadata in Komga")
        self.series_only = bool(getenv('KOMGA_SERIES_ONLY', 'false') == 'true')
        self.wait_delay = getenv('KOMGA_WAIT_DELAY', 15)
        self.use_proxies = bool(getenv('KOMGA_USE_PROXIES', 'false') == 'true')
        KOMGA_LIBRARY_LIST = getenv('KOMGA_LIBRARY_LIST', None)
        KOMGA_COLLECTION_LIST = getenv('KOMGA_COLLECTION_LIST', None)
        KOMGA_SERIE_LIST = getenv('KOMGA_SERIE_LIST', None)
        logger.info(f"Parameters:\nStatus: {self.status_to_update}\nDry run: {self.dry_run}\nSeries only: {self.series_only}\nWait delay:{self.wait_delay}\nUse proxies: {self.use_proxies}")

        if KOMGA_LIBRARY_LIST:
            KOMGA_LIBRARY_LIST = KOMGA_LIBRARY_LIST.split(',')
            if KOMGA_COLLECTION_LIST or KOMGA_SERIE_LIST:
                logger.error("Use only one of KOMGA_LIBRARY_LIST or KOMGA_COLLECTION_LIST or KOMGA_SERIE_LIST")
                exit()
            logger.info("Starting refresh in Library mode")
            for library in KOMGA_LIBRARY_LIST:
                self.all_series.extend(self.komga.get_series_with_libaryid(library)['content'])
        elif KOMGA_COLLECTION_LIST:
            KOMGA_COLLECTION_LIST = KOMGA_COLLECTION_LIST.split(',')
            if KOMGA_LIBRARY_LIST or KOMGA_SERIE_LIST:
                logger.error("Use only one of KOMGA_LIBRARY_LIST or KOMGA_COLLECTION_LIST or KOMGA_SERIE_LIST")
                exit()
            logger.info("Starting refresh in Collection mode")
            for collection in KOMGA_COLLECTION_LIST:
                self.all_series.extend(
                    self.komga.get_series_with_collection(collection)['content'])
        elif KOMGA_SERIE_LIST:
            KOMGA_SERIE_LIST = KOMGA_SERIE_LIST.split(',')
            if KOMGA_LIBRARY_LIST or KOMGA_COLLECTION_LIST:
                logger.error("Use only one of KOMGA_LIBRARY_LIST or KOMGA_COLLECTION_LIST or KOMGA_SERIE_LIST")
                exit()
            logger.info("Starting refresh in specific series mode")
            for serie in KOMGA_SERIE_LIST:
                self.all_series.append(self.komga.get_serie_with_serieid(serie))
        else:
            logger.info("Starting refresh in all series mode")
            self.all_series = self.komga.get_all_series()['content']
