from typing import Callable, Any
from swarms import Agent
from swarm_models import OpenAIChat
from dotenv import load_dotenv
import os
import json
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

    
    def run(self, task: str):
        """
        Run the agent on a task.
        """

        # step 1: get requirements for dance video generation from user input
        requirements = super().run(task)
        if type(requirements) == str:
            requirements = json.loads(requirements)
        
        print("Get requirements: ", requirements)

        # step 2: search database for dance videos that match the requirements

        return requirements
        

if __name__ == "__main__":
    agent = VideoGenerationAgent()
    out = agent.run("Create a video where pepe is dancing hiphop")
    print(out)
