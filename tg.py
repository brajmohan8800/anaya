import random
import google.generativeai as genai
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os
from datetime import datetime, timedelta
import traceback

# 🔐 Multiple Gemini API Keys
API_KEYS = [
    "AIzaSyCtzkhcb4iOUWwLIcQRLoqVLVQhAERMvvs",
    "AIzaSyBFNZzb9q7uAs2JytlF3nzcK-XiXhUQWJg",
    "AIzaSyCSQTADI5-vZ5NIv3jX-eS1nLq2uJQZb44",
    "AIzaSyDF60wPcFeoQGPO5z3K7zhMP7w-RSY8VrI",
    "AIzaSyCK6ZkPpqXr8cP2e4EOyRbOdYqXvTWcVDo",
    "AIzaSyBBvISoxS9VW7u16uaBZf8qP-dzLqvbHhE",
    "AIzaSyDBZ9WJyivCij2tMYAviiJBf6yZfhG9NJE",
    "AIzaSyCJgNgOy9fDyXjrGCfA-Y8sZwj-rV2Zd4k",
    "AIzaSyD8AnVqXzrLxH710phQJx9BJxMqmnRSCFs",
    "AIzaSyCpLFbNnctlVARz6lqseGGQh66TWaV6dq4",
    "AIzaSyAXHLOw7tcucO2ODu0IlNLi6ZMgAMzMClw",
    "AIzaSyAFiOShLQW_0VnX7NWk0jrletJcsqGrPXA",
    "AIzaSyDbfmg-hTNP_xpIVAsXeAUzEG0-FZ-rsdA",
    "AIzaSyAaA9fn5LEwexeuSwzBIY0_OvC9z6BetEY",
    "AIzaSyDNmTX9KCM5Jb7jiMtKNzSrKwn57HDsI-w"
]

# 🔄 Current API key management
current_api_index = 0
model = None

# 🔄 Initialize with first API key
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

# 🔄 Switch to next API key
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

# 🧠 Call Gemini with fallback support
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
            
            # Check if quota/limit error
            if "quota" in error_msg or "limit" in error_msg:
                print(f"⚠️ API Key #{current_api_index + 1} limit reached. Switching...")
                if switch_api_key():
                    attempts += 1
                    continue
                else:
                    break
            else:
                # Other errors (network, timeout, etc.)
                print(f"⚠️ API Error with Key #{current_api_index + 1}: {e}")
                return None, "api_error"
    
    return None, "all_keys_failed"

# 🤖 Bot username
BOT_USERNAME = "@anaya777bot"

# 📁 Create sessions directory
os.makedirs("sessions", exist_ok=True)

# 🔥 Sexy and gali responses
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

# 🧠 Hinglish personality
def get_personality_prompt(user_name):
    return f"""You are Anaya, ek bold aur confident girl ho jo {user_name} se baat kar rahi ho.
- Hinglish use karo (mix of Hindi-English)
- Emojis use karo 😊 😳 😉
- Flirt karo jab appropriate ho
- Gali de sakti ho jab required ho
- Short responses do (1-2 lines)
- Natural aur real behave karo
- Context maintain karo - pichli baat yaad rakhna"""

# 👋 Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    user = update.effective_user
    session_file = f"sessions/{user.id}.json"
    
    # Create minimal session
    session_data = {
        "c": [],  # conversations
        "l": datetime.now().isoformat()  # last_active
    }
    
    # Save session (agar file nahi hai to create karega)
    import os, json
    os.makedirs("sessions", exist_ok=True)
    with open(session_file, "w") as f:
        json.dump(session_data, f)

    # Buttons
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/+P-JiGcEHsDU0NWU1")],
        [InlineKeyboardButton("💬 Support", url="")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Welcome message
    await update.message.reply_text(
        f"👋 Welcome, {user.first_name}!\n\n"
        "This is your personal Telegram bot.\n"
        "Use the buttons below to connect with us ⬇️",
        reply_markup=reply_markup
    )

    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False)
    
    msg = f"Hey {user.first_name}! 👋\nMain Anaya hoon...\nKya chal raha hai? 😊"
    await update.message.reply_text(msg)

# 🧠 Get user session
def get_user_session(user_id):
    session_file = f"sessions/{user_id}.json"
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

# 🧠 Save user session
def save_user_session(user_id, session_data):
    session_file = f"sessions/{user_id}.json"
    try:
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False)
        return True
    except:
        return False

# 🧠 Clean expired sessions (5 minutes)
def clean_expired_sessions():
    now = datetime.now()
    expired_files = []
    
    for filename in os.listdir("sessions"):
        if filename.endswith(".json"):
            filepath = os.path.join("sessions", filename)
            try:
                # Check last active time
                with open(filepath, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                last_active = datetime.fromisoformat(session_data["l"])
                if now - last_active > timedelta(minutes=5):
                    expired_files.append(filepath)
            except:
                expired_files.append(filepath)
    
    # Remove expired sessions
    for filepath in expired_files:
        try:
            os.remove(filepath)
        except:
            pass

# 🧠 Update conversation (minimal) - FIXED TYPO
def update_conversation(user_id, user_msg, bot_msg):
    session_data = get_user_session(user_id)
    if not session_data:  # ✅ Fixed typo
        return False
    
    # Update last active
    session_data["l"] = datetime.now().isoformat()
    
    # Add conversation (max 8)
    session_data["c"].append([user_msg, bot_msg])
    if len(session_data["c"]) > 8:
        session_data["c"].pop(0)
    
    return save_user_session(user_id, session_data)

# 🧠 Get context (minimal)
def get_context(user_id):
    session_data = get_user_session(user_id)
    if not session_data or not session_data["c"]:
        return ""
    
    context = "\n"
    for user_text, bot_text in session_data["c"][-4:]:  # Last 4
        context += f"U: {user_text}\nA: {bot_text}\n"
    
    return context

# 🧠 Should respond
def should_respond(update: Update):
    if not update.message:
        return False, "no_message"
    
    # Private chat - always respond
    if update.effective_chat.type == "private":
        return True, "private"
    
    message = update.message
    
    # Text message checks
    if message.text:
        text = message.text.lower()
        # Mention
        if BOT_USERNAME.lower() in text:
            return True, "mention"
        # Reply
        if message.reply_to_message and message.reply_to_message.from_user.id == message._bot.id:
            return True, "reply"
        # Random chance
        if random.randint(1, 100) <= 20:
            return True, "random"
    
    # Media message - 10% chance
    elif message.sticker or message.photo:
        if random.randint(1, 100) <= 10:
            return True, "media"
    
    return False, "no_response"

# 🎭 Get meme response
def get_meme_response():
    responses = [
        "😂 Mast sticker! 😆",
        "🤣 Hilarious! 😂",
        "😆 Mazaak chal raha hai? 😄",
        "🤪 Creative! 👏",
        "😹 LOL! 😂😂",
        "🤓 Interesting! 😎",
        "😇 Cute! 😊",
        "🔥 Trendy! 🔥"
    ]
    return random.choice(responses)

# 💬 Handle text messages with improved error handling
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text.strip()
    
    # Remove bot mention
    clean_msg = user_message.replace(BOT_USERNAME, "").replace(BOT_USERNAME.lower(), "").strip()
    
    # Abusive check
    abusive_words = ['mah', 'bhen', 'chut', 'lund', 'gaand', 'madar', 'bhosdi', 'chutiya', 'bsdk']
    if any(word in user_message.lower() for word in abusive_words) and random.randint(1, 100) <= 70:
        reply = random.choice(get_sexy_gali_responses())
        await update.message.reply_text(reply)
        update_conversation(user.id, user_message, reply)
        return
    
    # Typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    try:
        # Get context
        context_text = get_context(user.id)
        
        # Build prompt
        prompt = f"""{get_personality_prompt(user.first_name)}

{context_text}

Current:
U: {clean_msg}
A:"""
        
        # Call API with fallback support
        response_text, status = await call_gemini_with_fallback(prompt)
        
        if status == "success" and response_text:
            reply = response_text
            if len(reply) > 250:
                reply = reply[:247] + "..."
        elif status == "all_keys_failed":
            # When all API keys are exhausted
            replies = [
                "😔 Sab API keys khatam ho gayi hain... kal fir try karo!",
                "💔 Free quota khatam... kal fresh keys milengi!",
                "😌 Thodi der休憩 karo... API rest pe hai!",
                "😪 Abhi koi key available nahi hai... kal ana!"
            ]
            reply = random.choice(replies)
        else:
            # Other fallback responses
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
        reply = "💔 Technical issue... sorry! 😔"
    
    await update.message.reply_text(reply)
    update_conversation(user.id, user_message, reply)

# 🖼️ Handle media messages
async def handle_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reply = get_meme_response()
    await update.message.reply_text(reply)
    update_conversation(user.id, "[media]", reply)

# 💬 Main message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clean expired sessions
    clean_expired_sessions()
    
    # Check if should respond
    should_respond_result, response_type = should_respond(update)
    
    if not should_respond_result:
        if random.randint(1, 100) <= 1:
            should_respond_result = True
        else:
            return
    
    # Handle based on message type
    if update.message.text:
        await handle_text_message(update, context)
    elif update.message.sticker or update.message.photo:
        await handle_media_message(update, context)

# 🚀 Bot commands
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Photo? Shy feel! 😳")

async def pic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎨 Photo nahi ho sakti! 😉")

# 🚀 Start bot
def main():
    # Initialize Gemini
    if not initialize_gemini():
        print("❌ Failed to initialize any API key!")
        return
    
    TOKEN = "8322806895:AAEntwL5uC4RPStsha3odUWBtVwv-a4RpA4"
    global BOT_USERNAME
    BOT_USERNAME = "@anaya777bot"
    
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("pic", pic))
    
    # Message handlers
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.Sticker.ALL | filters.PHOTO) & ~filters.COMMAND, 
        handle_message
    ))
    
    print("💕 Anaya Multi-API Bot Starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
