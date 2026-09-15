import os
from pyrogram import Client, filters
from pymongo import MongoClient

# Environment Variables से डेटा उठाना
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")
BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL"))

# Telegram और MongoDB कनेक्ट करना
app = Client("forward_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["tg_bot_db"]
files_collection = db["saved_files"]

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("नमस्ते! मैं तैयार हूँ। ग्रुप में मूवी/एनिमे का नाम लिखें, मैं फाइल ढूंढ कर दूंगा।")

# डेटाबेस चैनल में कोई नई फाइल आए तो उसका नाम और आईडी सेव करना
@app.on_message(filters.chat(BIN_CHANNEL) & (filters.document | filters.video))
async def save_file(client, message):
    file_name = ""
    if message.document:
        file_name = message.document.file_name.lower()
    elif message.video:
        file_name = (message.caption or "video").lower()
        
    if file_name:
        files_collection.update_one(
            {"message_id": message.id},
            {"$set": {"file_name": file_name, "message_id": message.id}},
            upsert=True
        )

# ग्रुप में कोई नाम लिखे तो फाइल ढूंढ कर फॉरवर्ड करना
@app.on_message(filters.group & filters.text)
async def search_and_forward(client, message):
    query = message.text.lower()
    if len(query) < 3:
        return
        
    result = files_collection.find_one({"file_name": {"$regex": query}})
    
    if result:
        try:
            await client.forward_messages(
                chat_id=message.chat.id,
                from_chat_id=BIN_CHANNEL,
                message_ids=result["message_id"]
            )
        except Exception as e:
            await message.reply_text(f"फाइल भेजने में एरर आया: {e}")
    else:
        # अगर डेटाबेस में फाइल न मिले तो कोई मैसेज न भेजें या अलर्ट दें
        pass

if __name__ == "__main__":
    app.run()
  
