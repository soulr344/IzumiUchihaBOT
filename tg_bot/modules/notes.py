import re
from time import sleep
from io import BytesIO
from typing import Optional, List

from telegram import MAX_MESSAGE_LENGTH, ParseMode, InlineKeyboardMarkup
from telegram import Message, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, RegexHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.notes_sql as sql
from tg_bot import dispatcher, CallbackContext, MESSAGE_DUMP, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.misc import build_keyboard, revert_buttons
from tg_bot.modules.helper_funcs.msg_types import get_note_type

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video
}


# Do not async
def get(bot, update, notename, show_none=True, no_format=False):
    chat_id = update.effective_chat.id
    note = sql.get_note(
        chat_id, notename
    )  # removed lower() for compatibility for fetching previously saved notes
    message = update.effective_message  # type: Optional[Message]
    timer = sql.get_clearnotes(chat_id)
    delmsg = ""

    if note:
        # If we're replying to a message, reply to that message (unless it's an error)
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id

        if note.is_reply:
            if MESSAGE_DUMP:
                try:
                    delmsg = bot.forward_message(chat_id=chat_id,
                                        from_chat_id=MESSAGE_DUMP,
                                        message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text(
                            "This message seems to have been lost - I'll remove it "
                            "from your notes list.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
            else:
                try:
                    delmsg = bot.forward_message(chat_id=chat_id,
                                        from_chat_id=chat_id,
                                        message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text(
                            "Looks like the original sender of this note has deleted "
                            "their message - sorry! Get your bot admin to start using a "
                            "message dump to avoid this. I'll remove this note from "
                            "your saved notes.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
        else:
            text = note.value
            keyb = []
            parseMode = ParseMode.MARKDOWN
            buttons = sql.get_buttons(chat_id, notename)
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                keyb = build_keyboard(buttons)

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    delmsg = bot.send_message(chat_id,
                                     text,
                                     reply_to_message_id=reply_id,
                                     parse_mode=parseMode,
                                     disable_web_page_preview=True,
                                     reply_markup=keyboard)
                else:
                    delmsg = ENUM_FUNC_MAP[note.msgtype](chat_id,
                                                note.file,
                                                caption=text,
                                                reply_to_message_id=reply_id,
                                                parse_mode=parseMode,
                                                reply_markup=keyboard)

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    message.reply_text(
                        "Looks like you tried to mention someone I've never seen before. If you really "
                        "want to mention them, forward one of their messages to me, and I'll be able "
                        "to tag them!")
                elif FILE_MATCHER.match(note.value):
                    message.reply_text(
                        "This note was an incorrectly imported file from another bot - I can't use "
                        "it. If you really need it, you'll have to save it again. In "
                        "the meantime, I'll remove it from your notes list.")
                    sql.rm_note(chat_id, notename)
                else:
                    message.reply_text(
                        "This note could not be sent, as it is incorrectly formatted. Ask in "
                        "@bot_workshop if you can't figure out why!")
                    LOGGER.exception("Could not parse message #%s in chat %s",
                                     notename, str(chat_id))
                    LOGGER.warning("Message was: %s", str(note.value))
        if timer != 0:
            sleep(int(timer))
            try:
                delmsg.delete()
                message.delete()
            except:
                pass
        return
    elif show_none:
        message.reply_text("This note doesn't exist")


def cmd_get(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    if len(args) >= 2 and args[1].lower() == "noformat":
        get(bot, update, args[0], show_none=True, no_format=True)
    elif len(args) >= 1:
        get(bot, update, args[0], show_none=True)
    else:
        update.effective_message.reply_text("Get rekt")


def hash_get(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    get(bot, update, no_hash, show_none=False)


@user_admin
def save(update: Update, context: CallbackContext):
    bot = context.bot
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    msg = update.effective_message  # type: Optional[Message]
    chat_name = chat.title or chat.first or chat.username
    try:
        note_name, text, data_type, content, buttons = get_note_type(msg)
    except IndexError:
        msg.reply_text("Yes, I'm dumb enough to save an empty note.",
                       parse_mode=ParseMode.MARKDOWN)
        return

    if data_type is None:
        msg.reply_text("Dude, there's no note.")
        return

    if len(text.strip()) == 0:
        text = escape_markdown(note_name)

    note_name = note_name.lower()
    sql.add_note_to_db(chat_id,
                       note_name,
                       text,
                       data_type,
                       buttons=buttons,
                       file=content)

    msg.reply_text(
        "Yas! Saved `{note_name}` for *{chat_name}*.\nGet it with `/get {note_name}`, or `#{note_name}`"
        .format(note_name=note_name, chat_name=chat_name),
        parse_mode=ParseMode.MARKDOWN)

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        if text:
            msg.reply_text(
                "Seems like you're trying to save a message from a bot. Unfortunately, "
                "bots can't forward bot messages, so I can't save the exact message. "
                "\nI'll save all the text I can, but if you want more, you'll have to "
                "forward the message yourself, and then save it.")
        else:
            msg.reply_text(
                "Bots are kinda handicapped by telegram, making it hard for bots to "
                "interact with other bots, so I can't save this message "
                "like I usually would - do you mind forwarding it and "
                "then saving that new message? Thanks!")
        return


@user_admin
def clear(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    chat = update.effective_chat
    chat_name = chat.title or chat.first or chat.username
    note_name, text, data_type, content, buttons = get_note_type(msg)
    if len(args) >= 1:
        notename = args[0]

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text(
                "Note for '`{note_name}`' has been deleted!".format(
                    note_name=note_name),
                parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text(
                "Unfortunately, There is no such notes saved on {chat_name}!".
                format(chat_name=chat_name))


def list_notes(update: Update, context: CallbackContext):
    bot = context.bot
    chat_id = update.effective_chat.id
    timer = sql.get_clearnotes(chat_id)
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    note_list = sql.get_all_chat_notes(chat_id)
    chat_name = chat.title or chat.first or chat.username
    msg = "*List of notes in {}:*\n"
    des = "You can get notes by using `/get notename`, or `#notename`.\n"
    delmsg = ""
    for note in note_list:
        note_name = (" • `{}`\n".format(note.name))
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg,
                                                parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name

    if msg == "*List of notes in {}:*\n":
        delmsg = update.effective_message.reply_text("No notes in this chat!")

    elif len(msg) != 0:
        delmsg = update.effective_message.reply_text(msg.format(chat_name) + des,
                                            parse_mode=ParseMode.MARKDOWN)
    if timer != 0:
        sleep(int(timer))
        try:
            delmsg.delete()
            update.effective_message.delete()
        except:
            pass

@user_admin
def clearnotes(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    message = update.effective_message
    if len(args) > 0 and args[0].isdigit():
        timer = int(args[0])
        if timer > 900 or ( timer < 60 and timer != 0 ):
            message.reply_text("Cannot set clearnotes value higher than 900 and lower than 60.")
            return
        sql.set_clearnotes(chat_id, timer=timer)
        if timer != 0:
            message.reply_text(f"Success! Set timer to {args[0]}s and clearnotes to on!")
        else:
            message.reply_text("Disabled clearnotes!")
    else:
        timer = sql.get_clearnotes(chat_id)
        clear = True if timer > 0 else False
        message.reply_text(f"Clearnotes is currently set to {clear}" + (((" with timer set to " + str(timer) + "s")) if clear else "!"))

def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get('extra', {}).items():
        match = FILE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end():].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata,
                                   sql.Types.TEXT)
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(
                chat_id,
                document=output,
                filename="failed_imports.txt",
                caption="These files/photos failed to import due to originating "
                "from another bot. This is a telegram API restriction, and can't "
                "be avoided. Sorry for the inconvenience!")


def __stats__():
    return "{} notes, across {} chats.".format(sql.num_notes(),
                                               sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    timer = sql.get_clearnotes(chat_id)
    clear = True if timer > 0 else False
    return ("There are `{}` notes in this chat.\nClear welcome is set to {}".format(len(notes), clear) + (" with timer set to {}".format(timer) if clear else "."))


__help__ = """
Save data for future users with notes!

Notes are great to save random tidbits of information; a phone number, a nice gif, a funny picture - anything!

 - /get <notename>: get the note with this notename
 - #<notename>: same as /get
 - /notes or /saved: list all saved notes in this chat

If you would like to retrieve the contents of a note without any formatting, use `/get <notename> noformat`. This can \
be useful when updating a current note.

*Admin only:*
 - /save <notename> <notedata>: saves notedata as a note with name notename
A button can be added to a note by using standard markdown link syntax - the link should just be prepended with a \
`buttonurl:` section, as such: `[somelink](buttonurl:example.com)`. Check /markdownhelp for more info.
 - /save <notename>: save the replied message as a note with name notename
 - /clear <notename>: clear note with this name
 - /clearnotes: replies with the current settings for clearing notes in the chat
 - /clearnotes <time>: automatically deletes messages used for retrieving notes after <time> seconds. \
This automatically deletes `/notes`, `#notename` and `/get notename` message and bot replies for those messages. \
Setting time as 0 will disable it.
 
 An example of how to save a note would be via:
`/save data This is some data!`

Now, anyone using "/get notedata", or "#notedata" will be replied to with "This is some data!".

If you want to save an image, gif, or sticker, or any other data, do the following:
`/save notename` while replying to a sticker or whatever data you'd like. Now, the note at "#notename" contains a sticker which will be sent as a reply.

Tip: to retrieve a note without the formatting, use /get <notename> noformat
This will retrieve the note and send it without formatting it; getting you the raw markdown, allowing you to make easy edits.
"""

__mod_name__ = "Notes"

GET_HANDLER = CommandHandler("get",
                             cmd_get,
                             run_async=True,
                             filters=Filters.chat_type.groups)
HASH_GET_HANDLER = RegexHandler(r"^#[^\s]+", hash_get, run_async=True)

SAVE_HANDLER = CommandHandler("save",
                              save,
                              run_async=True,
                              filters=Filters.chat_type.groups)
DELETE_HANDLER = CommandHandler("clear",
                                clear,
                                run_async=True,
                                filters=Filters.chat_type.groups)

LIST_HANDLER = DisableAbleCommandHandler(["notes", "saved"],
                                         list_notes,
                                         admin_ok=True,
                                         run_async=True,
                                         filters=Filters.chat_type.groups)

CLEARNOTES_HANDLER = CommandHandler("clearnotes",
                             clearnotes,
                             run_async=True,
                             filters=Filters.chat_type.groups)

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
dispatcher.add_handler(CLEARNOTES_HANDLER)
