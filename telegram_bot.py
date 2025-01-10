from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Message
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from generation_agent import VideoGenerationAgent, SharedConnections
import os
from dotenv import load_dotenv
import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import time

load_dotenv()
# print(os.getenv("TELEGRAM_BOT_TOKEN"))

class VideoGenerationBot:
    def __init__(self, num_agents: int = 2):
        SharedConnections()
        self.agent_pool = [VideoGenerationAgent() for _ in range(num_agents)]
        self.available_agents = deque(self.agent_pool)  # Queue of available agents
        self.agent_lock = asyncio.Lock()  # Lock for agent pool access
        self.processing_queue = deque()
        self.pending_users = set()
        self.user_messages = {}
        self.update_task = None
        self.max_concurrent_tasks = num_agents
        self.active_tasks = 0
        self.executor = ThreadPoolExecutor(max_workers=num_agents)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        keyboard = [
            ["/start - Start the bot"],
            ["/help - Learn how to use the bot"],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "👋 Hi! I'm AIMotion. I can create dance videos based on your descriptions.\n\n"
            "Use the menu below or type /help to see the instructions!",
            reply_markup=reply_markup
        )

    async def get_available_agent(self):
        """Get an available agent from the pool"""
        async with self.agent_lock:
            if self.available_agents:
                return self.available_agents.popleft()
            return None
        
    async def process_single_request(self, update, context):
        """Process a single request with an available agent"""
        user_id = update.message.from_user.id
        
        try:
            agent = await self.get_available_agent()
            if not agent:
                return  # No available agent, request stays in queue
            
            if user_id in self.user_messages:
                try:
                    await self.user_messages[user_id].delete()
                except Exception:
                    pass
                del self.user_messages[user_id]

            await update.message.reply_text("🎬 Starting to generate your video...")
            
            # Run the agent in a thread pool to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                agent.run,
                update.message.text
            )
            
            video_path = os.path.join(os.getenv("DATABASE_DIR"), "generated_videos", result)
            
            if os.path.exists(video_path):
                await update.message.reply_video(video=open(video_path, 'rb'))
            else:
                await update.message.reply_text("Sorry, there was an error generating your video.")
                
        except Exception as e:
            await update.message.reply_text(f"An error occurred: {str(e)}")
        finally:
            if agent:
                await self.return_agent(agent)
            self.pending_users.remove(user_id)
            async with self.agent_lock:
                self.active_tasks -= 1

    async def return_agent(self, agent):
        """Return an agent to the pool"""
        async with self.agent_lock:
            self.available_agents.append(agent)    

    async def update_queue_positions(self):
        """Periodically update queue positions for all waiting users"""
        while True:
            try:
                # Create a copy of the queue for iteration
                async with self.agent_lock:
                    queue_copy = list(self.processing_queue)
                
                for update, context in queue_copy:
                    user_id = update.message.from_user.id
                    position = list(self.processing_queue).index((update, context)) + 1
                    
                    # Calculate more accurate wait time based on active agents
                    estimated_wait = (position / len(self.agent_pool)) * 1.5  # 1.5 minutes per video
                    
                    new_text = (f"⏳ Your request is in queue.\n"
                              f"Current position: {position}\n"
                              f"Estimated wait time: {estimated_wait:.1f} minutes")
                    
                    # Get the previous status message
                    prev_message = self.user_messages.get(user_id)
                    
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
        """Process multiple requests simultaneously using the agent pool"""
        while self.processing_queue:
            async with self.agent_lock:
                if self.active_tasks >= self.max_concurrent_tasks:
                    await asyncio.sleep(1)  # Wait if all agents are busy
                    continue
                
                self.active_tasks += 1
                update, context = self.processing_queue.popleft()
                
                # Start processing this request
                asyncio.create_task(self.process_single_request(update, context))

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        help_text = (
            "🤖 Here's how to use me:\n\n"
            "1️⃣ Simply describe the dance video you want to create\n"
            "2️⃣ Include details like:\n"
            "   • Who should be dancing\n"
            "   • What style of dance\n"
            "   • Any specific settings or movements\n\n"
            "🎯 Try this example \\(click to copy\\):\n"
            "`Create a video where pepe is dancing hip hop`"
        )

        try:
            await update.message.reply_text(help_text, parse_mode='MarkdownV2')
        except Exception as e:
            print(f"Error sending help message: {e}")
            # Fallback without markdown
            await update.message.reply_text(help_text.replace('\\', ''))


    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages and generate videos."""
        user_id = update.message.from_user.id
        username = update.message.from_user.username
        print(f"user_id: {user_id}, username: {username}")

        if user_id in self.pending_users:
            await update.message.reply_text(
                "You already have a pending request. Please wait for it to complete before submitting another one."
            )
            return

        async with self.agent_lock:
            queue_position = len(self.processing_queue)
            
            # Only add to pending_users if we successfully add to queue
            self.processing_queue.append((update, context))
            self.pending_users.add(user_id)            
            print(f"pending_users: {self.pending_users}")

            if queue_position < len(self.available_agents):
                await update.message.reply_text("Processing your request... This may take a few minutes.")
            else:
                status_message = await update.message.reply_text(
                    f"⏳ Your request is in queue.\n"
                    f"Current position: {queue_position + 1}\n"
                    f"Active generators: {len(self.available_agents)}/{self.max_concurrent_tasks}\n"
                    f"Estimated wait time: {((queue_position + 1) / len(self.agent_pool)) * 1.5:.1f} minutes"
                )
                self.user_messages[user_id] = status_message
            
            # Start the update task if it's not running
            if not self.update_task:
                self.update_task = asyncio.create_task(self.update_queue_positions())
            
            # Start processing if we have available agents
            asyncio.create_task(self.process_queue())


    def run(self):
        """Start the bot."""
        application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        print("Starting bot...")
        application.run_polling()

if __name__ == '__main__':
    bot = VideoGenerationBot()
    bot.run()