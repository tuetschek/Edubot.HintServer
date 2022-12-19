import argparse
import os
import shutil
import urllib.request
import urllib.error
import json
from typing import Any, Optional
from socket import timeout

from config import SOLR_PATH, SOLR_URL, EXPORT_URL_PATTRN, CORE_NAME_MASTER, CORE_NAME_EMA, CORE_CONFIG_NAME_MASTER, CORE_CONFIG_NAME_EMA, CORE_CONFIG_SOURCE_PATH_MASTER, CORE_CONFIG_SOURCE_PATH_EMA

def main():
    parser = argparse.ArgumentParser(
        description="Methods for wornking with Solr database.")
    parser.add_argument("--job", required=True, type=str,
                        choices=["create", "drop", "sync"], help="Job that should be executed.")
    parser.add_argument("--last_changed", type=str,
                        help="Get items for synchronization that are newer than this date.")
    parser.add_argument("--source_db", choices=["ema", "clanky", "dum", "kc",
                        "ema_only"], type=str, help="Source database for synchronization.")

    args = parser.parse_args()

    if args.job == "create":
        create()
    elif args.job == "drop":
        drop()
    elif args.job == "sync":
        if args.source_db is None:
            parser.print_usage()
            return
        sync(args.last_changed, args.source_db)


def create():
    # Create base directory for schema configuration
    instanceTargetPath = os.path.join(SOLR_PATH, "data")
    configsetsTargetPath = os.path.join(instanceTargetPath, "configsets")
    if os.path.exists(configsetsTargetPath):
        print("Base configset directory already exists")
    else:
        print("Creating base configset directory")
        os.mkdir(configsetsTargetPath)
    # Copy schema and create core for both dbs
    for srcPath, configName, coreName in [(CORE_CONFIG_SOURCE_PATH_MASTER, CORE_CONFIG_NAME_MASTER, CORE_NAME_MASTER), (CORE_CONFIG_SOURCE_PATH_EMA, CORE_CONFIG_NAME_EMA, CORE_NAME_EMA)]:
        print(f"Creating {coreName}")
        # Copy schema
        tgtPath = os.path.join(configsetsTargetPath, configName)
        if os.path.exists(tgtPath):
            print(f"Path {tgtPath} already exists")
        else:
            print(f"Path {tgtPath} does not exist, copying")
            shutil.copytree(srcPath, tgtPath)
        # Detect if core exists
        url = f"{SOLR_URL}admin/cores?action=STATUS"
        response = urllib.request.urlopen(url).read()
        parsedResponse = json.loads(response)
        if coreName in parsedResponse["status"]:
            print(f"Core {coreName} already exists")
        else:
            # Create data dir
            tgtPath = os.path.join(instanceTargetPath, configName)
            if os.path.exists(tgtPath):
                print(f"Path {tgtPath} already exists")
            else:
                print(f"Path {tgtPath} does not exist, creating")
                os.mkdir(tgtPath)
            # Create core
            try:
                url = f"{SOLR_URL}admin/cores?action=CREATE&name={coreName}&configSet={configName}&instanceDir={configName}"
                response = urllib.request.urlopen(url).read()
                parsedResponse = json.loads(response)
                print(f"Core {coreName} created")
            except urllib.error.HTTPError as e:
                print(e.readlines())

def drop():
    instanceTargetPath = os.path.join(SOLR_PATH, "data")
    configsetsTargetPath = os.path.join(instanceTargetPath, "configsets")
    # Remove schema directory and drop core for both dbs
    for srcPath, configName, coreName in [(CORE_CONFIG_SOURCE_PATH_MASTER, CORE_CONFIG_NAME_MASTER, CORE_NAME_MASTER), (CORE_CONFIG_SOURCE_PATH_EMA, CORE_CONFIG_NAME_EMA, CORE_NAME_EMA)]:
        print(f"Deleting {coreName}")
        # Detect if core exists
        url = f"{SOLR_URL}admin/cores?action=STATUS"
        response = urllib.request.urlopen(url).read()
        parsedResponse = json.loads(response)
        if coreName in parsedResponse["status"]:
            # Create core
            url = f"{SOLR_URL}admin/cores?action=UNLOAD&core={coreName}"
            response = urllib.request.urlopen(url).read()
            parsedResponse = json.loads(response)
            print(f"Core {coreName} deleted")
        else:
            print(f"Core {coreName} already deleted")
        # Delete schema dir
        tgtPath = os.path.join(configsetsTargetPath, configName)
        if os.path.exists(tgtPath):
            shutil.rmtree(tgtPath)
            print(f"Path {tgtPath} deleted")
        else:
            print(f"Path {tgtPath} already had been deleted")
        # Delete data dir
        tgtPath = os.path.join(instanceTargetPath, configName)
        if os.path.exists(tgtPath):
            shutil.rmtree(tgtPath)
            print(f"Path {tgtPath} deleted")
        else:
            print(f"Path {tgtPath} already had been deleted")

def valueOrDefault(item: Any, key: str, default = None) -> Any:
    return default if ((key not in item) or (item[key] is None)) else item[key]

def asDate(value: Optional[str]) -> Optional[str]:
    return None if value is None else value.split("+")[0] + "Z"

def maxLength(value: Optional[str], length: int) -> Optional[str]:
    if value is None: return None
    for i in range(4):
        try:
            b = value.encode("utf8")         
            return b[:min(length-64+i, len(b))].decode("utf8")
        except:
            pass
    raise Exception()

def map_ema_only(item: Any):    
    return {
        "additional": valueOrDefault(item, "additional"),
        "autor": valueOrDefault(item, "autor"),
        "celkova_reputace": valueOrDefault(item, "celkova_reputace", "0.123"),
        "datum_posledni_indexace": asDate(valueOrDefault(item, "datum_posledni_indexace")),
        "datum_posledni_zmeny": asDate(valueOrDefault(item, "datum_posledni_zmeny")),
        "datum_vlozeni": asDate(valueOrDefault(item, "datum_vlozeni")),
        "datum_vzniku": asDate(valueOrDefault(item, "datum_vzniku")),
        "dostupnost": valueOrDefault(item, "dostupnost"),
        "externi_id": valueOrDefault(item, "externi_id"),
        "id": valueOrDefault(item, "id"),
        "id_feedu": valueOrDefault(item, "id_feedu"),
        "id_uzivatele": valueOrDefault(item, "id_uzivatele"),
        "id_zdroje": valueOrDefault(item, "id_zdroje"),
        "indexed_timestamp": valueOrDefault(item, "indexed_timestamp"),
        "jazyk": valueOrDefault(item, "jazyk"),
        "keywords_array": valueOrDefault(item, "keywords_array", "").split(";"),
        "licence": valueOrDefault(item, "licence"),
        "licence_url": valueOrDefault(item, "licence_url"),
        "nazev": valueOrDefault(item, "nazev"),
        "nazev_lemmatized": valueOrDefault(item, "nazev_lemmatized"),
        "nazev_lemmatized_ascii": valueOrDefault(item, "nazev_lemmatized_ascii"),
        "popis": valueOrDefault(item, "popis"),
        "popis_lemmatized": valueOrDefault(item, "popis"),
        "popis_lemmatized_ascii": valueOrDefault(item, "popis"),
        "klicova_slova": valueOrDefault(item, "klicova_slova"),
        "klicova_slova_lemmatized": valueOrDefault(item, "keywords_array", "").split(";"),
        "klicova_slova_lemmatized_ascii": valueOrDefault(item, "keywords_array", "").split(";"),
        "nazev_feedu": valueOrDefault(item, "nazev_feedu", ""),
        "nazev_stavu": valueOrDefault(item, "nazev_stavu", ""),
        "nazev_zdroje": valueOrDefault(item, "nazev_zdroje"),
        "otevreny_zdroj": valueOrDefault(item, "otevreny_zdroj"),
        "rocnik": valueOrDefault(item, "rocnik"),
        "stav": valueOrDefault(item, "stav"),
        "stupen_vzdelavani": valueOrDefault(item, "stupen_vzdelavani"),
        "title": valueOrDefault(item, "title"),
        "title_search": valueOrDefault(item, "title_search"),
        "typ": valueOrDefault(item, "typ"),
        "url": valueOrDefault(item, "url"),
        "url_feedu": valueOrDefault(item, "url_feedu", ""),
    }

def map_ema(item: Any):    
    return {
        "id": f"ema-{valueOrDefault(item, 'id')}",
        "source_database": "ema",
        "id_zdroje": valueOrDefault(item, "id_zdroje"),
        "id_feedu": valueOrDefault(item, "id_feedu"),
        "externi_id": valueOrDefault(item, "externi_id"),
        "url": valueOrDefault(item, "url"),
        "user_id": valueOrDefault(item, "id_uzivatele"),
        "datum_vzniku": asDate(valueOrDefault(item, "datum_vzniku")),
        "datum_vlozeni": asDate(valueOrDefault(item, "datum_vlozeni")),
        "stav": valueOrDefault(item, "stav"),
        "celkova_reputace": valueOrDefault(item, "celkova_reputace"),
        "nazev": valueOrDefault(item, "nazev"),
        "popis": valueOrDefault(item, "popis"),
        "author_name": valueOrDefault(item, "autor"),
        "otevreny_zdroj": valueOrDefault(item, "otevreny_zdroj"),
        "normalizovana_reputace": valueOrDefault(item, "normalizovana_reputace"),
        "datum_posledni_indexace": asDate(valueOrDefault(item, "datum_posledni_indexace")),
        "datum_posledni_zmeny": asDate(valueOrDefault(item, "datum_posledni_zmeny")),
        "prumer_externiho_hodnoceni": valueOrDefault(item, "prumer_externiho_hodnoceni"),
        "pocet_externich_hodnoceni": valueOrDefault(item, "pocet_externich_hodnoceni"),
        "pocet_zobrazeni": valueOrDefault(item, "pocet_zobrazeni"),
        "pocet_stazeni": valueOrDefault(item, "pocet_stazeni"),
        "pocet_komentaru": valueOrDefault(item, "pocet_komentaru"),
        "pocet_hodnoceni": valueOrDefault(item, "pocet_hodnoceni"),
        "prumer_hodnoceni_celkem": valueOrDefault(item, "prumer_hodnoceni_celkem"),
        "obsazen_v_kolekcich": valueOrDefault(item, "obsazen_v_kolekcich"),
        "licence": valueOrDefault(item, "licence"),
        "licence_url": valueOrDefault(item, "licence_url"),
        "jina_licence": valueOrDefault(item, "jina_licence"),
        "jina_licence_url": valueOrDefault(item, "jina_licence_url"),
        "stupen_vzdelavani": valueOrDefault(item, "stupen_vzdelavani"),
        "rocnik": valueOrDefault(item, "rocnik"),
        "dostupnost": valueOrDefault(item, "dostupnost"),
        "typ": valueOrDefault(item, "typ"),
        "typ_kod": valueOrDefault(item, "typ_kod"),
        "jazyk": valueOrDefault(item, "jazyk"),
        "vlozil": valueOrDefault(item, "vlozil"),
        "nazev_zdroje": valueOrDefault(item, "nazev_zdroje"),
        "url_zdroje": valueOrDefault(item, "url_zdroje"),
        "patron_zobrazit": valueOrDefault(item, "patron_zobrazit"),
        "patron": valueOrDefault(item, "patron"),
        "pocet_public_hodnoceni": valueOrDefault(item, "pocet_public_hodnoceni"),
        "pocet_public_komentaru": valueOrDefault(item, "pocet_public_komentaru"),
        "klicova_slova": valueOrDefault(item, "klicova_slova", "").split(";"),
        "vzdelavaci_obor": valueOrDefault(item, "vzdelavaci_obor"),
        "gramotnost": valueOrDefault(item, "gramotnost"),
        "prilohy": list(map(lambda x: x["url"], valueOrDefault(item, "prilohy", []))),
    }

def map_clanky(item: Any):
    return {
        "id": f"clanky-{valueOrDefault(item, 'post_id')}",
        "source_database": "clanky",
        "nazev": valueOrDefault(item, "post_title"),
        "perex": valueOrDefault(item, "perex"),
        "content": maxLength(valueOrDefault(item, "content"), 32766),
        "additional": valueOrDefault(item, "additional"),
        "o_jazyce": valueOrDefault(item, "o_jazyce"),
        "spomocnik": valueOrDefault(item, "spomocnik"),
        "studentska_prace": valueOrDefault(item, "studentska_prace"),
        "ldap_id": valueOrDefault(item, "ldap_id"),
        "author_name": valueOrDefault(item, "author_name"),
        "published": asDate(valueOrDefault(item, "published")),
        "svp": valueOrDefault(item, "svp"),
        "kompetence": valueOrDefault(item, "kompetence", "").split("|"),
        "citace": valueOrDefault(item, "citace"),
        "citace_isbn": valueOrDefault(item, "citace_isbn"),
        "klicova_slova": valueOrDefault(item, "keywords"),
        "organizace": valueOrDefault(item, "organizace", "").split("|"),
        "pv": valueOrDefault(item, "pv"),
        "presah": valueOrDefault(item, "presah"),
        "obor": valueOrDefault(item, "obor"),
        "pt": valueOrDefault(item, "pt"),
        "rvp_kody": valueOrDefault(item, "rvp", "").split("|"),
        "rvp_nazvy": valueOrDefault(item, "rvp_nazvy", "").split("|"),
        "rvp_nazvy_pv": valueOrDefault(item, "rvp_nazvy_pv"),
        "autori_cizi": valueOrDefault(item, "autori_cizi"),
        "autori_uzivatele": valueOrDefault(item, "autori_uzivatele"),
        "typ": valueOrDefault(item, "typ"),
        "zalozky": valueOrDefault(item, "zalozky", "").split("|"),
        "zalozky_nazvy": valueOrDefault(item, "zalozky_nazvy", "").split("|"),
        "commentcount": valueOrDefault(item, "commentcount"),
        "kategorie_nazvy": valueOrDefault(item, "kategorie_nazvy"),
        "rating": valueOrDefault(item, "rating"),
        "viewcount": valueOrDefault(item, "viewcount"),
        "rating_rvp": valueOrDefault(item, "rating_rvp"),
        "zalozky_nazvy": valueOrDefault(item, "type"),
        "prilohy": valueOrDefault(item, "prilohy"),
        "kategorie": valueOrDefault(item, "kategorie"),
        "nahledovy_obrazek_url": valueOrDefault(item, "nahledovy_obrazek_url"),
        "url": valueOrDefault(item, "url"),
    }

def map_dum(item: Any):
    return {
        "id": f"dum-{valueOrDefault(item, 'id')}",
        "source_database": "dum",
        "pocet_zobrazeni": valueOrDefault(item, "object_id"),
        "identificator": valueOrDefault(item, "identificator"),
        "seoname": valueOrDefault(item, "seoname"),
        "url": valueOrDefault(item, "material_link"),
        "published": asDate(valueOrDefault(item, "published")),
        "oid": valueOrDefault(item, "oid"),
        "viewcount": valueOrDefault(item, "viewcount"),
        "rating_rvp": valueOrDefault(item, "rating_rvp"),
        "recommends": valueOrDefault(item, "recommends"),
        "interactivityType": valueOrDefault(item, "interactivityType"),
        "learningResourceType": valueOrDefault(item, "learningResourceType"),
        "intendedEndUserRole": valueOrDefault(item, "intendedEndUserRole"),
        "nazev": valueOrDefault(item, "title"),
        "popis": valueOrDefault(item, "description"),
        "klicova_slova": valueOrDefault(item, "keywords", "").split("|"),
        "rvp": valueOrDefault(item, "rvp"),
        "lang": valueOrDefault(item, "lang"),
        "age_range": valueOrDefault(item, "age_range"),
        "author_name": valueOrDefault(item, "author_name"),
        "author_id": valueOrDefault(item, "author_id"),
        "files": valueOrDefault(item, "files", "").split("|"),
        "filetitles": valueOrDefault(item, "filetitles", "").split("|"),
        "filenames": valueOrDefault(item, "filenames", "").split("|"),
        "filesizes": valueOrDefault(item, "filesizes", "").split("|"),
        "fileurls": valueOrDefault(item, "fileurls", "").split("|"),
        "mimetypes": valueOrDefault(item, "mimetypes", "").split("|"),
        "commentcount": valueOrDefault(item, "commentcount"),
        "rating": valueOrDefault(item, "rating"),
        "stupen_vzdelavani": valueOrDefault(item, "education_level"),
        "vzdelavaci_oblast": valueOrDefault(item, "vzdelavaci_oblast"),
        "vzdelavaci_obor": valueOrDefault(item, "vzdelavaci_obor"),
    }

def map_kc(item: Any):
    return {
        "id": f"kc-{valueOrDefault(item, 'id')}",
        "source_database": "kc",
        "post_date": asDate(valueOrDefault(item, "post_date")),
        "nazev": valueOrDefault(item, "post_title"),
        "content": valueOrDefault(item, "post_content"),
        "post_excerpt": valueOrDefault(item, "post_excerpt"),
        "guid": valueOrDefault(item, "guid"),
        "user_login": valueOrDefault(item, "user_login"),
        "display_name": valueOrDefault(item, "display_name"),
        "zalozky_nazvy": valueOrDefault(item, "type"),
        "user_id": valueOrDefault(item, "user_id"),
    }

def sync(lastChanged: str, sourceDb: str):
    # Retrieve parameters by source database
    knownSources = {
        "ema": (map_ema, "ema", CORE_NAME_MASTER),
        "clanky": (map_clanky, "clanky", CORE_NAME_MASTER),
        "dum": (map_dum, "dum", CORE_NAME_MASTER),
        "kc": (map_kc, "kc", CORE_NAME_MASTER),
        "ema_only": (map_ema_only, "ema", CORE_NAME_EMA)
    }
    mappingFn, typeName, coreName = knownSources[sourceDb]
    lastChanged = lastChanged if lastChanged is not None else "1900-01-01"
    perPage = 500

    # Load count of items
    url = EXPORT_URL_PATTRN.format(page=1, per_page=1, last_change=lastChanged, type=typeName)
    response = urllib.request.urlopen(url).read()
    parsedResponse = json.loads(response)
    count = int(parsedResponse["all_results_count"])
    pageCount = count // perPage

    # Loop through pages
    page = 0
    while page < pageCount:
        page += 1
        print(f"Fetching page {page}/{pageCount} for {typeName}")

        # Retrieve items
        url = EXPORT_URL_PATTRN.format(page=page, per_page=perPage, last_change=lastChanged, type=typeName)
        response = urllib.request.urlopen(url).read()
        parsedResponse = json.loads(response)

        # Refresh count (in case of modifications)
        count = int(parsedResponse["all_results_count"])
        pageCount = count // perPage

        # Map items to internal db format
        print(f"Mapping page {page}/{pageCount} for {typeName}")
        parsedItems = []

        for resultItem in parsedResponse["results"]:
            parsedItem = mappingFn(resultItem)
            parsedItems.append(parsedItem)

        # Save items
        print(f"Saving page {page}/{pageCount} for {typeName}")
        attempts = 10
        timeout = 10
        for i in range(attempts):
            try:
                url = f"{SOLR_URL}{coreName}/update?commit=true"
                data = json.dumps(parsedItems).encode("utf-8")
                request = urllib.request.Request(url, data=data, method="post")
                request.add_header("Content-Type", "application/json")
                request.add_header("Content-Length", len(data))
                response = urllib.request.urlopen(request, timeout=timeout).read()
                parsedResponse = json.loads(response)
                break
            except urllib.error.URLError as e:
                if isinstance(e.reason, timeout):
                    print(f"Timeout, retrying ({attempts-i-1} attempts left)")
                    continue
                else:
                    print(e.readlines())
                    break

if __name__ == "__main__":
    main()
