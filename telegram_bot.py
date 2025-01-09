from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from generation_agent import VideoGenerationAgent
import os
from dotenv import load_dotenv
import asyncio
from collections import deque

load_dotenv()
# print(os.getenv("TELEGRAM_BOT_TOKEN"))

class VideoGenerationBot:
    def __init__(self):
        self.agent = VideoGenerationAgent()
        self.processing_queue = deque()  # Queue to store pending requests
        self.is_processing = False
        self.lock = asyncio.Lock()  # Add lock for thread safety
        self.pending_users = set()  # Add set to track users with pending requests
        self.user_messages = {}  # Store last status message for each user
        self.update_task = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        await update.message.reply_text(
            "Hi! I'm AIMotion. Tell me what kind of dance video you want to create. "
            "For example: 'Create a video where pepe is dancing hiphop'"
        )

    async def update_queue_positions(self):
        """Periodically update queue positions for all waiting users"""
        while True:
            try:
                for update, context in self.processing_queue:
                    user_id = update.message.from_user.id
                    position = list(self.processing_queue).index((update, context)) + 1
                    
                    # Get the previous status message
                    prev_message = self.user_messages.get(user_id)
                    
                    # Create new status message
                    new_text = (f"⏳ Your request is in queue.\n"
                              f"Current position: {position}\n"
                              f"Estimated wait time: {position * 1.5} minutes")
                    
                    # Update or send new message
                    if prev_message:
                        try:
                            await prev_message.edit_text(new_text)
                        except Exception:
                            # If editing fails (message too old), send new message
                            new_message = await update.message.reply_text(new_text)
                            self.user_messages[user_id] = new_message
                    else:
                        new_message = await update.message.reply_text(new_text)
                        self.user_messages[user_id] = new_message
                        
            except Exception as e:
                print(f"Error updating queue positions: {e}")
                
            await asyncio.sleep(30)  # Update every 30 seconds

    async def process_queue(self):
        """Process requests in the queue"""
        while self.processing_queue:
            update, context = self.processing_queue.popleft()
            user_id = update.message.from_user.id
            self.is_processing = True
            
            try:
                if user_id in self.user_messages:
                    try:
                        await self.user_messages[user_id].delete()
                    except Exception:
                        pass  # Message might be too old to delete
                    del self.user_messages[user_id]

                await update.message.reply_text("🎬 Starting to generate your video...")
                
                # Call the VideoGenerationAgent
                result = self.agent.run(update.message.text)
                
                # Get the generated video path from the result
                video_path = os.path.join(os.getenv("DATABASE_DIR"), "generated_videos", result)
                
                # Send the video back to the user
                if os.path.exists(video_path):
                    await update.message.reply_video(video=open(video_path, 'rb'))
                else:
                    await update.message.reply_text("Sorry, there was an error generating your video.")
                    
            except Exception as e:
                await update.message.reply_text(f"An error occurred: {str(e)}")
            finally:
                # Remove user from pending set after processing
                self.pending_users.remove(user_id)
            
        self.is_processing = False

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        await update.message.reply_text(
            "Just send me a description of the dance video you want to create. "
            "Include details like who should be dancing and what style of dance."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages and generate videos."""
        user_id = update.message.from_user.id
        
        if user_id in self.pending_users:
            await update.message.reply_text(
                "You already have a pending request. Please wait for it to complete before submitting another one."
            )
            return

        async with self.lock:
            queue_position = len(self.processing_queue) + (1 if self.is_processing else 0)
            
            if queue_position == 0:
                await update.message.reply_text("Processing your request... This may take a few minutes.")
            else:
                status_message = await update.message.reply_text(
                    f"⏳ Your request is in queue.\n"
                    f"Current position: {queue_position}\n"
                    f"Estimated wait time: {queue_position * 1.5} minutes"
                )
                self.user_messages[user_id] = status_message
            
            self.processing_queue.append((update, context))
            self.pending_users.add(user_id)
            
            # Start the update task if it's not running
            if not self.update_task:
                self.update_task = asyncio.create_task(self.update_queue_positions())
            
            if not self.is_processing:
                asyncio.create_task(self.process_queue())

    def run(self):
        """Start the bot."""
        # Create the Application and pass it your bot's token
        # print(os.getenv("TELEGRAM_BOT_TOKEN"))
        application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Start the bot
        print("Starting bot...")
        application.run_polling()

if __name__ == '__main__':
    bot = VideoGenerationBot()
    bot.run()