#!/usr/bin/env python3
import os
import click
import logging
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
import re

import bots

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

BRAINS_IMAGE = os.environ.get('BRAINS_IMAGE', 'ddrscott/brains')
REPL_HISTORY = '.prompt_toolkit_history'
ROLE_TO_CLASS = {
    'system': SystemMessage,
    'human': HumanMessage,
    'user': HumanMessage,
    'ai': AIMessage
}

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

    return [ROLE_TO_CLASS[h['role']](content=h['content']) for h in messages]

def handle_execute(text):
    """
    Check if text starts with "```execute" and if so,
    get the contents between the code fences and execute it.
    """
    # Get the contents between the code fences
    for code in re.findall(r"```execute(.*)```", text, re.DOTALL):
        lines = []
        for line in execute_shell(code.strip()):
            print(line, end='')
            lines.append(line)
        return ''.join(lines)
    return False

@click.command()
@click.argument('name', default='vanilla')
def run(name):
    session = PromptSession(history=FileHistory(REPL_HISTORY))

    bot = bots.bot_base(name)

    print(f'Chatting with {bot["title"]}. [ctrl+c to exit.]')

    llm=ChatOpenAI(
            client=None,
            model=bot['model'],
            temperature=bot['temperature'],
            streaming=True,
        )
    messages = bot['history'].copy()
    while True:
        user_input = session.prompt("user> ")

        messages.append({'role': 'human', 'content': user_input})
        while True:
            result = []
            print(f'{name}> ', end='')
            for part in llm.stream(dict_to_langchain_messages(messages)):
                print(part.content, end='')
                result.append(part.content)
            print('')
            result = ''.join(result)
            messages.append({'role': 'ai', 'content': result})
            if output := handle_execute(result):
                messages.append({'role': 'human', 'content': f"""```output\n{output}\n```"""})
            else:
                break

if __name__ == "__main__":
    try:
        run()
    except (EOFError, KeyboardInterrupt):
        exit(0)
