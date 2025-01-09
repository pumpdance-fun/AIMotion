from typing import Callable, Any
from swarms import Agent
from swarm_models import OpenAIChat
from dotenv import load_dotenv
import os
import json
from database import ChromaDatabase
from generation_client import VideoGenerationClient

load_dotenv()

SYSTEM_PROMPT = "Your task is to analyze user's input to identify the requirements for the following dance video generation task. Based on the user input, you need to analyze and extract key information including the subject (dancer), dance name if mentioned, dance style if mentioned, and other mentioned requirements. Once extract all information, output them in a json format."


class VideoGenerationAgent(Agent):
    """
    VideoGenerationAgent is an agent that can generate videos based on user's input.
    """
    def __init__(self, name: str = "Video-Generation-Agent", system_prompt: str = SYSTEM_PROMPT, model_name: str = "gpt-4o-mini", description: str = None, llm: Callable = None):
        """
        Initialize the custom agent.

        Args:
            name (str): The name of the agent.
            system_prompt (str): The prompt guiding the agent.
            model_name (str): The name of your model can use litellm [openai/gpt-4o]
            description (str): A description of the agent's purpose.
            llm (Callable, optional): A callable representing the language model to use.
        """

        if model_name == "gpt-4o-mini":
            llm = OpenAIChat(
                openai_api_key=os.getenv("OPENAI_API_KEY"), model_name="gpt-4o-mini", temperature=0.1
            )
        super().__init__(agent_name=name, system_prompt=system_prompt, model_name=model_name, llm=llm)
        self.description = description
        self.db = ChromaDatabase()
        self.video_generation_client = VideoGenerationClient()
    def run(self, task: str):
        """
        Run the agent on a task.
        """

        # step 1: get requirements for dance video generation from user input
        requirements = super().run(task)
        if type(requirements) == str:
            requirements = requirements.replace("```json", "").replace("```", "")
            requirements = json.loads(requirements)
        
        print("Get requirements: ", requirements)

        # step 2: search database for dance videos that match the requirements
        query_text = ""

        if requirements.get("dance_name"):
            query_text += requirements["dance_name"]
        if requirements.get("style"):
            query_text += " " + requirements["style"]
        # todo: add other requirements into query text

        video_path = self.db.query_dances(
            collection_name="dance_videos",
            query_texts=[query_text],
        )[0].file_path

        print("Search results for existing video: ", video_path)

        # step 3: search database for images that match the requirements
        query_text = requirements.get("subject")
        image_path = self.db.query_images(
            collection_name="token_images",
            query_texts=[query_text],
        )[0].file_path
        print("Search results for existing images: ", image_path)

        # step 4: call external tools or API to generate video
        task_id = self.video_generation_client.submit_task(
            image_path,
            video_path,
            os.path.join(os.getenv("DATABASE_DIR"), "generated_videos")
        )
        print("Submitted task: ", task_id)
        # Wait for result
        result = self.video_generation_client.get_result(task_id, timeout=300)  # 5 minute timeout
        if result:
            print(f"Task completed: {result}")
            return result["output_path"]
        else:
            print("Task timed out")
            raise Exception("Video generation timed out")
        

if __name__ == "__main__":
    agent = VideoGenerationAgent()
    agent.run("Create a video where pepe is dancing hiphop")

