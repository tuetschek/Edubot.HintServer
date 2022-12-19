import os

# Path to data storage for Solr
SOLR_PATH = "/etc/edubot/newsolr"
# URL for Solr server
SOLR_URL = "http://localhost:8985/solr/"
# URL pattern for import
EXPORT_URL_PATTRN = "https://devel.ema.rvp.cz/api/export-dvz?api_key=SECRETAPIKEY&typ={type}&per_page={per_page}&page={page}&last_change={last_change}"
# Name of Solr core for master db
CORE_NAME_MASTER = "masterdb"
# Name of Solr core for Ema db
CORE_NAME_EMA = "ema"
# Name of directory with master db configuration
CORE_CONFIG_NAME_MASTER = "masterdb-solr-config"
# Name of directory with Ema db configuration
CORE_CONFIG_NAME_EMA = "ema-solr-config"
# Path to directory with master db configuration
CORE_CONFIG_SOURCE_PATH_MASTER = os.path.join(os.path.dirname(__file__), CORE_CONFIG_NAME_MASTER)
# Path to directory with Ema db configuration
CORE_CONFIG_SOURCE_PATH_EMA = os.path.join(os.path.dirname(__file__), CORE_CONFIG_NAME_EMA)