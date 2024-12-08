'''
Download from Python library HTTP Server

usage: python dphs.py url
url is set by command 'python -m http.server' or 'python server.py'

Examples:

> ls
[1] a
[2] b
[3] c/
[4] example_dir/
> get [1]
Downloading a
Successfully saved to a
> ls [4]
[1] h
[2] i
[3] j/
> ls .
[1] a
[2] b
[3] c/
[4] example_dir/
> get -r [4]
Downloading example_dir
Downloading example_dir/h to example_dir/h
Downloading example_dir/i to example_dir/i
Downloading example_dir/j to example_dir/j
Downloading example_dir/j/k to example_dir/j/k
Downloading example_dir/j/k/l to example_dir/j/k/l
Successfully saved to example_dir
> p a
Hello, I'm file a.
> q

'''


import re
import shutil
import logging
import requests
import argparse
from tqdm import tqdm
from math import ceil
from pathlib import Path, PurePosixPath



class ExitNormally(Exception):
    pass

class Request404(Exception):
    pass

class ArgError(Exception):
    pass

class SpecialCharacter(Exception):
    pass

class ArgParser(argparse.ArgumentParser):
    def exit(self, status=0, message=None):
        if status:
            raise ArgError(message)
        # if message:
            # print(type(message))
        #     print(message)
        raise ExitNormally(message)


KiB = 1024
MiB = 1024 ** 2
# headers = {
#     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
# }


class DownloadFromPythonHTTPSever():
    "Main Class"

    def __init__(self, url, encoding='utf-8'):
        "Default encoding is utf-8"
        if url[:4] != 'http':
            self.url = 'http://' + url
        else:
            self.url = url
        if self.url[-1] == '/':
            self.url = self.url[:-1]
        self.path = PurePosixPath('/')
        self.encoding = encoding
        self.results = []

    def request(self, path='', content=False, raw=False, stream=False):
        "Try 7 times, each time for 5 seconds"
        try:
            url = self.get_url_path(path)[0]
            if path:
                for i in range(7):
                    if i:
                        print(i + 1)
                    try:
                        res = requests.get(url, stream=stream, timeout=5)
                    except requests.exceptions.ConnectionError:
                        continue
                    else:
                        break
            else:
                res = requests.get(url, stream=stream, timeout=5)

        except Exception as e:
            raise e

        if res.status_code == 404:
            raise Request404('File Not Found(404) at ' + url)
        res.raise_for_status()
        is_dir = self.is_dir(res)
        if raw:
            return res
        if content:
            real_length = int(res.headers['Content-Length'])
            if stream and real_length > MiB:
                c = ''.encode()
                length = ceil(real_length / MiB)
                bar = tqdm(
                    total=length,
                    unit='MiB',
                )
                for data in res.iter_content(MiB):
                    c += data
                    bar.update(1)
                print(end='', flush=True)
                return c, is_dir
            return res.content, is_dir
        res.encoding = self.encoding
        return res.text, is_dir

    def is_dir(self, res):
        ct = res.headers['Content-Type']
        return ct.startswith('text/html; charset')

    def parse_request(self, path=''):
        text, is_dir = self.request(path)
        if not is_dir:
            # print(ct)
            raise ArgError(
                f'{self.analyse_path(self.path / path)} is not a directory'
            )
        return self.parse_html(text)

    def parse_html(self, text):
        '''Return a dict of files and directories. And result's value will be True if result is a file, False if result is a directory
        0 represents file, 1 represents link file and 2 represents directory, 3 represents link directory'''
        reg = re.compile(r'<li><a href="(.*?)">(.*?)</a></li>')
        contents = reg.findall(text)
        results = []
        for content in contents:
            content = list(content)
            if content[0].endswith('/') and content[0][:-1] + '@' == content[1]:
                content[1] += '/'
                content.append(3)
            elif content[0].endswith('/'):
                content.append(2)
            elif content[0] + '@' == content[1]:
                content.append(1)
            else:
                content.append(0)
            results.append(content)
        return results

    def _create_argparse(self):
        'Create parsers'

        # 总命令
        parser = ArgParser(
            description='A script to download files or directories from http.server or server.py',
            prog='>',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='Type h(help) for help.\n'
            'Type [cmd] -h for detail help of [cmd].\n'
            'Type q(quit) or Ctrl-D to exit',
        )
        cmd = parser.add_subparsers(
            # parser_class=ArgParser,
            title='Commands',
            help='Commands to handle',
        )

        # 分命令
        ls = cmd.add_parser(
            'ls',
            aliases=['l'],
            help='List files and directories of current directory',
        )
        ls.add_argument(
            'path',
            metavar='dir',
            nargs='?',
            default='',
        )
        ls.set_defaults(func=self.ls)

        get = cmd.add_parser(
            'get',
            aliases=['g'],
            help='Get file or directory',
        )

        get.add_argument(
            'path',
            metavar='dest',
            help='Dest file or diretory.\n'
            '[int] represents the item displayed by the command ls',
        )
        get.add_argument(
            '-r', '--recursively',
            action='store_true',
            help='Get directory and its contents recursively',
        )
        get.set_defaults(func=self.get)

        cd = cmd.add_parser(
            'cd',
            help='Change the directory',
        )
        cd.add_argument(
            'path',
            metavar='dir',
            help='Directory',
        )
        cd.set_defaults(func=self.cd)

        pwd = cmd.add_parser(
            'pwd',
            help='Print work directory',
        )
        pwd.set_defaults(func=self.pwd)

        pt = cmd.add_parser(
            'print',
            aliases=['p'],
            help='Print file content'
        )
        pt.add_argument(
            'path',
            metavar='file',
            help='File which must be a text file instead of a binary file',
        )
        pt.set_defaults(func=self.pt)

        return parser

    def handle_args(self, cmd):
        'Handle the arguments'
        args = self.parser.parse_args(cmd.split())
        args.func(args)

    def ls(self, args):
        path = self.resolve_arg(args.path)
        self.check_special(path)
        results = self.parse_request(path)
        self.results = results

        i = 1
        for a, b, c in results:
            print(f'[{i}] ', end='', flush=True)
            if c == 0:
                if b.split('.')[-1] in ['py']:
                    print(f'\033[1;m{b}\033[0m')
                elif b.split('.')[-1] in ['tar', 'tgz', 'zip', 'rar', 'bz2']:
                    print(f'\033[1;31m{b}\033[0m')
                else:
                    print(f'\033[0;m{b}\033[0m')
            elif c == 1 or c == 3:
                print(f'\033[1;36m{b}\033[0m')
            else:
                print(f'\033[1;34m{b}\033[0m')
            i += 1

    def get(self, args):
        path = self.resolve_arg(args.path)
        self.check_special(path)
        dest = self.get_url_path(path)[1].parts[-1]
        if dest == '/':
            raise ArgError("Dest can't be /")
        # print(dest)
        content, is_dir = self.request(path, True, stream=True)
        if args.recursively ^ is_dir:
            raise ArgError(
                "Specifiy -r when dest is a directory. Don't do this when dest is a file.\nType get -h for more help"
            )
        if is_dir:
            dest += '/'
        for result in self.results:
            if dest == result[0]:
                dest = result[1]
                break
        dest = Path(dest)
        r = self.check_exist(dest)
        if not r:
            return
        if r == 2:
            self.remove(dest)
        path = PurePosixPath(path)

        print(f'Downloading {dest}')
        if not args.recursively and not is_dir:
            self.download(dest, content)
        else:
            self.download_dir(dest, path)
        print('Successfully saved to', dest)

    def check_exist(self, dest):
        if dest.exists():
            while True:
                answer = input(
                    'Dest already exists. '
                    'Do you want to overwrite?\n'
                    'y(yes) or n(no) '
                )
                if answer.lower() in ['y', 'yes']:
                    return 2
                elif answer.lower() in ['n', 'no']:
                    return 0
        return 1

    def remove(self, dest):
        if dest.is_file() or dest.is_symlink():
            dest.unlink()
        elif dest.is_dir():
            shutil.rmtree(dest)
        else:
            raise Exception("Can't remove " + dest)

    def download(self, dest, content):
        'Download a single file'
        with open(dest, 'wb') as f:
            f.write(content)

    def download_dir(self, dest, path):
        'Download a directyory'
        dest.mkdir()
        results = self.parse_request(path)
        for a, b, c in results:
            print('Downloading', path / a, 'to', dest / b)
            if c <= 1:
                content = self.request(path / a, True, stream=True)[0]
                with open(dest / b, 'wb') as f:
                    f.write(content)
            else:
                child_dest = dest / b
                child_path = path / a
                self.download_dir(
                    child_dest,
                    child_path,
                )

    def cd(self, args):
        path = self.resolve_arg(args.path)
        self.check_special(path)
        self.path = self.get_url_path(path)[1]

    def pwd(self, args):
        print(self.path)

    def pt(self, args):
        path = self.resolve_arg(args.path)
        self.check_special(path)
        content = self.request(path, True)[0]
        try:
            print(content.decode(self.encoding), end='')
        except:
            raise ArgError("Decode Error. File can't be a binary file")

    def analyse_path(self, path: PurePosixPath):
        str_path = str(path)

        if '../' in str_path:
            split_path = str_path.split('../', 1)
            path = PurePosixPath(
                split_path[0]).parent / PurePosixPath(split_path[1])
            return self.analyse_path(path)
        if str_path[-2:] == '..':
            path = path.parent.parent
            return self.analyse_path(path)

        return path

    def resolve_arg(self, arg):
        if res := re.match(r'\[(\d+)\]$', arg):
            index = int(res.group(1)) - 1
            return self.results[index][0]
        if re.match(r'\\\[\d+\]', arg) or re.match(r'\\\\\[\d+\]', arg):
            return arg[1:]
        return arg

    def get_url_path(self, path):
        path = self.analyse_path(self.path / path)
        url = self.url + str(path)
        return url, path

    def check_special(self, text):
        if '?' in text:
            logging.error('? exists in the arg')
            raise SpecialCharacter('? exists in the arg')
        for x in '&<>':
            if x in text:
                logging.warning(f'{x} exists in the arg')

    def control(self):
        # self.parser.print_help()
        while True:
            try:
                cmd = input('> ')
                if cmd in ['q', 'quit']:
                    exit()
                elif cmd in ['h', 'help']:
                    self.parser.print_help()
                else:
                    if not cmd:
                        continue
                    self.handle_args(cmd)
            except KeyboardInterrupt:
                print("If you want to exit, please type q(quit) or type Ctrl-D")
                print("Please don't type Ctrl-C")
            except EOFError:
                print()
                exit()
            except ArgError as e:
                print(e)
                print('Type h(help) for help')
            except ExitNormally:
                pass
            except Request404 as e:
                print(e)
            except IndexError as e:
                print('IndexError:', e)
            except SpecialCharacter as e:
                print('Special character:', e)
            except Exception as e:
                # raise e
                logging.critical('Exception: ' + str(e))

    def pretreat(self):
        '''Check the connection and create parser'''
        print('Connecting to', self.url)
        self.request()
        print('Connected Successfully')

        self.parser = self._create_argparse()

    def main(self):
        '''The main function'''
        self.pretreat()
        # try:
        #     self.control()
        # except:
        #     pass
        self.control()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download from Python library http.server or server.py',
    )
    parser.add_argument(
        'url', help='The url'
    )
    args = parser.parse_args()
    dphs = DownloadFromPythonHTTPSever(args.url)
    dphs.main()
