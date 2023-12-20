#!/usr/bin/env python3
import os
import click
from copy import deepcopy

from bots import bot_base
from colors import COLORS, CLEAR

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, AIMessage, ChatMessage

BRAINS_IMAGE = os.environ.get('BRAINS_IMAGE', 'ddrscott/brains')
REPL_HISTORY = '.prompt_toolkit_history'


def dict_to_langchain_messages(messages):
    return [
        AIMessage(content=message['content']) if message['role'] == 'ai' else
        SystemMessage(content=message['content']) if message['role'] == 'system' else
        ChatMessage(role='user', content=message['content'])
        for message in messages
    ]

@click.command()
@click.option('--bots', help='Comma-separated list of bots to chat with.')
@click.argument('start', nargs=-1)
def run(bots, start):
    names = [b.strip() for b in bots.split(',')]
    bots = [bot_base(n) for n in names]
    start = ' '.join(start)

    print(f'Automated chat with {" and ".join(names)}. [ctrl+c to exit.]')

    for i, bot in enumerate(bots):
        bot.llm = ChatOpenAI(
            client=None,
            streaming=True,
            **(bot.model_kwargs or {})
        )
        bot.ansi_color = COLORS[i % len(COLORS)]

    human, ai = bots[0], bots[1]
    # Always start with AI's history because it's responding first
    messages = deepcopy(ai.messages)
    # Load in initial message
    messages.append({'role': 'human', 'content': start})
    print(f'{CLEAR}{human.base}:\n{human.ansi_color}{start}', end='', flush=True)
    while True:
        result = []
        print(f'\n\n{CLEAR}{ai.base}:\n{ai.ansi_color}', end='', flush=True)
        for part in human.llm.stream(dict_to_langchain_messages(messages)):
            print(part.content, end='', flush=True)
            result.append(part.content)
        result = ''.join(result)
        messages.append({'role': 'ai', 'content': result})
        # rotate the bots
        bots = bots[1:] + bots[:1]
        human, ai = bots[0], bots[1]
        # alter the system prompt based on the next responder
        messages[0]['content'] = ai.messages[0]['content']
        # any role that's 'ai', change to 'human'
        for message in messages[1:]:
            message['role'] = 'human' if message['role'] == 'ai' else 'ai'

if __name__ == "__main__":
    try:
        run()
    except (EOFError, KeyboardInterrupt):
        exit(0)
