from os import environ
from time import sleep

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from queue import Queue, Empty

if 'TGTOKEN' not in environ:
    raise ImportError('No TGTOKEN in env!')

if 'NICKNAME' not in environ:
    raise ImportError('No NICKNAME in env!')

nickname = environ['NICKNAME']

updater = Updater(token=environ['TGTOKEN'], use_context=True)
dispatcher = updater.dispatcher
bot = updater.bot

user_id = None
messages = Queue()

is_ready = lambda: not user_id is None

def start(update, context):
    global user_id
    if update.effective_user.name[1:] == nickname:
        user_id = update.effective_chat.id
        context.bot.send_message(chat_id=user_id,
                             text="Hello, nice to meet you, @%s!" % nickname)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hello, you won't be able to use this bot unless you are @%s!" % nickname)

start_handler = CommandHandler('start', start)

def put_message_in_queue(update, context):
    if update.effective_chat.id != user_id:
        context.bot.send_message(update.effective_chat.id,
            "You are not supposed to text me! (or you didn't press /start, my master)")
    messages.put(update.effective_message.text)

message_handler = MessageHandler(Filters.all, put_message_in_queue)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(message_handler)

_input, _print = input, print

def input(prompt):
    while True:
        try:
            messages.get(False)
        except Empty:
            break
    bot.send_message(user_id, prompt)
    _print()
    msg = messages.get()
    _print('@%s:> %s' % (nickname, msg))
    return msg

def new_print(msg):
    _print(msg)
    if not msg.strip():
        msg = '___'
    sleep(0.03)
    bot.send_message(user_id, msg)

print = new_print
console_print = new_print

def get_num_options(num):
    while True:
        choice = input("Enter the number of your choice: ")
        try:
            result = int(''.join(filter(str.isnumeric,choice)))
            if result >= 0 and result < num:
                return result
            else:
                print("Error invalid choice. ")
        except ValueError:
            print("Error invalid choice. ")

stop = updater.stop

updater.start_polling()
