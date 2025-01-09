from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from generation_agent import VideoGenerationAgent
import os
from dotenv import load_dotenv

load_dotenv()
print(os.getenv("TELEGRAM_BOT_TOKEN"))

class VideoGenerationBot:
    def __init__(self):
        self.agent = VideoGenerationAgent()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        await update.message.reply_text(
            "Hi! I'm AIMotion. Tell me what kind of dance video you want to create. "
            "For example: 'Create a video where pepe is dancing hiphop'"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        await update.message.reply_text(
            "Just send me a description of the dance video you want to create. "
            "Include details like who should be dancing and what style of dance."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages and generate videos."""
        await update.message.reply_text("Processing your request... This may take a few minutes.")
        
        try:
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

    def run(self):
        """Start the bot."""
        # Create the Application and pass it your bot's token
        print(os.getenv("TELEGRAM_BOT_TOKEN"))
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