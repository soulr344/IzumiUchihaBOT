from telegram import ChatMember, Update
from tg_bot import SUDO_USERS

ADMIN_PERMS = [
    "can_delete_messages", "can_restrict_members", "can_pin_messages",
    "can_promote_members"
]

MESSAGES = [
    "You don't have sufficient permissions to delete messages!",
    "You don't have sufficient permissions to restrict users!",
    "You don't have sufficient permissions to pin messages!",
    "You don't have sufficient permissions to promote users!"
]


def check_perms(update: Update, type: str):
    chat = update.effective_chat
    user = update.effective_user

    admin = chat.get_member(int(user.id))
    admin_perms = admin[ADMIN_PERMS[type]] if admin[
        "status"] != "creator" and user.id not in SUDO_USERS else True

    if not admin_perms:
        update.effective_message.reply_text(MESSAGES[type])
        return False

    return True
