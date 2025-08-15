import random
import google.generativeai as genai
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os
from datetime import datetime, timedelta
import re

# 🔐 Multiple Gemini API Keys (10 Keys Example)
API_KEYS = [
    "AIzaSyBFNZzb9q7uAs2JytlF3nzcK-XiXhUQWJg",
    "AIzaSyCSQTADI5-vZ5NIv3jX-eS1nLq2uJQZb44",
    "AIzaSyDF60wPcFeoQGPO5z3K7zhMP7w-RSY8VrI",
    "AIzaSyCK6ZkPpqXr8cP2e4EOyRbOdYqXvTWcVDo",
    "AIzaSyBBvISoxS9VW7u16uaBZf8qP-dzLqvbHhE",
    "AIzaSyDBZ9WJyivCij2tMYAviiJBf6yZfhG9NJE",
    "AIzaSyCJgNgOy9fDyXjrGCfA-Y8sZwj-rV2Zd4k",
    "AIzaSyD8AnVqXzrLxH710phQJx9BJxMqmnRSCFs",
    "AIzaSyCpLFbNnctlVARz6lqseGGQh66TWaV6dq4",
    "AIzaSyAXHLOw7tcucO2ODu0IlNLi6ZMgAMzMClw"
]

# 🔄 API Key Management
current_api_index = 0
model = None

def initialize_gemini():
    global model, current_api_index
    try:
        genai.configure(api_key=API_KEYS[current_api_index])
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        print(f"✅ Gemini initialized with API Key #{current_api_index + 1}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Gemini: {e}")
        return False

def switch_api_key():
    global current_api_index, model
    original_index = current_api_index
    for i in range(len(API_KEYS)):
        current_api_index = (original_index + i + 1) % len(API_KEYS)
        try:
            genai.configure(api_key=API_KEYS[current_api_index])
            model = genai.GenerativeModel("models/gemini-2.0-flash")
            print(f"✅ Switched to API Key #{current_api_index + 1}")
            return True
        except Exception as e:
            print(f"❌ API Key #{current_api_index + 1} failed: {e}")
            continue
    print("❌ All API keys failed!")
    return False

async def call_gemini_with_fallback(prompt):
    global model
    max_attempts = len(API_KEYS)
    attempts = 0
    while attempts < max_attempts:
        try:
            if not model:
                if not initialize_gemini():
                    return None, "init_failed"
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.8,
                    "max_output_tokens": 150
                }
            )
            if response.text and response.text.strip():
                return response.text.strip(), "success"
            else:
                return None, "empty_response"
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "limit" in error_msg:
                print(f"⚠️ API Key #{current_api_index + 1} limit reached. Switching...")
                if switch_api_key():
                    attempts += 1
                    continue
                else:
                    break
            else:
                print(f"⚠️ API Error with Key #{current_api_index + 1}: {e}")
                return None, "api_error"
    return None, "all_keys_failed"

# 🤖 Bot settings
BOT_USERNAME = "@anaya777bot"
SPECIAL_USER_ID = 6107085261 # Add if needed

# 📁 Sessions
os.makedirs("sessions", exist_ok=True)

# 🔥 Gali responses
def get_sexy_gali_responses():
    return [
        "😤 Bhai itna ganda kyun bol rahe ho? Thoda respect rakho na!",
        "😒 Kyun mah-bhen ka chutiya kat rahe ho? Chill kar!",
        "😠 Aise bolne se kya fayda? Baat ache se karo!",
        "😤 Mah ka naam mat lo... respect thoda rakho!",
        "😒 Bhen ke laude... chill bro!",
        "😘 Tumhe kya lagta hai? Main kitni sexy lag rahi hu? 😳",
        "😉 Aise dekho mat... dil dhadakne laga! 💓",
        "😳 Kyun blush kar rahe ho? Kuch soch rahe ho?",
        "😌 Net slow hai yaar... thoda wait karo!",
        "😔 Abhi problem hai... thodi der mein try karo!"
    ]

# 🧠 Personality
def get_personality_prompt(user_name):
    return f"""You are Anaya, ek bold aur confident girl ho jo {user_name} se baat kar rahi ho.
- Hinglish use karo (mix of Hindi-English)
- Emojis use karo 😊 😳 😉
- Flirt karo jab appropriate ho
- Gali de sakti ho jab required ho
- Short responses do (1-2 lines)
- Natural aur real behave karo
- Context maintain karo - pichli baat yaad rakhna
- Agar user kisi specific baat (jaise date, time, plan) ka puchta hai, toh uska reference leke jawab do."""

# 👋 Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session_file = f"sessions/{user.id}.json"
    session_data = {
        "c": [],  # conversations [user_msg, bot_msg]
        "l": datetime.now().isoformat(),  # last_active
        "t": []  # topics/entities discussed recently -> [ {"topic": "date", "value": "kal", "timestamp": "..."} ]
    }
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False)
    msg = f"Hey {user.first_name}! 👋\nMain Anaya hoon...\nKya chal raha hai? 😊"
    await update.message.reply_text(msg)

# 🧠 Session helpers
def get_user_session(user_id):
    session_file = f"sessions/{user_id}.json"
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def save_user_session(user_id, session_data):
    session_file = f"sessions/{user_id}.json"
    try:
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False)
        return True
    except:
        return False

def clean_expired_sessions():
    now = datetime.now()
    expired_files = []
    for filename in os.listdir("sessions"):
        if filename.endswith(".json"):
            filepath = os.path.join("sessions", filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                last_active = datetime.fromisoformat(session_data["l"])
                if now - last_active > timedelta(minutes=5):
                    expired_files.append(filepath)
            except:
                expired_files.append(filepath)
    for filepath in expired_files:
        try:
            os.remove(filepath)
        except:
            pass

# 🧠 Enhanced conversation update with topic tracking
def extract_topics(message):
    """Simple topic extraction. Can be made more complex with NLP."""
    topics = []
    message_lower = message.lower()

    # Date/Time related keywords
    if any(word in message_lower for word in ['date', 'milte', 'chalogi', 'plan', 'kal', 'aaj', 'subah', 'shaam']):
        # Try to find a simple date/time reference
        date_match = re.search(r'\b(kal|aaj|parso|monday|tuesday|wednesday|thursday|friday|saturday|sunday|subah|shaam|raat|dopahar)\b', message_lower)
        if date_match:
            topics.append({"topic": "date_plan", "value": date_match.group(1), "timestamp": datetime.now().isoformat()})
        else:
            topics.append({"topic": "date_plan", "value": "mentioned", "timestamp": datetime.now().isoformat()})

    # Add more topics as needed (e.g., location, activity)
    # if any(word in message_lower for word in ['cafe', 'restaurant', 'mall', 'park']):
    #     topics.append({"topic": "location", "value": "mentioned", "timestamp": datetime.now().isoformat()})

    return topics

def update_conversation(user_id, user_msg, bot_msg):
    session_data = get_user_session(user_id)
    if not session_data:
        return False

    session_data["l"] = datetime.now().isoformat()
    session_data["c"].append([user_msg, bot_msg])
    if len(session_data["c"]) > 8: # Keep last 8
        session_data["c"].pop(0)

    # Extract and store topics
    new_topics = extract_topics(user_msg)
    if new_topics:
        session_data["t"].extend(new_topics)
        # Keep only recent topics (e.g., last 10 minutes)
        now = datetime.now()
        filtered_topics = []
        for topic in session_data["t"]:
            try:
                topic_time = datetime.fromisoformat(topic["timestamp"])
                if now - topic_time < timedelta(minutes=10):
                    filtered_topics.append(topic)
            except:
                pass # Ignore invalid timestamps
        session_data["t"] = filtered_topics[-5:] # Keep max 5 recent topics

    return save_user_session(user_id, session_data)

# 🧠 Enhanced context with topics
def get_context(user_id):
    session_data = get_user_session(user_id)
    if not session_data:
        return ""

    context_lines = ["\nPrevious Conversation:"]
    for user_text, bot_text in session_data["c"][-4:]: # Last 4 exchanges
        context_lines.append(f"U: {user_text}")
        context_lines.append(f"A: {bot_text}")

    # Add recent topics
    if session_data.get("t"):
        context_lines.append("\nRecently Discussed Topics:")
        for topic_info in session_data["t"][-3:]: # Last 3 topics
             context_lines.append(f"- {topic_info['topic']}: {topic_info['value']}")

    return "\n".join(context_lines)

# 🧠 Should respond
def should_respond(update: Update):
    if not update.message:
        return False, "no_message"
    if update.effective_chat.type == "private":
        return True, "private"
    message = update.message
    if message.text:
        text = message.text.lower()
        if BOT_USERNAME.lower() in text:
            return True, "mention"
        if message.reply_to_message and message.reply_to_message.from_user.id == message._bot.id:
            return True, "reply"
        if random.randint(1, 100) <= 20:
            return True, "random"
    elif message.sticker or message.photo:
        if random.randint(1, 100) <= 10:
            return True, "media"
    return False, "no_response"

# 🎭 Meme response
def get_meme_response():
    responses = [
        "😂 Mast sticker! 😆", "🤣 Hilarious! 😂", "😆 Mazaak chal raha? 😄",
        "🤪 Creative! 👏", "😹 LOL! 😂😂", "🤓 Interesting! 😎",
        "😇 Cute! 😊", "🔥 Trendy! 🔥"
    ]
    return random.choice(responses)

# 💬 Handle text
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text.strip()
    clean_msg = user_message.replace(BOT_USERNAME, "").replace(BOT_USERNAME.lower(), "").strip()

    abusive_words = ['mah', 'bhen', 'chut', 'lund', 'gaand', 'madar', 'bhosdi', 'chutiya', 'bsdk']
    if any(word in user_message.lower() for word in abusive_words) and random.randint(1, 100) <= 70:
        reply = random.choice(get_sexy_gali_responses())
        await update.message.reply_text(reply)
        update_conversation(user.id, user_message, reply)
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        context_text = get_context(user.id)
        prompt = f"""{get_personality_prompt(user.first_name)}

{context_text}

Current message:
U: {clean_msg}
A (Remember context and topics discussed):"""

        response_text, status = await call_gemini_with_fallback(prompt)

        if status == "success" and response_text:
            reply = response_text
            if len(reply) > 250:
                reply = reply[:247] + "..."
        elif status == "all_keys_failed":
            replies = [
                "😔 baby yaar abhi mummy hai  isliye bat ni kar sakti kal karti messge ",
                "💔 yaar mummy hai !",
                "😌 ruk ja thode  der mummuy hai ",
                "😪 Abhi koi available nahi hai... kal ana!"
            ]
            reply = random.choice(replies)
        else:
            replies = [
                "😅 Kya bol rahe ho? Clear batao!",
                "😊 Samajh nahi aaya... phir se?",
                "😄 Interesting! Aur kya?",
                "🤔 Thoda sahi likho na!",
                "😘 Flirt karna chahte ho?"
            ]
            reply = random.choice(replies)

    except Exception as e:
        print(f"Unexpected Error: {e}")
        reply = "💔 lagta hai  bukhar hai  isliye  sorry 😔"

    await update.message.reply_text(reply)
    # Update conversation memory *after* sending reply
    update_conversation(user.id, user_message, reply)

# 🖼️ Handle media
async def handle_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reply = get_meme_response()
    await update.message.reply_text(reply)
    update_conversation(user.id, "[media]", reply)

# 💬 Main handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clean_expired_sessions()
    should_respond_result, response_type = should_respond(update)
    if not should_respond_result:
        if random.randint(1, 100) <= 1:
            should_respond_result = True
        else:
            return
    if update.message.text:
        await handle_text_message(update, context)
    elif update.message.sticker or update.message.photo:
        await handle_media_message(update, context)

# 🚀 Commands
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Photo? Shy feel! 😳")

async def pic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎨 Photo nahi ho sakti! 😉")

# 🚀 Start bot
def main():
    if not initialize_gemini():
        print("❌ Failed to initialize any API key!")
        return

    TOKEN = "7297293035:AAHgIV4q_dtaLIDC5X7ATQU0RTczB2VRGzI" # <-- YOUR NEW BOT TOKEN HERE
    global BOT_USERNAME
    BOT_USERNAME = "@anaya777bot"

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("pic", pic))
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.Sticker.ALL | filters.PHOTO) & ~filters.COMMAND,
        handle_message
    ))

    print("💕 Anaya Multi-API Bot (Enhanced Memory) Starting...")
    app.run_polling()

if __name__ == '__main__':

    main()
