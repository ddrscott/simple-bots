#!/usr/bin/env python3
import os
import click
import logging
import subprocess
from copy import deepcopy
import re

from bots import bot_base
from colors import COLORS, CLEAR

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, AIMessage, ChatMessage

BRAINS_IMAGE = os.environ.get('BRAINS_IMAGE', 'ddrscott/brains')
REPL_HISTORY = '.prompt_toolkit_history'


def execute_shell(cmd):
    logger = logging.getLogger(__name__)
    command = 'docker run --rm -i {img} {cmd}'.format(img=BRAINS_IMAGE, cmd=cmd)
    logger.info(f"Running command: {command}")

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Yield each line of the output
    for line in process.stdout or []:
        yield line

    process.wait()

    if process.returncode != 0:
        for line in process.stderr or []:
            yield line

    logger.info(f"Command finished with return code: {process.returncode}")
    return process.returncode

def dict_to_langchain_messages(messages):
    return [
        AIMessage(content=h['content']) if h['role'] == 'ai' else \
        SystemMessage(content=h['content']) if h['role'] == 'system' else \
        ChatMessage(role='user', content=h['content'])
        for h in messages
    ]

def handle_execute(text):
    """
    Check if text starts with "```execute" and if so,
    get the contents between the code fences and execute it.
    """
    output_pre = '```output\n'
    output_post = '\n```'
    # Get the contents between the code fences
    for code in re.findall(r"```execute(.*)```", text, re.DOTALL):
        lines = [output_pre]
        print(output_pre, end='')
        for line in execute_shell(code.strip()):
            print(line, end='')
            lines.append(line)
        lines.append(output_post)
        print(output_post)
        return ''.join(lines)
    return False

@click.command()
@click.option('--bots', help='Comma-separated list of bots to chat with.')
@click.argument('start', nargs=-1)
def run(bots, start):
    names = [b.strip() for b in bots.split(',')]
    bots = [ bot_base(n) for n in names ]
    start = ' '.join(start)

    print(f'Automated chat with {" and ".join(names)}. [ctrl+c to exit.]')

    for i, bot in enumerate(bots):
        bot['llm'] = ChatOpenAI(
            client=None,
            model=bot['model'],
            temperature=bot['temperature'],
            streaming=True,
        )
        bot['color'] = COLORS[i % len(COLORS)]

    human, ai = bots[0], bots[1]
    # Always start with AI's history because it's responding first
    messages = deepcopy(ai['history'])
    # Load in initial message
    messages.append({'role': 'human', 'content': start})
    print(f'{CLEAR}{human["base"]}:\n{human["color"]}{start}', end='', flush=True)
    while True:
        result = []
        print(f'\n{CLEAR}{ai["base"]}:\n{ai["color"]}', end='', flush=True)
        for part in human['llm'].stream(dict_to_langchain_messages(messages)):
            print(part.content, end='', flush=True)
            result.append(part.content)
        result = ''.join(result)
        messages.append({'role': 'ai', 'content': result})
        # rotate the bots
        bots = bots[1:] + bots[:1]
        human, ai = bots[0], bots[1]
        # alter the system prompt based on the next responder
        messages[0]['content'] = ai['history'][0]['content']
        # any role that's 'ai', change to 'human'
        for message in messages[1:]:
            message['role'] = 'human' if message['role'] == 'ai' else 'ai'

if __name__ == "__main__":
    try:
        run()
    except (EOFError, KeyboardInterrupt):
        exit(0)
