from telegram.ext import Updater, CommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler
import logging
import json
import os
import time
import random


# === Replace this with your real token ===
TOKEN = "7688604284:AAEkTBtrtFuqJAs7ij8Ny25_U8KeCNSGSnI"

# File to save user coin data
DATA_FILE = "data.json"
user_data = {}

# 🔄 Load existing coin data (if any)
def load_data():
    global user_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            user_data = json.load(f)
        print("✅ Data loaded from file.")
    else:
        print("ℹ️ No data file found, starting fresh.")

# 💾 Save current coin data to file
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f)
    print("✅ Data saved to file.")

# /start command
def start(update, context):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "NoUsername"

    if user_id not in user_data:
        user_data[user_id] = {
            "coins": 0,
            "referred_by": None,
            "referrals": [],
            "username": username
        }
    else:
        user_data[user_id]["username"] = username  # Update in case it changed

    save_data()
    
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👋 Welcome to the Tap-to-Earn Game!\nUse /tap to earn coins!"
    )


# /tap command with cooldown
def tap(update, context):
    user_id = str(update.effective_user.id)
    user_data.setdefault(user_id, {"coins": 0, "last_tap": 0, "last_daily": 0})
    now = time.time()

    # Cooldown (5 seconds)
    last_tap = user_data[user_id].get("last_tap", 0)
    if now - last_tap < 5:
        wait = int(5 - (now - last_tap))
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"⏳ Wait {wait} seconds before tapping again!")
        return

    # 🎁 Random reward between 1 and 5
    reward = random.randint(1, 5)
    user_data[user_id]["coins"] += reward
    user_data[user_id]["last_tap"] = now
    save_data()

    coins = user_data[user_id]["coins"]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"🔥 You tapped and earned +{reward} coins!\n💰 Total: {coins}")

# /balance command
def balance(update, context):
    user_id = str(update.effective_user.id)
    coins = user_data.get(user_id, {"coins": 0})["coins"]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"💰 Your coin balance: {coins}")

# 🔁 Main function to start the bot
def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    load_data()

    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("tap", tap))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("leaderboard", leaderboard))
    dp.add_handler(CommandHandler("daily", daily))
    dp.add_handler(CommandHandler("tapbutton", tap_button))
    dp.add_handler(CallbackQueryHandler(button_callback, pattern="tap_action"))
    dp.add_handler(CommandHandler("withdraw", withdraw))
    dp.add_handler(CommandHandler("top", top))
    dp.add_handler(CommandHandler("myref", myref))
    dp.add_handler(CommandHandler("myreferrals", myreferrals))



    print("🚀 Bot is running...")
    updater.start_polling()
    updater.idle()

def leaderboard(update, context):
    if not user_data:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="📉 No data yet. Be the first to tap!")
        return

    # Sort users by coins in descending order
    top_users = sorted(user_data.items(), key=lambda x: x[1]["coins"], reverse=True)[:5]

    msg = "🏆 Top Tappers:\n\n"
    for rank, (uid, data) in enumerate(top_users, start=1):
        name = context.bot.get_chat(uid).first_name
        msg += f"{rank}. {name} — {data['coins']} coins\n"

    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

def daily(update, context):
    user_id = str(update.effective_user.id)
    now = time.time()

    if user_id not in user_data:
        user_data[user_id] = {"coins": 0, "last_tap": 0, "last_daily": 0}

    last_claim = user_data[user_id].get("last_daily", 0)

    # Check if 24 hours (86400 seconds) passed
    if now - last_claim < 86400:
        remaining = int(86400 - (now - last_claim))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"🕒 You already claimed your daily bonus!\nCome back in {hours}h {minutes}m.")
        return

    # Grant daily reward
    user_data[user_id]["coins"] += 10
    user_data[user_id]["last_daily"] = now
    save_data()

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="🎁 You received +10 daily bonus coins!")

def tap_button(update, context):
    keyboard = [[InlineKeyboardButton("🔘 Tap!", callback_data="tap_action")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="👇 Tap below to earn coins!",
                             reply_markup=reply_markup)

def button_callback(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    now = time.time()

    user_data.setdefault(user_id, {"coins": 0, "last_tap": 0, "last_daily": 0})
    last_tap = user_data[user_id].get("last_tap", 0)

    # Cooldown check (5 seconds)
    if now - last_tap < 5:
        wait = int(5 - (now - last_tap))
        query.answer(f"⏳ Wait {wait} seconds!", show_alert=False)
        return

    user_data[user_id]["coins"] += 1
    user_data[user_id]["last_tap"] = now
    save_data()

    coins = user_data[user_id]["coins"]
    query.answer()
    query.edit_message_text(text=f"🔥 You tapped! Total coins: {coins}\n\n👇 Tap again to earn more!",
                            reply_markup=InlineKeyboardMarkup(
                                [[InlineKeyboardButton("🔘 Tap Again!", callback_data="tap_action")]]
                            ))

def withdraw(update, context):
    user_id = str(update.effective_user.id)
    user_data.setdefault(user_id, {"coins": 0, "last_tap": 0, "last_daily": 0})

    coins = user_data[user_id]["coins"]

    if coins < 50:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="❌ You need at least 50 coins to withdraw.")
        return

    user_data[user_id]["coins"] -= 50
    save_data()

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="✅ You withdrew 50 coins!\nWe’ll process your reward soon 🚀")
    
def top(update, context):
    if not user_data:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="📭 No data available yet.")
        return

    # Sort users by coin count (highest first)
    sorted_users = sorted(user_data.items(), key=lambda x: x[1].get("coins", 0), reverse=True)

    message = "🏆 Top 5 Users:\n\n"
    for i, (user_id, data) in enumerate(sorted_users[:5], start=1):
        coins = data.get("coins", 0)
        message += f"{i}. User {user_id[-4:]} — {coins} coins\n"

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def myref(update, context):
    user_id = str(update.effective_user.id)
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    context.bot.send_message(chat_id=update.effective_chat.id,
        text=f"🔗 Share this link to invite friends:\n{referral_link}")

def myreferrals(update, context):
    user_id = str(update.effective_user.id)
    user = user_data.get(user_id, {"coins": 0, "referrals": []})
    referrals = user.get("referrals", [])
    referral_count = len(referrals)

    if referral_count == 0:
        msg = "😕 You haven't referred anyone yet.\nShare your link to earn rewards!"
    else:
        msg = f"🎉 You’ve referred {referral_count} user(s)!\n"
        for rid in referrals:
            ref_user = user_data.get(rid, {})
            ref_username = ref_user.get("username", "Unknown")
            msg += f"👤 @{ref_username} (ID: {rid})\n"
        msg += "\n💰 You earned +5 coins per referral!"

    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

if __name__ == "__main__":
    main()
