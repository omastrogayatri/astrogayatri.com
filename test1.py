from flask import Flask, render_template, request, jsonify
import csv
from collections import defaultdict
import requests
import pytz
import os
import urllib.request
TOGETHER_API_KEY = "tgp_v1_xekeicYc2vvaUxUnpuWODX3q1LLMf-x4MCO5HYY6mmc"
TOGETHER_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"  # You can change model
prompt = f"""
    Donot include any reasoning steps or thoughts, Generate a short 5 lines essay on dogs , do not include chain of thought or think in the output. I just need clean essay in the output
    """

headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

data = {
        "model": TOGETHER_MODEL,
        "role": "system",
        "prompt": prompt,
        "max_tokens": 2048,
        "temperature": 0.4
    }

response = requests.post("https://api.together.xyz/v1/completions", headers=headers, json=data, timeout=240)
if response.status_code == 200:
        kundali_text = response.json()['choices'][0]['text'].strip()
        print(kundali_text)
else:
        print(f"Error: {response.text}")