from multiprocessing.util import log_to_stderr
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from mybale import *
from telegram.ext import CallbackContext, CallbackQueryHandler

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters, CallbackContext,
)

TOKEN = ""

telegram_app = None
watch = {
    "telegram_chat_id": None,
    "bale_id": None,
    "chat_type": None,
    "bale_name": None,
}
seen_messages = set()
sender_names = {}


def message_key(message):
    return int(message.chat.type), int(message.chat.id), int(message.message_id)


def is_watched_message(message):
    return (
        watch["telegram_chat_id"] is not None
        and int(message.chat.id) == watch["bale_id"]
        and int(message.chat.type) == watch["chat_type"]
    )


async def sender_name(message):
    if int(message.sender_id) == int(client.id):
        return "You"

    sender_id = int(message.sender_id)
    if int(message.chat.type) == int(ChatType.PRIVATE):
        return watch["bale_name"] or f"user {sender_id}"

    if sender_id in sender_names:
        return sender_names[sender_id]

    try:
        user = await client.load_user(sender_id, ChatType.PRIVATE)
        name = user.name
    except Exception as ex:
        print(ex)
        name = f"user {sender_id}"
    sender_names[sender_id] = name
    return name


async def message_lines(message):
    if not is_displayable_message_text(message.text):
        return []
    name = await sender_name(message)
    return [f"{name}: {line}" for line in message.text.splitlines() if line.strip()]


async def send_text_lines(chat_id, lines):
    for line in lines:
        if line.strip():
            await telegram_app.bot.send_message(chat_id=chat_id, text=line)


async def forward_new_message(message):
    if telegram_app is None or not is_watched_message(message):
        return

    key = message_key(message)
    if key in seen_messages:
        return
    seen_messages.add(key)

    try:
        if int(message.sender_id) == int(client.id):
            return
    except Exception:
        pass

    lines = await message_lines(message)
    if lines:
        await send_text_lines(watch["telegram_chat_id"], lines)


async def remember_recent_messages(bale_id, chat_type):
    try:
        history = await client.load_history(
            chat_id=bale_id,
            chat_type=ChatType(chat_type),
            limit=20,
        )
    except Exception as ex:
        print(ex)
        return []

    for message in history:
        seen_messages.add(message_key(message))
    return history


async def poll_open_chat():
    while True:
        await asyncio.sleep(3)
        if watch["telegram_chat_id"] is None:
            continue
        try:
            history = await client.load_history(
                chat_id=watch["bale_id"],
                chat_type=ChatType(watch["chat_type"]),
                limit=5,
            )
        except Exception as ex:
            print(ex)
            continue

        for message in sorted(history, key=lambda msg: (msg.date, msg.message_id)):
            await forward_new_message(message)


@dp.message()
async def on_new_bale_message(message):
    await forward_new_message(message)


async def chatter(update: Update, context: CallbackContext):
    current = context.user_data.get("current")
    if not current:
        await update.message.reply_text("pick some one")
        return
    user_id, chat_type = current
    try:
        await sender(user_id, update.message.text, chat_type)
    except Exception as ex:
        print(ex)
        await update.message.reply_text("failed to send")
        return


async def button_click(update: Update, context: CallbackContext):
    call = update.callback_query
    await call.answer()

    if call.data == "return":
        context.user_data.pop("current", None)
        watch.update({"telegram_chat_id": None, "bale_id": None, "chat_type": None, "bale_name": None})
        await chat_loader(call.message, context)
        return

    bale_id, chat_type = call.data.split(":")
    bale_id = int(bale_id)
    chat_type = int(chat_type)
    context.user_data["current"] = (bale_id, chat_type)
    selected_chat = next(
        (chat for chat in context.user_data.get("chats", {}).values()
         if int(chat["id"]) == bale_id and int(chat["type"]) == chat_type),
        None,
    )
    watch.update({
        "telegram_chat_id": call.message.chat.id,
        "bale_id": bale_id,
        "chat_type": chat_type,
        "bale_name": selected_chat["name"] if selected_chat else None,
    })

    history = await remember_recent_messages(bale_id, chat_type)
    lines = []
    for message in sorted(history, key=lambda msg: (msg.date, msg.message_id)):
        lines.extend(await message_lines(message))
    if not lines:
        lines = ["no messages"]
    for i in lines:
        if i.strip():
            await call.message.reply_text(i)

    markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="return", callback_data="return")]])
    await call.message.reply_text("choose", reply_markup=markup)


async def chat_loader(message, context: CallbackContext):
    keyboard = []
    chats, printer = await nameGetter()
    context.user_data["chats"] = chats
    [keyboard.append([InlineKeyboardButton(text=j["name"], callback_data=f"{j['id']}:{j['type']}")]) for i, j in chats.items()]
    markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("choose", reply_markup=markup)


async def start(update: Update, context: CallbackContext):
    await chat_loader(update.message, context)


async def post_init(app):
    global telegram_app
    telegram_app = app
    await client.start(run_in_background=True)
    asyncio.create_task(poll_open_chat())


def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chatter))
    app.run_polling()


if __name__ == "__main__":
    main()
