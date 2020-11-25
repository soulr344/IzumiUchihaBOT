import telegram.ext as tg
from telegram import Update
from tg_bot import ALLOW_EXCL

CMD_STARTERS = ('/', '!')


class CustomCommandHandler(tg.PrefixHandler):
    def __init__(self, command, callback, **kwargs):
        if "admin_ok" in kwargs:
            del kwargs["admin_ok"]
        super().__init__(CMD_STARTERS if ALLOW_EXCL else CMD_STARTERS[0], command, callback, **kwargs)

    def check_updatee(self, update):
        if (isinstance(update, Update)
                and (update.message or update.edited_message and self.allow_edited)):
            message = update.message or update.edited_message

            if message.text and len(message.text) > 1:
                fst_word = message.text_html.split(None, 1)[0]
                if len(fst_word) > 1 and any(fst_word.startswith(start) for start in CMD_STARTERS):
                    command = fst_word[1:].split('@')
                    command.append(message.bot.username)  # in case the command was sent without a username
                    if self.filters is None:
                        res = True
                    elif isinstance(self.filters, list):
                        res = any(func(message) for func in self.filters)
                    else:
                        res = self.filters(message)

                    return res and (command[0].lower() in self.command
                                    and command[1].lower() == message.bot.username.lower())

            return False


class CustomRegexHandler(tg.MessageHandler):
    def __init__(self, pattern, callback, friendly="", **kwargs):
        super().__init__(tg.Filters.regex(pattern), callback, **kwargs)
