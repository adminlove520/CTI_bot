#!/usr/bin/env python3
import os
import sys
import json
from configparser import ConfigParser

# Set environment variables for testing
os.environ['RANSOMWARE_LIVE_API_KEY'] = 'test_key'
os.environ['RANSOMWARE_USE_PRO'] = 'true'
os.environ['DINGTALK_WEBHOOK_RANSOMWARE'] = 'https://example.com/webhook'
os.environ['DINGTALK_SECRET_RANSOMWARE'] = 'test_secret'
os.environ['DINGTALK_WEBHOOK_FEED'] = 'https://example.com/feed-webhook'
os.environ['DINGTALK_SECRET_FEED'] = 'feed-secret'
os.environ['DINGTALK_WEBHOOK_IOC'] = 'https://example.com/ioc-webhook'
os.environ['DINGTALK_SECRET_IOC'] = 'ioc-secret'

# Add current directory to path
sys.path.append('.')

# Import the module and initialize global variables
import TeamsIntelBot

# Initialize global variables by calling the setup function or directly setting them
TeamsIntelBot.webhook_ransomware = os.getenv('DINGTALK_WEBHOOK_RANSOMWARE')
TeamsIntelBot.secret_ransomware = os.getenv('DINGTALK_SECRET_RANSOMWARE')

# Create a mock ConfigParser instance
mock_config = ConfigParser()
mock_config['Ransomware'] = {'TestGroup': '2025-01-01'}

# Set the global FileConfig
TeamsIntelBot.FileConfig = mock_config

# Create mock options
class MockOptions:
    Debug = True

TeamsIntelBot.options = MockOptions()

# Run the ransomware updates function
TeamsIntelBot.get_ransomware_updates()
