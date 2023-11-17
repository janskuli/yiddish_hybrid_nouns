from bs4 import BeautifulSoup
import ast
import re


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def parse_entries(data):
    soup = BeautifulSoup(data,features='html.parser') 
    entries = soup.find_all('table', {'class': 'translit'})
    return entries


def create_entry(entry, entry_id):
    caption = entry.find('table', {'class': 'caption'}).find_all('td')
    entry_text = entry.find('td', {'class': 'text'})
    contents = entry_text.contents[1:]
    tokens = [create_token(contents[i],i) for i in range(0,len(contents))]
    author = caption[1].text.strip()
    document = caption[0].text.strip()
    parsed_entry = {
            'id': entry_id,
            'document': caption[0].text.strip(),
            'author': author if author else document ,
            'date': caption[2].text.strip(),
            'raw_text': entry_text.text[1:],
            'text': ''.join([token.get('text','') for token in tokens if token]),
            'tokens': tokens
            }
    return parsed_entry


def create_token(token, position):
    token_dict = {'text': token.text, 'position': position}
    try:
        onmouseover = token.attrs.get('onmouseover', None)
        is_result = token.attrs.get('class', None)
        if is_result:
            token_dict['text'] = f'{bcolors.WARNING}{token.text}{bcolors.ENDC}'
        if onmouseover:
            matches = re.search(r'(\[.*\]),(\[.*\]),(\[.*\]),(\[.*\]),(\[.*\])',onmouseover)
            lex = ast.literal_eval(matches[1])
            pos = ast.literal_eval(matches[2])
            gram = ast.literal_eval(matches[3])
            gloss = ast.literal_eval(matches[5])
            token_dict.update({'annotation': create_annotation(lex, pos, gram, gloss)})
            return token_dict
        else:
            return None
    except AttributeError:
        return token_dict

def create_annotation(lex, pos, gram, gloss):
    ann = [{'lex': lex[i], 'pos': pos[i], 'gram': gram[i], 'gloss': gloss[i]} for i in range(0,len(lex))]
    return ann if len(ann) > 0 else None
