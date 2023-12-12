#!/bin/env python3

"""
# Module dependencies:
  - requests
  - tabulate 

  
# Syntax Example 
# Esempio di sintassi

  I nomi composti da spazi vanno inseriti tra apici
  Names composed of spaces must be enclosed in quotes

  ./ipa_pec_finder.py -c "villafranca di verona" -e comune
  ./ipa_pec_finder.py -c roma -e "dipartimento per lo sport"
"""


# import requests and suppress ssl warning
import requests
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
from tabulate import tabulate

import sys
import argparse
import hashlib
import os
import datetime
import re

from typing import IO
from typing import Union



#########
# Globs #
#########

SITE: str = "https://indicepa.gov.it"
URL: str = f"{SITE}/ipa-dati/dataset/ad45db51-fea4-4454-af80-5914e574e7b5/resource/606eef76-18d5-4aee-b965-fd0d5218fae3/download/elenco-pec.txt"

#LOCAL_FILE: str = 'elenco-pec.txt'
LOCAL_FILE: Union[str, bytes] = 'elenco-pec.txt'

# ==================== LOGO ====================

LOGO: str = """

╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     _____   _____    _____     ______ _           _               ║       
║    |  __ \ |  ___|  / ____|   |  ____(_)         | |              ║
║    | |__)  | |__   | |        | |__   _ _ __   __| | ___ _ __     ║
║    |  ___/ |  __|  | |        |  __| | | '_ \ / _` |/ _ \ '__|    ║
║    | |     | |___  | |____    | |    | | | | | (_| |  __/ |       ║
║    |_|     |_____|  \_____|   |_|    |_|_| |_|\__,_|\___|_|       ║
║                                                                   ║
║  Elenco degli indirizzi di PEC associati a:                       ║
║                                                                   ║  
║   • Enti                                                          ║
║   • Aree Organizzative Omogenee                                   ║
║   • Unità Organizzative presenti in IPA                           ║
║                                                                   ║
║  Origine dati: https://indicepa.gov.it/ipa-dati/                  ║
║                                                                   ║
║  Author: Vittorio Milazzo <vittorio.milazzo@gmail.com>            ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

"""


## -- argparse vars
parser = argparse.ArgumentParser(
    prog = 'ipa_pec_finder.py',
    description='Elenco degli indirizzi di PEC associati agli Enti alle Aree Organizzative Omogenee e alle Unità Organizzative presenti in IPA', 
    epilog='Syntax example: ipa_pec_finder.py --comune -Roma --ente "Dipartimento per lo Sport"'
    )

## Paramenters to pass to the script
parser.add_argument('--comune', '-c', dest='comune', type=str, help='The name of the comune', required=True)
parser.add_argument('--ente', '-e', dest='ente', default=None, type=str, help='The name of the ente')

## create obj with all parameters (declared above)
args = parser.parse_args()

## populate variables with proper values
comune: str = args.comune
ente: str   = args.ente



#########
# Funcs #
#########

def search_pattern(pattern: str, string: str) -> bool:
    """search pattern from a string"""
    match = re.search(r"\b" + re.escape(pattern) + r"\b", string)
    if match:
        return True
    else:
        return False


def compare_date_of_file_with_today(LOCAL_FILE: Union[str, bytes]) -> bool:
    """
    Descr:  if date of local file is one day older than today, return False
            otherwise return True
    Return: 
            True  if date of local file is the same of today
            False if date of local file is older than today

    Called by: in the main, first check is about date of localfile
    """

    # Get the file's stats
    stats = os.stat(LOCAL_FILE)

    # Get the creation and modification dates
    # in Unix format (the number of seconds since January 1, 1970)
    creation_time = stats.st_ctime
    modification_time = stats.st_mtime

    ## Date in Human readable format
    ## convert the timestamps to datetime objects
    ##
    ## all in one
    # creation_date = datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d')
    #
    ## two step to clean variables strings content
    # mypy error: Incompatible types in assignment (expression has type "str", variable has type "datetime")
    # creation_date = datetime.datetime.fromtimestamp(creation_time)
    # creation_date = creation_date.strftime('%Y-%m-%d')
    
    # Soluzione
    creation_date = datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d')

    # mypy error: Incompatible types in assignment (expression has type "str", variable has type "datetime")
    # modification_date = datetime.datetime.fromtimestamp(modification_time)
    # modification_date = modification_date.strftime('%Y-%m-%d')
    # Soluzione
    modification_date = datetime.datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d')
    
    ## returns the current local date
    today = datetime.date.today()
    ## NOTE:
    ## the type value of var 'today' is <class 'datetime.date'>
    ## the type value of creation_date and modification_date is <class 'str'>
    ## so, the comparison check creation_date == today will be return false due to different type comparison.
    ## - Solution:
    ## cast value of today in string, to avoid false negative in the final check (for return code)
    today = str(today) 
    if creation_date < today:
        return False
    else:
        return True


def request_checksum_compare() -> bool :
    """
    Descr: calculate md5 checksum on file located on web site
    return True if checksum of two files match
    Called by: in the main, first check is about compare checksom on LOCAL_FILE and on site file
    """
    print(f'■ [CHECK]: check if {LOCAL_FILE} is updated...')

    # try to make the request    
    try:
        response = requests.get(URL, verify=False, timeout=(10, 10))
    except requests.exceptions.Timeout:
        print(f'\n■ [ERROR]: Connection Timeout! I could not reach {SITE}\n')
        sys.exit(1)
    else:
        if response.status_code != 200:
            print('■ [ERROR]: the request was not successful (status code != 200')
            print(response.status_code)
            print(response.reason)
            print("AAA")
            print(URL)
            sys.exit(1)
    
    contents = response.content
    m = hashlib.md5()
    m.update(contents)
    checksum = m.hexdigest()
    checksum_online_file = checksum
    print(f'■ [CHECK]: checksum of on-line file:\t{checksum_online_file}')

    ## calculate md5 checksum on local file
    with open(LOCAL_FILE, 'rb') as f:
        contents = f.read()
        m = hashlib.md5()
        m.update(contents)
        checksum = m.hexdigest()

    checksum_local_file = checksum
    print(f'■ [CHECK]: checksum of downloaded file:\t{checksum_local_file}')

    ## final check to return bool value based from outcome
    if checksum_online_file == checksum_local_file:
        return True
    else:
        return False


def request_to_write_file(file_to_write: IO[str]) -> None:
    """
    Descr: make the requests and write data response to local file
    Return : None
    """

    print(f'■ [INFO]: Downloading file from {SITE}') 

    try:
        response = requests.get(URL, verify=False, timeout=(10, 10))
    except requests.exceptions.Timeout:
        # handle timeout
        print(f'\n■ [ERROR]: Connection Timeout! I could not reach {SITE}\n')
        sys.exit(1)
    else:
        if response.status_code != 200:
            print('■ [ERROR]: the request was not successful (status code != 200')
            print("BBBBB")
            sys.exit(1)
        
    try:
        with open(file_to_write, "w", encoding="utf-8") as outfile:
            outfile.write(response.text)
    except Exception as e:
        print('\n■ [ERROR]: cannot write local file\n')
        print(e)
        sys.exit(1)
    # file was written successfully, then check if content is ok
    else: 
        print(f'■ [OK]: file written successully: {LOCAL_FILE}') 
        print('■ [CHECK]: check the content of the downloaded file')

        if not check_content_file():
            sys.exit(1)

        
def read_downloaded_file(file_to_read: IO[str]) -> str:
    """
    Descr: read local file and save its content inside variable 'contents'
    Return: content of the file
    Called by: start
    """
    with open(file_to_read, 'r', encoding="utf-8") as file:
        contents = file.read() #        => str
        #contents = file.readlines() #  => list
        return contents


def search_and_print() -> None :
    """docstring"""
    line_symbol = "═"
    # text to print into {text}
    if ente: 
        text = f'■  Risultati per : {comune.title()} {ente.title()}'
    else:
        text = f'■  Risultati per: {comune.title()}'

    # print the text inside cornice
    print()
    print("╔" + line_symbol * (len(text)+2) + "╗")
    print("║ " + text + " ║")
    print("╚" + line_symbol * (len(text)+2) + "╝")
    #print(text)
    print()

    # pupulate var {output} with content of file
    output = read_downloaded_file(LOCAL_FILE)
    
    # if the argument --ente | -e is passed
    if ente:
        if search_pattern(comune.lower(), output.lower()) and search_pattern(ente.lower(), output.lower()):

            lines = output.strip().split('\n')
            header = re.split(r'\t|  +', lines[0].strip())
            data = []
            for line in lines[3:]:
                data.append(dict(zip(header, re.split(r'\t|  +', line.strip()))))
            
            # data contains list of dictionaries (created above)
            
            # loop over list of dict to find the matches
            for e in data:
                if comune.lower() in e['Comune'].lower() and (ente.lower() in e['Descrizione'].lower() or ente.lower() in e['Tipologia_istat'].lower()):
                    # delete \u from key "Cod_amm"
                    e = {key.encode('utf-8').decode('unicode-escape'): value for key, value in e.items()}
                    # delete character BOM ï»¿  from key "Cod_amm"
                    e = {key.strip('ï»¿'): value for key, value in e.items()}

                    # print the results inside the tables 
                    table = tabulate(e.items(), tablefmt="fancy_grid")
                    print(table)
                    print()

                    # print the results (no tables)
                    # for k,v in e.items():
                    #     print(f"{k}: {v}")
                    # print()
                    # print("=====")
                    # print()

    # if -e or --ente was not passed, then the search extends over the comune
    # (gets all results for specified comune)
    else:
        if search_pattern(comune.lower(), output.lower()):
            lines = output.strip().split('\n')
            header = re.split(r'\t|  +', lines[0].strip())
            data = []
            for line in lines[3:]:
                data.append(dict(zip(header, re.split(r'\t|  +', line.strip()))))

            for e in data:
                if comune.lower() in e['Comune'].lower():
                    # delete \u from key "Cod_amm"
                    e = {key.encode('utf-8').decode('unicode-escape'): value for key, value in e.items()}
                    # delete character BOM ï»¿  from key "Cod_amm"
                    e = {key.strip('ï»¿'): value for key, value in e.items()}

                    # print the results inside the tables 
                    table = tabulate(e.items(), tablefmt="fancy_grid")
                    print(table)
                    print()

                    # print the results (no tables)
                    # ciclo su k,v del dizionario e le stampo
                    # #print(e)
                    # for k,v in e.items():
                    #     print(f"{k}: {v}")
                    # print()
                    # print("=====")
                    # print()


def check_content_file() -> None:
    """
    Descr: this function
    
    The first action made by script is to check if LOCAL_FILE 'elenco-pec.txt' exists and if yes, 
    also check if its content is compliant, checking a specific pattern on title:
    Cod_amm Descrizione     Tipo    Tipologia_istat Regione Provincia       Comune  Mail    Tipo_mail

    Script before to make the first request,
    """

    with open(LOCAL_FILE, 'r') as infile:

        for line in infile:

            if "Cod_amm" in line or "Tipologia_istat" in line:
                print(f'■ [OK]: content of {LOCAL_FILE} is compliant')
                return True
            else:
                print(f'■ [WARNING]: unexpected content of {LOCAL_FILE}\n')
                return False
    

def check_local_file(file):    
    # check if {LOCAL_FILE} exists
    # if not call function request_to_write_file(LOCAL_FILE)
    if not os.path.exists(file):
        print(f'■ [WARNING]: {file} not found')
        # call function to make request to get/write file with db of pec
        request_to_write_file(file)

    # local file exists, check if its content is compliant
    # if not, call func to get/write file from remote source {URL}
    else: 
        if not check_content_file():
            request_to_write_file(file)



# __main__
if __name__ == "__main__":
    print(LOGO)

    ## check if already exists local db pec file
    ## and check if its content is compliant
    check_local_file(LOCAL_FILE)

    ## check and compare checksum of local file vs remote file
    if not request_checksum_compare():
        print('■ [WARNING]: files differs. Updating file')
        request_to_write_file(LOCAL_FILE)
        ## after download of file (after the request), populate var {content_file}
        search_and_print()
    else:
        print('■ [OK]: local file is updated\n')
        ## skip the request and use directly local file
        search_and_print()
