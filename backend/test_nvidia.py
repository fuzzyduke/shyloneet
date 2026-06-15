import os
import requests

NVIDIA_API_KEY = "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"
headers = {
  "Authorization": f"Bearer {NVIDIA_API_KEY}",
  "Accept": "application/json"
}

payload = {
  "model": "meta/llama-3.2-90b-vision-instruct",
  "messages": [
    {
      "role": "user",
      "content": "Hello, what models are available?"
    }
  ],
  "max_tokens": 50
}

response = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload)
print(response.status_code)
print(response.text)
