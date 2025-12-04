#!/usr/bin/env python3
import os
import sys
import json
import requests

# Set the actual API key provided by user
api_key = "8b05eccc-a8d2-4efa-898b-c3d32a91e279"

# PRO API endpoint
url = "https://api-pro.ransomware.live/victims/"
headers = {
    "X-API-KEY": api_key,
    "Content-Type": "application/json"
}

# Test with current year and month
params = {
    "year": "2025",
    "month": "12"
}

print(f"Testing PRO API with key: {api_key[:8]}...")
print(f"URL: {url}")
print(f"Headers: {headers}")
print(f"Params: {params}")

# Test API call
try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"\nResponse status code: {response.status_code}")
    print(f"Response content length: {len(response.content)} bytes")
    
    # Try to parse JSON
    if response.ok:
        try:
            data = response.json()
            print(f"Response type: {type(data)}")
            print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            
            # Print sample data
            if isinstance(data, dict):
                for key, value in data.items():
                    value_type = type(value)
                    value_len = len(value) if hasattr(value, '__len__') else 'N/A'
                    print(f"  {key}: {value_type} (length: {value_len})")
                    
                    # Print first few items if it's a list
                    if isinstance(value, list):
                        print(f"    First 3 items:")
                        for i, item in enumerate(value[:3]):
                            if isinstance(item, dict):
                                print(f"    [{i+1}] Full structure:")
                                for k, v in item.items():
                                    # Truncate long strings
                                    v_display = v[:50] + "..." if isinstance(v, str) and len(v) > 50 else v
                                    print(f"      {k}: {v_display}")
                                print()
                            else:
                                print(f"    [{i+1}] {item}")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response content: {response.content[:500]}...")
    else:
        print(f"Error response: {response.content.decode('utf-8', errors='ignore')}")
        
except requests.RequestException as e:
    print(f"Request error: {e}")
    if hasattr(e, 'response'):
        print(f"Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
        print(f"Response content: {e.response.content[:500] if hasattr(e.response, 'content') else 'N/A'}")
