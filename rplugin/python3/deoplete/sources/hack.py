import json
import re

from .base import Base
from subprocess import Popen, PIPE
from threading import Timer

TOKEN = 'AUTO332'

class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)
        self.hh_client = self.vim.vars.get('hack#hh_client', 'hh_client')
        self.timeout = self.vim.vars.get('hack#timeout', 0.5)
        self.filetypes = ['php']
        self.input_pattern = r'\w+|[^. \t]->\w*|\w+::\w*|\w\([\'"][^\)]*|\w\(\w*|\\\w*|\$\w*'
        self.mark = '[Hack]'
        self.name = 'hack'
        self.rank = 500

    def get_complete_position(self, context):
        m = re.search(r'[a-zA-Z_0-9\x7f-\xff\\$]*$', context['input'])
        return m.start() if m else -1

    def gather_candidates(self, context):
        [line, column] = self.vim.current.window.cursor
        line -= 1
        lines = self.vim.current.buffer[:]
        lines[line] = lines[line][:column] + TOKEN + lines[line][column:]
        text = str.encode('\n'.join(lines))
        command = [self.hh_client, '--auto-complete', '--json']
        try:
            process = Popen(command, stdout=PIPE, stdin=PIPE)
            timer = Timer(self.timeout, lambda p: p.kill(), [process])
            try:
                timer.start()
                command_results = process.communicate(input=text)[0]
                if process.returncode != 0:
                    return []
                results = json.loads(command_results.decode('utf-8'))
                return [parse_result(r) for r in results]
            finally:
                timer.cancel()
        except FileNotFoundError:
            return []

def parse_result(result):
    word = result['name']
    menu = result['type']
    if menu.startswith('(function'):
        menu = menu[9:-1]
    return {'word': word, 'menu': menu}
