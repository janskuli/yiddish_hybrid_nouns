import json
import click

@click.command()
@click.option('-c','--corpus-file', help='Corpus file')
@click.option('-s','--save-file', help='Save file')

def main(corpus_file, save_file):
    if not (corpus_file or save_file):
        print('Either corpus or save file needs to be given')
        exit()
    
    if corpus_file:
        corpus = load_file(corpus_file)
        out_file = f'{corpus_file.split(".")[0]}_rated.jsonl'

    elif save_file:
        out_file = save_file
        save_point = load_file(save_file)[-1]['id']
        corpus = load_file(save_file.replace('_rated', ''))[save_point+1:]

    rate_entries(corpus, out_file)


def rate_entries(corpus, out_file):
    corpus_size = len(corpus)
    with open(out_file, 'a') as out:
        for i in range(0,len(corpus)):
            entry = corpus[i]
            print(f'{i}/{corpus_size}')
            print(f'{entry["text"]}')
            response = None
            while response not in {'y', 'n', 'q'}:
                response = input("Add to subcorpus? (n)o or (y)es:")
            if response == 'y':
                decision = None
                while decision not in {'n', 'f', 'i'}:
                    decision = input("What agreement? (n)eutrum, (f)eminine ot (i)ndiff:")
                entry.update({'decision': decision})
                jout = json.dumps(entry) + '\n'
                out.write(jout)
            elif response == 'q':
                exit()


def load_file(file_name):
    print(f'Loading from file {file_name}')
    with open(file_name, 'r') as file:
        result = [json.loads(jline) for jline in file.read().splitlines()]

    if len(result) == 0:
        print('File is empty')
        exit()

    print(f'Found {len(result)} items')
    return result


if __name__ == "__main__":
    main()
