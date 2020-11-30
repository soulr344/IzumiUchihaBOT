from typing import List

from telegram import Update, Bot, Chat, Message, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from tg_bot.modules.helper_funcs.chat_status import bot_admin
from tg_bot.modules.helper_funcs.filters import CustomFilters

from tg_bot import dispatcher, CallbackContext
import random, re


@bot_admin
def getlink(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    if args:
        pattern = re.compile(r'-\d+')
    else:
        message.reply_text("You don't seem to be referring to any chats.")
    links = "Invite link(s):\n"
    for chat_id in pattern.findall(message.text):
        try:
            chat = bot.getChat(chat_id)
            bot_member = chat.get_member(bot.id)
            if bot_member.can_invite_users:
                invitelink = bot.exportChatInviteLink(chat_id)
                links += str(chat_id) + ":\n" + invitelink + "\n"
            else:
                links += str(
                    chat_id
                ) + ":\nI don't have access to the invite link." + "\n"
        except BadRequest as excp:
            links += str(chat_id) + ":\n" + excp.message + "\n"
        except TelegramError as excp:
            links += str(chat_id) + ":\n" + excp.message + "\n"

    message.reply_text(links)


GETLINK_HANDLER = CommandHandler("getlink",
                                 getlink,
                                 run_async=True,
                                 filters=CustomFilters.sudo_filter)

dispatcher.add_handler(GETLINK_HANDLER)
