from time import sleep

from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async
from typing import List
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.sql.users_sql import get_all_chats

import telegram
from tg_bot import dispatcher, CallbackContext, OWNER_ID

MESSAGE_1 = "And when the lamb broke the seventh seal, there was silence in heaven."
MESSAGE_2 = "I saw the seven angels who stood before God, and to them were given seven trumpets."
MESSAGE_3 = "And another angel came and stood at the altar, having a golden censer to which was given too much insence."
MESSAGE_4 = "And the smoke of the incense, which came with the prayers of the saints, ascended up before God."
MESSAGE_5 = "And the angel took the censer, and filled it with fire of the altar, and casted it into the earth, and there were voices, and thunderings, and lightnings, and an earthquake."
MESSAGE_6 = "The seven angels which had the seven trumpets prepared themselves to sound."
MESSAGE_7 = "And I heard a great voice out of the temple saying to the seven angels, Go your ways, and pour out the vials of the wrath of God upon the earth."


def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        del args[0]
        try:
            bot.leave_chat(int(chat_id))
            update.effective_message.reply_text("Left the group successfully!")
        except telegram.TelegramError:
            update.effective_message.reply_text("Attempt failed.")
    else:
        update.effective_message.reply_text("Give me a valid chat id")


""" Don't want anyone to accidentally trigger this lmao, so it's commented
def selfDestroy(bot: Bot, update: Update):
    chats = get_all_chats()
    for chat in chats:
        try:
            bot.sendMessage(MESSAGE_1, int(chat.chat_id))
            bot.sendMessage(MESSAGE_2, int(chat.chat_id))
            bot.sendMessage(MESSAGE_3, int(chat.chat_id))
            bot.sendMessage(MESSAGE_4, int(chat.chat_id))
            bot.sendMessage(MESSAGE_5, int(chat.chat_id))
            bot.sendMessage(MESSAGE_6, int(chat.chat_id))
            bot.sendMessage(MESSAGE_7, int(chat.chat_id))
            sleep(0.1)
            bot.leave_chat(int(chat.chat_id))
        except:
            pass
"""

__help__ = ""

__mod_name__ = "Leave"

LEAVE_HANDLER = CommandHandler("leave",
                               leave,
                               run_async=True,
                               filters=Filters.user(OWNER_ID))
dispatcher.add_handler(LEAVE_HANDLER)
