import requests


def call_gemini(api_key, model, prompt, chat_history=None, max_tokens=1000, temperature=0.7, retries=2, timeout=10):
    """
    Call Google Gemini API (Google AI Studio) and return the response text.
    If chat_history is provided, it will be formatted for context.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    if chat_history:
        # Format chat history for Gemini
        parts = []
        for msg in chat_history[-10:]:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            if role == "user":
                parts.append(f"User: {text}")
            elif role == "assistant":
                parts.append(f"Assistant: {text}")
        prompt_text = "\n".join(parts) if parts else prompt
    else:
        prompt_text = prompt
    data = {
        "contents": [
            {"parts": [{"text": prompt_text}]}
        ]
    }
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            print(f"[Gemini] Attempt {attempt} sending request...")
            resp = requests.post(url, headers=headers, json=data, timeout=timeout)
            result = resp.json()
            if resp.status_code == 200:
                print("[Gemini] Success.")
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                print(f"[Gemini] API error: {error_msg}")
                last_exc = Exception(f"Google Gemini API error: {error_msg}")
        except Exception as e:
            print(f"[Gemini] Exception: {e}")
            last_exc = e
        if attempt < retries:
            import time
            wait = 1.5 ** attempt
            print(f"[Gemini] Waiting {wait:.1f}s before retry...")
            time.sleep(wait)
    raise last_exc if last_exc else Exception("Unknown Gemini API error")
