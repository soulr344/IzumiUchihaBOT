import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, ParseMode
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, RegexHandler, run_async, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, CallbackContext, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_not_admin, user_admin
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import reporting_sql as sql

REPORT_GROUPS = 5


@user_admin
def report_setting(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text(
                    "Turned on reporting! You'll be notified whenever anyone reports something."
                )

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text(
                    "Turned off reporting! You wont get any reports.")
        else:
            msg.reply_text("Your current report preference is: `{}`".format(
                sql.user_should_report(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text(
                    "Turned on reporting! Admins who have turned on reports will be notified when /report "
                    "or @admin are called.")

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text(
                    "Turned off reporting! No admins will be notified on /report or @admin."
                )
        else:
            msg.reply_text("This chat's current setting is: `{}`".format(
                sql.chat_should_report(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)


@user_not_admin
@loggable
def report(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    ping_list = ""

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user  # type: Optional[User]
        if reported_user.id == bot.id:
            message.reply_text("Haha nope, not gonna report myself.")
            return ""
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            ping_list += f"​[​](tg://user?id={admin.user.id})"

        message.reply_text(
            f"Successfully reported [{reported_user.first_name}](tg://user?id={reported_user.id}) to admins! "
            + ping_list,
            parse_mode=ParseMode.MARKDOWN)

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat is setup to send user reports to admins, via /report and @admin: `{}`".format(
        sql.chat_should_report(chat_id))


def __user_settings__(user_id):
    return "You receive reports from chats you're admin in: `{}`.\nToggle this with /reports in PM.".format(
        sql.user_should_report(user_id))


__mod_name__ = "Reporting"

__help__ = """
We're all busy people who don't have time to monitor our groups 24/7. But how do you \
react if someone in your group is spamming?

Presenting reports; if someone in your group thinks someone needs reporting, they now have \
an easy way to call all admins.

 - /report <reason>: reply to a message to report it to admins.
 - @admin: reply to a message to report it to admins.
NOTE: neither of these will get triggered if used by admins

*Admin only:*
 - /reports <on/off>: change report setting, or view current status.
   - If done in pm, toggles your status.
   - If in chat, toggles that chat's status.

To report a user, simply reply to user's message with @admin or /report. \
This message tags all the chat admins; same as if they had been @'ed.
You MUST reply to a message to report a user; you can't just use @admin to tag admins for no reason!

Note that the report commands do not work when admins use them; or when used to report an admin. Bot assumes that \
admins don't need to report, or be reported!
"""

REPORT_HANDLER = CommandHandler("report",
                                report,
                                filters=Filters.chat_type.groups,
                                run_async=True)
SETTING_HANDLER = CommandHandler("reports", report_setting, run_async=True)
ADMIN_REPORT_HANDLER = RegexHandler("(?i)@admin(s)?", report, run_async=True)

dispatcher.add_handler(REPORT_HANDLER, group=REPORT_GROUPS)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, group=REPORT_GROUPS)
dispatcher.add_handler(SETTING_HANDLER)
