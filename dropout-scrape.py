from os import path
from os import stat
from getpass import getpass
from bs4 import BeautifulSoup as bs
import time
import requests
from ast import literal_eval
import json

DELAY=0.5 # get-requests delay in sec

def setup_user(token, email ='', password=''):
    '''
    Sets up the headers and payload required for the initial login POST
    returns two dicts, custom_header and payload
    '''
    
    while email == '' or password == '':
        # asks the user for input as nothing existed in the .crd file
        email, password = '', ''
        email = input('E-mail address: ')
        password = getpass()

    custom_header = {'User-Agent': 'Mozilla/5.0'}
    payload = {'email': email,
               'authenticity_token': token,
               'utf8': '&#x2713;',
               'password': password
               }
    return custom_header, payload

def init_files(credentials='dropout.crd', storage='dropout.json'):
    '''
    Prepares file used for credentials so we dont
    Keep the user login info in the source code
    
    Returns a list with username,password as the two elements
    if the file exists, else return an error message

    The formate of the file is plaintext, as follows:
    Login|Password
    '''
    print(f'Checking json data in >> {storage} << for show data:')
    try:
        path.isfile(storage) and stat(storage).st_size >= 0
        with open(storage) as file:
            json_file = json.load(file)
        print('Show data exists!')
    except:
        print('Empty show database! Scraping is required.')
        json_file = False

    print(f'Checking keychain in >> {credentials} << for login details:')
    try:
        # does the file exist and is have at least 3+3 data characters?
        path.isfile(credentials) and stat(credentials).st_size >= 7
        with open(credentials) as file:
            userdata = file.read().strip().split('|')
        print('Credentials data exists!')
        return [userdata, json_file]
    except:
        print('Empty keychain! User details required for login.')
        return [False, json_file]

def post_payload(url, cust_header, payload, session):
    '''
    performs a POST to url with the custom header and the login payload
    using the session object established in the start
    we return the post object to the main function
    '''

    return session.post(url, headers=cust_header, data=payload)

def find_keyword(search_txt, key):
    '''
    Finds the line with our search item on it and returns the slice
    that is relevant
    '''

    out_list = []
    for line in search_txt.splitlines():
        if key in line and key == 'csrf-token':
            return line.split('"')[1]
        elif key in line and key == 'embed_url':
            return line[line.find('"')+1:line.find(',')-1].strip()
        elif key in line and key == 'browse-item-link':
            line = line.split('"')
            show = line[1]
            title = line[7].split('&quot')[-2][1:]
            title = title.replace('&#x27;', '')
            title = title.replace('\\u0026', '&')
            out_list.append(f'{show};{title}')
    if len(out_list) > 0:
        return out_list
    else:
        print(f'\nError: Could not find required results in search data.' \
              f'\nPlease check your inputs or network connection.' \
              f'\nsearch_txt: {search_txt} | key: {key}')
        quit()

def gen_series(series_url, session):
    '''
    simple block to grab all visible shows on the /series page

    sends con_dict to gen(seasons): 
        con_dict contains shows only at this point

    returns con_dict, a dictionary containing shows.seasons.episodes
    '''
    time.sleep(DELAY)
    series_text = session.get(series_url).text
    series_list = find_keyword(series_text, 'browse-item-link')
    show = 1
    contents = {'show': {}}
    
    for serie in series_list:
        contents['show'][show] = {}
        contents['show'][show]['name'] = serie.split(";")[1]
        contents['show'][show]['url'] = serie.split(";")[0].split(".tv")[1]
        show += 1
        
    contents = gen_seasons(session, contents)
    return contents

def gen_seasons(session, con_dict):
    '''
    Gets the dict with all the shows defined, walks over those pages and
    retrieves the seasons for each show. We still have to define the dict
    keys before we can continue assigning data here as well.
    
    sends con_dict to gen_episodes(): 
        con_dict contains shows.seasons at this point

    returns con_dict, a dictionary containing shows.seasons.episodes
    '''

    for show in con_dict['show']:
        season_i = 1 # initial season for each show
        con_dict['show'][show]['season'] = {}
        show_url = "https://www.dropout.tv" + con_dict['show'][show]['url']
        time.sleep(DELAY)
        show_data = session.get(show_url).text
        soup = bs(show_data, "html.parser")
        
        # .select works well with the dropdown lists here, each entry points
        # to the season URL. We filter out list entries that are not links.
        dropdown = soup.select('option[value]')
        list_url = [item.get('value') for item in dropdown if 'https' in item.get('value')]
        list_text = [url.text.strip() for url in dropdown]
        
        t_list, title = [(list_url[i], list_text[i]) for i in range(len(list_url))], soup.find('title').string[:-10]
        for url, show_name in t_list:
            con_dict['show'][show]['season'][season_i] = {}
            con_dict['show'][show]['season'][season_i]['name'] = show_name
            con_dict['show'][show]['season'][season_i]['url'] = url
            season_i += 1 # next season
        
    gen_episodes(session, con_dict)
    return con_dict

def gen_episodes(session, con_dict):
    '''
    Gets the dict with all the shows and seasons defined, walks over those pages
    and retrieves the episodes for each show. We still have to define the dict
    keys before we can continue assigning data here as well.

    soup.select was bothersome here, so we just just a .find_all to get the <a>
    tag that contains the url and the label with the name itself. It needs to
    be broken down however, which we do with episode[key][value]value

    returns con_dict, a dictionary containing shows.seasons.episodes
    '''
    
    for show in con_dict['show']:
        for season in con_dict['show'][show]['season']:
            season_i = 1
            con_dict['show'][show]['season'][season]['episode'] = {}
            show_url = con_dict['show'][show]['season'][season]['url']
            time.sleep(DELAY)
            soup = bs(session.get(show_url).text, 'html.parser')

            data = soup.find_all('a', {"class": "browse-item-link"})
            episode_i = 1
            for episode in data:
                ep_url = episode['href']
                ep_name = literal_eval(episode['data-track-event-properties'])['label']
                con_dict['show'][show]['season'][season]['episode'][episode_i] = {}
                con_dict['show'][show]['season'][season]['episode'][episode_i]['url'] = ep_url
                con_dict['show'][show]['season'][season]['episode'][episode_i]['name'] = ep_name
                episode_i += 1
    return con_dict

# we begin by doing a GET on the first login page, to get the necessary
# cookies and establishing a session
url = "https://www.dropout.tv/login"
series_url = "https://www.dropout.tv/series"
session = requests.Session()
url_data = session.get(url)
login_text = url_data.text # one massive wall of characters

auth_token = find_keyword(login_text, 'csrf-token')

# is there a file with credentials set?
# credcheck is a two-element list, [0] is False if there's no file
credcheck = init_files()

# setup_user returns the headers and payload we need for the post
if credcheck[0] == False:
    cust_header, payload = setup_user(auth_token)
else:
    cust_header, payload = setup_user(auth_token, credcheck[0], credcheck[1])


# we send a login post in order to get authenticated cookie
postrequest = post_payload(url, cust_header, payload, session)

# did we already have show info saved? False means no.
if credcheck[1] == False:
    print(f"Scraping required: press Enter to continue.")
    try:
        input()
    except KeyboardInterrupt:
        print('\rCtrl-C detected. Bye!')
        quit()

    # scrape the various shows that dropout carry
    contents = gen_series(series_url, session)

    with open('dropout.json', 'w') as file:
        json.dump(contents, file)

choice = input("Type URL to episode (blank to quit): ")
if choice == '':
    quit()
else:
    d20 = session.get(choice)

embed_url = find_keyword(d20.text, 'embed_url')

print(embed_url)
