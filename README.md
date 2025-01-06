# AIMotion

The AIMotion project from Pump Dance is a collection of AI agents to generate funny and interesting video content.

## Architecture
![AIMotion Architecture](./assets/aimotion_arch.png)

AIMotion is built on top of the Swarms framework. 

+ Media agents are responsible for monitoring social media platforms to save and learn interesting content.
+ Task agent is the front end to interact with the user and generate tasks for the generation agents. It also integrates with the media agents to get the hot spot topics on social media and generate tasks based on that.
+ Generation agents are responsible for generating video content based on the saved content by autonomously selecting suitable content and generation techniques.

