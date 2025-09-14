"""
ChatGPT.py - Simple OpenAI ChatGPT API wrapper for Hyggshi OS Code Mini
"""

import requests

class ChatGPTClient:
    def __init__(self, api_key, model="gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def chat(self, messages, max_tokens=1000, temperature=0.7):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        resp = requests.post(self.api_url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        return result["choices"][0]["message"]["content"].strip()

# Example usage:
if __name__ == "__main__":
    # Replace with your OpenAI API key
    api_key = "sk-..."
    client = ChatGPTClient(api_key)
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, who are you?"}
    ]
    try:
        reply = client.chat(messages)
        print("ChatGPT:", reply)
    except Exception as e:
        print("Error:", e)
