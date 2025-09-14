#!/usr/bin/env python3
"""
Small CLI tool to test AI provider responses
"""

import os
import sys
import argparse
import json
import time

try:
    import requests
    from requests.exceptions import RequestException, Timeout
except ImportError:
    print("ERROR: 'requests' library is not installed. Please install it with 'pip install requests'")
    sys.exit(1)

def _post_with_retries(url, headers, json_data, timeout=30, max_retries=3, backoff_base=1.5):
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            if 500 <= resp.status_code < 600:
                last_exc = Exception(f"Server error {resp.status_code}")
            else:
                return resp
        except (RequestException, Timeout) as e:
            last_exc = e
        if attempt < max_retries:
            wait = backoff_base ** attempt
            print(f"Attempt {attempt} failed, retrying in {wait:.1f}s...")
            time.sleep(wait)
    raise Exception(f"HTTP request failed after {max_retries} attempts: {last_exc}")

def call_openai(api_key, model, prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    resp = _post_with_retries(url, headers, data, timeout=30, max_retries=3)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text

def call_gemini(api_key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    resp = _post_with_retries(url, headers, data, timeout=30, max_retries=3)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text

def call_anthropic(api_key, model, prompt):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": model,
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }
    resp = _post_with_retries(url, headers, data, timeout=30, max_retries=3)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text

def call_cohere(api_key, model, prompt):
    url = "https://api.cohere.com/v1/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "message": prompt,
        "max_tokens": 1000
    }
    resp = _post_with_retries(url, headers, data, timeout=30, max_retries=3)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text
    
def call_xai(api_key, model, prompt):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    resp = _post_with_retries(url, headers, data, timeout=30, max_retries=3)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text

def extract_ai_response(company, status, resp):
    if status != 200:
        return f"API Error (Status {status}): {resp}"
    if not isinstance(resp, dict):
        return f"Unexpected response format: {resp}"
    try:
        if company == "OpenAI":
            if "choices" in resp and len(resp["choices"]) > 0:
                choice = resp["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
            return f"Could not extract OpenAI response: {resp}"
        elif company == "Google":
            if "candidates" in resp and len(resp["candidates"]) > 0:
                candidate = resp["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"]
            return f"Could not extract Google response: {resp}"
        elif company == "Anthropic":
            if "content" in resp and len(resp["content"]) > 0:
                content = resp["content"][0]
                if "text" in content:
                    return content["text"]
            return f"Could not extract Anthropic response: {resp}"
        elif company == "Cohere":
            if "text" in resp:
                return resp["text"]
            return f"Could not extract Cohere response: {resp}"
        return f"Unknown company format: {resp}"
    except Exception as e:
        return f"Error extracting response: {e} - Raw: {resp}"

def main():
    parser = argparse.ArgumentParser(description="Test AI API calls and show responses")
    parser.add_argument("--company", choices=["OpenAI", "Google", "Anthropic", "Cohere"], default="OpenAI")
    parser.add_argument("--key", help="API key")
    parser.add_argument("--model", help="Model to use")
    parser.add_argument("--prompt", default="Explain how AI works in a few words")
    parser.add_argument("--raw", action="store_true", help="Show only raw JSON response")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    api_key = (args.key or os.environ.get("AI_API_KEY") or os.environ.get("OPENAI_API_KEY") or
               os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("COHERE_API_KEY"))

    if not api_key:
        print("ERROR: No API key provided. Use --key or environment variable.")
        return 1

    default_models = {
        "OpenAI": "gpt-3.5-turbo",
        "Google": "gemini-2.0-flash",
        "Anthropic": "claude-3-sonnet-20240229",
        "Cohere": "command-r"
    }
    model = args.model or default_models.get(args.company, "default")

    try:
        if args.company == "OpenAI":
            status, resp = call_openai(api_key, model, args.prompt)
        elif args.company == "Google":
            status, resp = call_gemini(api_key, model, args.prompt)
        elif args.company == "Anthropic":
            status, resp = call_anthropic(api_key, model, args.prompt)
        elif args.company == "Cohere":
            status, resp = call_cohere(api_key, model, args.prompt)
        else:
            print(f"ERROR: Unsupported company: {args.company}")
            return 1

        if args.raw:
            if isinstance(resp, (dict, list)):
                print(json.dumps(resp, indent=2, ensure_ascii=False))
            else:
                print(resp)
        else:
            ai_text = extract_ai_response(args.company, status, resp)
            print(ai_text)
            if status != 200 and args.verbose:
                if isinstance(resp, (dict, list)):
                    print(json.dumps(resp, indent=2, ensure_ascii=False))
                else:
                    print(resp)
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
