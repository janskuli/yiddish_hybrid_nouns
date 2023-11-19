import requests
import re
from bs4 import BeautifulSoup
import parse_results as pr
import json
import click
from pathlib import Path

START = 1
URL = 'http://web-corpora.net/YNC/search/results.php'
HEADERS = {
        'Host': 'web-corpora.net',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': '491',
        'Origin': 'http://web-corpora.net',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Referer': 'http://web-corpora.net/YNC/search/frame_parts/main_menu.php?interface_language=en&subcorpus=&search_language=yiddish',
        'Upgrade-Insecure-Requests': '1'
        }
DATA = {
    'interface_language': 'en',
    'sentences_per_enlarged_occurrence': '1',
    'contexts_layout': 'basic',
    'show_gram_info': '1',
    'contexts_output_language': 'translit1',
    'search_language': 'yiddish',
    'selected_words_percent': '1',
    'min1': '1',
    'use_distance': 'same_sentence',
    'sort_by': '',
    'subcorpus': '',
    'subcorpus_query': '',
    'gr1_values': '',
    'right_punct_1': '',
    'left_punct_1': '',
    'position_1': '',
    'case_sensitive_1': '',
    'nlems_1': '',
    'gr2_values': '',
    'right_punct_2': '',
    'left_punct_2': '',
    'position_2': '',
    'case_sensitive_2': '',
    'nlems_2': ''
}

@click.command()
@click.option('-o','--occurences-per-page', default=100, help='Number of occurences per page')
@click.option('-m','--max-distance', default=1, help='Maximal diance between two search terms')
@click.option('--word1', help='First word to search')
@click.option('--lex1', help='First lexeme to search')
@click.option('--gram1',help='Gramatical properties of first search')
@click.option('--word2', help='Second word to search')
@click.option('--lex2', help='Second lexem to search')
@click.option('--gram2',help='Gramatical properties of first search')
def main(occurences_per_page, max_distance, word1, lex1, gram1, word2, lex2, gram2):
    data = DATA
    data.update({'occurences_per_page': str(occurences_per_page)})
    data.update({'max1': str(max_distance)})
    if not (word1 or lex1 or gram1):
        print('Missing word1 lex1 or gram1')
        exit()
    if word1:
        data.update({'lex1': word1, 'wf_flag1': '1'})
    if lex1:
        data.update({'lex1': lex1, 'wf_flag1': '0'})
    if gram1:
        data.update({'gr1': gram1})
        if not (lex1 or word1):
            data.update({'wf_flag1': '1', 'lex1': ''})
    else:
        data.update({'gr1': ''})
    if word2:
        data.update({'lex2': word2, 'wf_flag2': '1'})
    if lex2:
        data.update({'lex2': lex2, 'wf_flag2': '0'})
    data.update({'gr2': gram2 if gram2 else  ''})
    if not (lex2 or word2):
        data.update({'wf_flag2': '1', 'lex2': ''})

    page_num = START
    entry_id = 0
    sid, number_of_pages = post_data(data, URL)
    gram_1_name = gram1.replace(",","_") if gram1 else ''
    gram_2_name = gram2.replace(",","_") if gram2 else ''
    query_name = f'{data.get("lex1")}_{gram_1_name}_{data.get("lex2")}_{gram_2_name}'
    file_name = query_name
    Path('data').mkdir(parents=True, exist_ok=True)
    alt_num = 1
    while Path(f'data/{file_name}.jsonl').is_file():
        file_name = f'{query_name}.{alt_num}'
        alt_num += 1
    print(f'Writing results to data/{file_name}.jsonl') 
    with open(f'data/{file_name}.jsonl', 'w') as out:
        while page_num <= number_of_pages:
            page_response = get_response(sid, page_num)
            print(f'Parsing entries for page {page_num}')
            parsed_entries = pr.parse_entries(page_response.text)
            for i in range(0,len(parsed_entries)):
                ddict = pr.create_entry(parsed_entries[i],entry_id)
                jout = json.dumps(ddict) + '\n'
                out.write(jout)
                entry_id += 1

            page_num += 1    


def post_data(data,url):
    print(f'Query for {data}')
    response = requests.post(url, data = data)
    sid = re.search('sid=([0-9]+)',response.text).groups()[0]
    unrandom = requests.get(f'http://web-corpora.net/YNC/search/results.php?sid={sid}&search_language=yiddish&interface_language=en&unrandom=1')
    unrand_sid = re.search('sid=([0-9]+)',unrandom.text).groups()[0]
    first_page = requests.get(f'http://web-corpora.net/YNC/search/results.php?sid={unrand_sid}&page=1&search_language=yiddish&interface_language=en')
    soup = BeautifulSoup(first_page.text, features='html.parser')
    search_info = soup.find('table',{'class': 'search_info'})
    number_of_matches = int(re.search(r'(\d+)(\s)match',search_info.text)[1])
    if number_of_matches == 0:
        print('No match found')
        exit(1)
    print(f'{number_of_matches} matches found')
    last_page = soup.find('td', {'class': 'pages'}).find_all('a')[-1]
    last_page_num = int(re.search(r'page=([0-9]+)', str(last_page)).groups()[0]) 
    search_info = soup.find('table',{'class': 'search_info'})
    return unrand_sid, last_page_num


def get_response(sid, page_num):
    print(f'Requesting page {page_num}')
    page_url = f'http://web-corpora.net/YNC/search/results.php?sid={sid}&page={page_num}&search_language=yiddish&interface_language=en'
    return requests.get(page_url)


if __name__ == "__main__":
    main()
