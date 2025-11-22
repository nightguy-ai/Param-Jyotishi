# src/agent.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from src.instructions import SYSTEM_INSTRUCTION
from src.tools import tools_list, tool_map

# Load Environment Variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=api_key)

class AstrologyAgent:
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name='gemini-3-pro-preview', # Use Pro for complex reasoning
            tools=tools_list,
            system_instruction=SYSTEM_INSTRUCTION,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        # Initialize chat with automatic function calling enabled
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)

    def send_message(self, user_input):
        try:
            # The SDK handles the tool execution loop internally now!
            response = self.chat.send_message(user_input)
            return response.text
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def reset(self):
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)
