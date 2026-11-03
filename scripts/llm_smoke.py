import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.core.llm_wrapper import chat, last_provider

if __name__ == "__main__":
    prompt = "Say hi in Hindi and Odia"
    print(f"Prompt: {prompt}")
    reply = chat(prompt)
    print(f"Provider used: {last_provider()}")
    print("Response:")
    print(reply)

