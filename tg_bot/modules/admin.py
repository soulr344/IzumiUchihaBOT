import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, ChatPermissions
from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, CallbackContext, SUDO_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text, extract_user
from tg_bot.modules.helper_funcs.perms import check_perms
from tg_bot.modules.log_channel import loggable


@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext, check="restrict") -> str:
    if not check_perms(update, 3):
        return
    bot = context.bot
    args = context.args
    chat_id = update.effective_chat.id
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id, title = extract_user_and_text(message, args)

    if not user_id or int(user_id) == 777000 or int(user_id) == 1087968824:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text(
            "How am I meant to promote someone that's already an admin?")
        return ""

    if user_id == bot.id:
        message.reply_text(
            "I can't promote myself! Get an admin to do it for me.")
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    bot.promoteChatMember(
        chat_id,
        user_id,
        can_change_info=bot_member.can_change_info,
        can_post_messages=bot_member.can_post_messages,
        can_edit_messages=bot_member.can_edit_messages,
        can_delete_messages=bot_member.can_delete_messages,
        can_invite_users=bot_member.can_invite_users,
        can_restrict_members=bot_member.can_restrict_members,
        can_promote_members=bool(False if user_id not in SUDO_USERS else
                                 bot_member.can_restrict_members),
        can_pin_messages=bot_member.can_pin_messages)

    text = ""
    if title:
        bot.set_chat_administrator_custom_title(chat_id, user_id, title[:16])
        text = " with title <code>{}</code>".format(title[:16])

    message.reply_text("Successfully promoted {}".format(
        mention_html(user_member.user.id, user_member.user.first_name)) +
                       text + "!",
                       parse_mode=ParseMode.HTML)
    return "<b>{}:</b>" \
           "\n#PROMOTED" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    if not check_perms(update, 3):
        return
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)

    if not user_id or int(user_id) == 777000 or int(user_id) == 1087968824:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == 'creator':
        message.reply_text(
            "This person CREATED the chat, how would I demote them?")
        return ""

    if not user_member.status == 'administrator':
        message.reply_text("Can't demote what wasn't promoted!")
        return ""

    if user_id == bot.id:
        message.reply_text(
            "I can't demote myself! Get an admin to do it for me.")
        return ""

    try:
        bot.restrict_chat_member(chat.id,
                                 int(user_id),
                                 permissions=ChatPermissions(
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)
                                 )  #restrict incase you're demoting a bot
        bot.promoteChatMember(int(chat.id),
                              int(user_id),
                              can_change_info=False,
                              can_post_messages=False,
                              can_edit_messages=False,
                              can_delete_messages=False,
                              can_invite_users=False,
                              can_restrict_members=False,
                              can_pin_messages=False,
                              can_promote_members=False)

        message.reply_text("Successfully demoted {}!".format(
            mention_html(user_member.user.id, user_member.user.first_name)),
                           parse_mode=ParseMode.HTML)
        return "<b>{}:</b>" \
               "\n#DEMOTED" \
               "\n<b>Admin:</b> {}" \
               "\n<b>User:</b> {}".format(html.escape(chat.title),
                                          mention_html(user.id, user.first_name),
                                          mention_html(user_member.user.id, user_member.user.first_name))

    except BadRequest:
        message.reply_text(
            "Could not demote. I might not be admin, or the admin status was appointed by another "
            "user, so I can't act upon them!")
        return ""


@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    if not check_perms(update, 2):
        return
    bot = context.bot
    args = context.args
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower()
                         == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            bot.pinChatMessage(chat.id,
                               prev_message.message_id,
                               disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return "<b>{}:</b>" \
               "\n#PINNED" \
               "\n<b>Admin:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name))

    return ""


@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    if not check_perms(update, 2):
        return
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user  # type: Optional[User]
    args = {}

    if update.effective_message.reply_to_message:
        args[
            "message_id"] = update.effective_message.reply_to_message.message_id

    try:
        bot.unpinChatMessage(chat.id, **args)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    return "<b>{}:</b>" \
           "\n#UNPINNED" \
           "\n<b>Admin:</b> {}".format(html.escape(chat.title),
                                       mention_html(user.id, user.first_name))


@bot_admin
@can_pin
@user_admin
@loggable
def unpinall(update: Update, context: CallbackContext) -> str:
    if not check_perms(update, 2):
        return
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user  # type: Optional[User]

    try:
        bot.unpinAllChatMessages(chat.id)
        update.effective_message.reply_text(
            "Successfully unpinned all messages!")
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    return "<b>{}:</b>" \
           "\n#UNPINNED" \
           "\n<b>Admin:</b> {}".format(html.escape(chat.title),
                                       mention_html(user.id, user.first_name))


@bot_admin
@user_admin
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    if chat.username:
        update.effective_message.reply_text("@{}".format(chat.username))
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(
                "I don't have access to the invite link, try changing my permissions!"
            )
    else:
        update.effective_message.reply_text(
            "I can only give you invite links for supergroups and channels, sorry!"
        )


def adminlist(update: Update, context: CallbackContext):
    bot = context.bot
    administrators = update.effective_chat.get_administrators()
    msg = update.effective_message
    text = "Members of *{}*:".format(update.effective_chat.title
                                     or "this chat")
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = "[{}](tg://user?id={})".format(
            user.first_name + " " + (user.last_name or ""), user.id)
        if user.username:
            name = escape_markdown("@" + user.username)
        if status == "creator":
            text += "\n *Creator:*"
            text += "\n`🤴🏻 `{} \n\n *Administrators:*".format(name)
    for admin in administrators:
        user = admin.user
        status = admin.status
        chat = update.effective_chat
        count = chat.get_members_count()
        name = "[{}](tg://user?id={})".format(
            user.first_name + " " + (user.last_name or ""), user.id)
        if user.username:
            name = escape_markdown("@" + user.username)
        if status == "administrator":
            text += "\n`👮🏻 `{}".format(name)
            members = "\n\n*Members:*\n`🙎🏻‍♂️ ` {} users".format(count)

    msg.reply_text(text + members, parse_mode=ParseMode.MARKDOWN)


def __chat_settings__(chat_id, user_id):
    return "You are *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status in (
            "administrator", "creator"))


__help__ = """
Lazy to promote or demote someone for admins? Want to see basic information about chat? \
All stuff about chatroom such as admin lists, pinning or grabbing an invite link can be \
done easily using the bot.

 - /adminlist: list of admins and members in the chat
 - /staff: same as /adminlist

*Admin only:*
 - /pin: silently pins the message replied to - add 'loud' or 'notify' to give notifies to users.
 - /unpin: unpins the currently pinned message
 - /invitelink: gets invitelink
 - /link: same as /invitelink
 - /promote: promotes the user replied to
 - /demote: demotes the user replied to

An example of promoting someone to admins:
`/promote @username`; this promotes a user to admins.
"""

__mod_name__ = "Admin"

PIN_HANDLER = CommandHandler("pin",
                             pin,
                             pass_args=True,
                             filters=Filters.chat_type.groups,
                             run_async=True)
UNPIN_HANDLER = CommandHandler("unpin",
                               unpin,
                               filters=Filters.chat_type.groups,
                               run_async=True)
UNPINALL_HANDLER = CommandHandler("unpinall",
                                  unpinall,
                                  filters=Filters.chat_type.groups,
                                  run_async=True)

INVITE_HANDLER = CommandHandler(["invitelink", "link"],
                                invite,
                                filters=Filters.chat_type.groups,
                                run_async=True)

PROMOTE_HANDLER = CommandHandler("promote",
                                 promote,
                                 pass_args=True,
                                 filters=Filters.chat_type.groups,
                                 run_async=True)
DEMOTE_HANDLER = CommandHandler("demote",
                                demote,
                                pass_args=True,
                                filters=Filters.chat_type.groups,
                                run_async=True)

ADMINLIST_HANDLER = DisableAbleCommandHandler(["adminlist", "staff"],
                                              adminlist,
                                              filters=Filters.chat_type.groups,
                                              run_async=True)

dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(UNPINALL_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
