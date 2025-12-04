#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CTI_bot - Cyber Threat Intelligence Bot

This bot fetches cyber threat intelligence feeds and sends notifications to DingTalk.
It supports RSS feeds, ransomware updates, and red flag domains.
"""
#----------------------------------------------------------------------------
# Created By  : Anonymous @adminlove520
# Original By : VX-Underground
# Created Date: 28/09/2025
# Version     : 3.0.0 (2025-09-28)
# Modified By : 将推送方式改为钉钉webhook+签名
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
# Standard library imports
import time
import csv # Feed.csv
import sys # Python version
import hashlib
import hmac
import base64 # Ransomware feed via ransomware.live
import urllib.parse
import urllib.request
from configparser import ConfigParser
import os # Webhook OS Variable and Github action
from os.path import exists
from optparse import OptionParser
from datetime import datetime, timedelta
import re

# Third-party library imports
import feedparser
import requests
from bs4 import BeautifulSoup # parse redflag
from dotenv import load_dotenv
import yaml # For loading ransomware config

# 加载.env文件中的环境变量
load_dotenv()

# ---------------------------------------------------------------------------
# Function to send DingTalk card with webhook and signature
# ---------------------------------------------------------------------------
def send_dingtalk(webhook_url:str, secret:str, content:str, title:str) -> int:
    """
      - Send a DingTalk notification to the desired webhook_url with signature
      - Returns the status code of the HTTP request
        - webhook_url : the url you got from the DingTalk webhook configuration
        - secret : the secret key for signature
        - content : your formatted notification content
        - title : the message that'll be displayed as title
    """
    # Generate timestamp and signature
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = f"{timestamp}\n{secret}"
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

    # Construct full URL with timestamp and signature
    full_url = (f"{webhook_url}&timestamp={timestamp}"
                f"&sign={sign}")

    # Replace HTML tags with Markdown format for DingTalk
    content = content.replace('<br>', '\n').replace('<br/>', '\n').replace('<br></br>', '\n')
    content = content.replace('<b>', '**').replace('</b>', '**')
    content = content.replace('<a href="', '[').replace('">', '](').replace('</a>', ')')

    # Prepare payload
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": f"## {title}\n{content}"
        }
    }

    try:
        response = requests.post(
            url=full_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10
        )
        # 添加日志记录，便于调试
        print(f"DingTalk push result: Status {response.status_code}, Content: {response.text}")
        response.raise_for_status()  # 抛出HTTP错误
        return response.status_code # Should be 200
    except requests.RequestException as e:
        print(f"DingTalk push failed: {e}")
        # 尝试打印响应内容
        try:
            if hasattr(e, 'response') and e.response:
                print(f"Response content: {e.response.text}")
        except Exception:
            pass
        return getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500

# ---------------------------------------------------------------------------
# Load ransomware config from YAML file
# ---------------------------------------------------------------------------
def load_ransomware_config(config_file="config_ransomware.yaml"):
    """
    Load ransomware configuration from YAML file
    :param config_file: Path to config file
    :return: Config dictionary
    """
    # Default config structure to ensure we always return a valid dict
    default_config = {
        "ransomware": {
            "api_key": "",
            "enabled": True,
            "use_pro": False,
            "filters": {
                "group": [],
                "sector": [],
                "country": [],
                "year": [],
                "month": [],
                "date": "discovered"
            },
            "push_settings": {
                "webhook_url": os.getenv("DINGTALK_WEBHOOK_RANSOMWARE"),
                "secret": os.getenv("DINGTALK_SECRET_RANSOMWARE")
            }
        }
    }
    
    if not exists(config_file):
        # Create default config if file doesn't exist
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            return default_config
        except Exception as e:
            print(f"Error creating default ransomware config: {e}")
            return default_config

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"Successfully read config file: {config_file}")
        
        # Ensure config is a valid dict
        if not isinstance(config, dict):
            print("Invalid config format, using default config")
            return default_config

        # Ensure ransomware key exists
        if "ransomware" not in config:
            print("ransomware key not found in config, adding default ransomware config")
            config["ransomware"] = default_config["ransomware"]
        
        ransomware_config = config["ransomware"]
        
        # Print initial config values for debugging
        print(f"Initial use_pro from config: {ransomware_config.get('use_pro', 'Not found')}")
        print(f"Initial api_key from config: {'Set' if ransomware_config.get('api_key') else 'Not Set'}")
        
        # Ensure filters key exists
        if "filters" not in ransomware_config:
            ransomware_config["filters"] = default_config["ransomware"]["filters"]
        
        filters = ransomware_config["filters"]

        # Convert old filter names to new ones if present
        if "countries" in filters and "country" not in filters:
            filters["country"] = filters.pop("countries")
        if "attack_types" in filters and "sector" not in filters:
            filters["sector"] = filters.pop("attack_types")
        if "groups" in filters and "group" not in filters:
            filters["group"] = filters.pop("groups")

        # Ensure default filter values
        if "date" not in filters:
            filters["date"] = "discovered"
        if "year" not in filters:
            filters["year"] = []
        if "month" not in filters:
            filters["month"] = []
        if "group" not in filters:
            filters["group"] = []
        if "sector" not in filters:
            filters["sector"] = []
        if "country" not in filters:
            filters["country"] = []

        # Ensure push_settings exists
        if "push_settings" not in ransomware_config:
            ransomware_config["push_settings"] = {}
        
        # Always prioritize environment variables over config file values
        # Get API key from environment variable if available
        api_key_env = os.getenv('RANSOMWARE_LIVE_API_KEY')
        if api_key_env:
            print(f"Setting api_key from environment variable")
            ransomware_config["api_key"] = api_key_env
        
        # Get enabled flag from environment variable if available
        enabled_env = os.getenv('RANSOMWARE_ENABLED')
        if enabled_env:
            print(f"Setting enabled from environment variable: {enabled_env}")
            ransomware_config["enabled"] = enabled_env.lower() == 'true'
        
        # Get use_pro flag from environment variable if available
        use_pro_env = os.getenv('RANSOMWARE_USE_PRO')
        if use_pro_env:
            print(f"Setting use_pro from environment variable: {use_pro_env}")
            ransomware_config["use_pro"] = use_pro_env.lower() == 'true'
        # If no environment variable, ensure use_pro is set from config file
        elif "use_pro" not in ransomware_config:
            print(f"use_pro not found in config, using default: {default_config['ransomware']['use_pro']}")
            ransomware_config["use_pro"] = default_config["ransomware"]["use_pro"]
        
        # Get push settings from environment variables if available
        push_settings = ransomware_config["push_settings"]
        webhook_env = os.getenv('DINGTALK_WEBHOOK_RANSOMWARE')
        secret_env = os.getenv('DINGTALK_SECRET_RANSOMWARE')

        if webhook_env:
            push_settings["webhook_url"] = webhook_env
        if secret_env:
            push_settings["secret"] = secret_env

        ransomware_config["push_settings"] = push_settings
        config["ransomware"] = ransomware_config
        
        # Print final config values for debugging
        print(f"Final use_pro: {ransomware_config.get('use_pro')}")
        print(f"Final api_key: {'Set' if ransomware_config.get('api_key') else 'Not Set'}")

        return config
    except yaml.YAMLError as e:
        print(f"Error parsing ransomware config: {e}, using default config")
        return default_config
    except Exception as e:
        print(f"Error reading ransomware config: {e}, using default config")
        return default_config

# ---------------------------------------------------------------------------
# Fetch Ransomware attacks from https://www.ransomware.live
# ---------------------------------------------------------------------------
def get_ransomware_updates():
    """
    Fetch ransomware updates from ransomware.live API.

    Loads configuration, fetches data from either PRO or free API,
    applies filters, and sends notifications to DingTalk.
    """

    # Get global webhook and secret variables
    global webhook_ransomware, secret_ransomware
    
    # Load ransomware config
    ransomware_config = load_ransomware_config().get("ransomware", {})
    use_pro = ransomware_config.get("use_pro", False)
    api_key = ransomware_config.get("api_key", "")
    filters = ransomware_config.get("filters", {})

    # Get push settings
    push_settings = ransomware_config.get("push_settings", {})
    webhook = push_settings.get("webhook_url", webhook_ransomware)
    secret = push_settings.get("secret", secret_ransomware)

    data = None

    # Debug log for PRO API conditions - show first 5 chars of api_key for security
    api_key_display = f"{api_key[:5]}..." if api_key else "Not Set"
    print(f"PRO API conditions: use_pro={use_pro}, api_key={api_key_display}")
    
    if use_pro and api_key:
        # Use API PRO
        url = "https://api-pro.ransomware.live/victims/"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        params = {}

        # Add filters if any - only add non-empty values
        if filters.get("group") and filters["group"]:
            params["group"] = ",".join(filters["group"])
        if filters.get("sector") and filters["sector"]:
            params["sector"] = ",".join(filters["sector"])
        if filters.get("country") and filters["country"]:
            params["country"] = ",".join(filters["country"])
        
        # Add year filter - use current year if not provided
        if filters.get("year") and filters["year"]:
            params["year"] = ",".join(filters["year"])
        else:
            current_year = str(datetime.now().year)
            params["year"] = current_year
        
        # Add month filter - use current month if not provided
        if filters.get("month") and filters["month"]:
            params["month"] = ",".join(filters["month"])
        else:
            current_month = str(datetime.now().month).zfill(2)
            params["month"] = current_month
        
        # Note: date parameter is removed as it was causing 400 errors
        
        print(f"Attempting PRO API call with filters: {params}")
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            print(f"API PRO call successful, status code: {response.status_code}")
            print(f"API PRO response content length: {len(response.content)} bytes")
            
            # Process PRO API response directly
            try:
                response_dict = response.json()
                print(f"PRO API response type: {type(response_dict)}")
                print(f"Response keys: {list(response_dict.keys())}")
                
                # Print more detailed response information
                for key, value in response_dict.items():
                    value_type = type(value)
                    value_len = len(value) if hasattr(value, '__len__') else 'N/A'
                    print(f"  {key}: {value_type} (length: {value_len})")
                    # Print sample data for lists or dicts
                    if isinstance(value, list) and value:
                        print(f"    Sample entry type: {type(value[0])}")
                        if isinstance(value[0], dict):
                            print(f"    Sample entry keys: {list(value[0].keys())}")
                            # Print a more detailed sample
                            print(f"    Detailed sample: {value[0].get('group_name', 'N/A')} - {value[0].get('post_title', 'N/A')[:50]}...")
                    elif isinstance(value, dict):
                        print(f"    Dict keys: {list(value.keys())}")
                
                # Get victims list
                victims = response_dict.get('victims', [])
                print(f"Processing {len(victims)} victims from PRO API")
                
                # Process each victim
                for victim_entry in victims:
                    # Get victim information
                    group_name = victim_entry.get('group', 'Unknown Group')
                    post_title = victim_entry.get('victim', 'No Title')
                    discovered = victim_entry.get('discovered', 'Unknown Date')
                    website = victim_entry.get('website', '')
                    description = victim_entry.get('description', '')
                    post_url = victim_entry.get('post_url', '')
                    
                    # Prepare website link
                    if website:
                        website_link = f"[{website}]({website})"
                    else:
                        search_query = post_title.replace(".*", "")
                        website_link = f"[Search Google](https://www.google.com/search?q={search_query})"
                    
                    # Prepare screenshot link if available
                    url = ""
                    if post_url:
                        url_md5 = hashlib.md5(post_url.encode('utf-8')).hexdigest()
                        url = f"\n\n📸 [Screenshot](https://images.ransomware.live/screenshots/posts/{url_md5}.png)"
                    elif victim_entry.get('screenshot'):
                        # Use direct screenshot URL from PRO API if available
                        url = f"\n\n📸 [Screenshot]({victim_entry['screenshot']})"
                    
                    # Prepare classification tags
                    classification_tags = []
                    post_title_lower = post_title.lower()
                    if ".cn" in post_title_lower or ".中国" in post_title_lower:
                        classification_tags.append("🇨🇳 中国")
                    elif ".fr" in post_title_lower:
                        classification_tags.append("🇫🇷 法国")
                    elif ".us" in post_title_lower or ".美国" in post_title_lower:
                        classification_tags.append("🇺🇸 美国")
                    elif ".ru" in post_title_lower or ".俄罗斯" in post_title_lower:
                        classification_tags.append("🇷🇺 俄罗斯")
                    
                    # Add country from API response if available
                    country = victim_entry.get('country', '')
                    if country == "CN":
                        classification_tags.append("🇨🇳 中国")
                    elif country == "FR":
                        classification_tags.append("🇫🇷 法国")
                    elif country == "US":
                        classification_tags.append("🇺🇸 美国")
                    elif country == "RU":
                        classification_tags.append("🇷🇺 俄罗斯")
                    
                    # Add activity sector if available
                    activity = victim_entry.get('activity', '')
                    if activity:
                        classification_tags.append(f"🏢 {activity}")
                    
                    # Attack type tag
                    desc_lower = description.lower()
                    if "cyberattack" in desc_lower or "attack" in desc_lower:
                        classification_tags.append("⚔️ cyberattack")
                    elif "nego" in desc_lower or "negotiation" in desc_lower:
                        classification_tags.append("💬 nego")
                    elif "data" in desc_lower and "leak" in desc_lower:
                        classification_tags.append("📊 data leak")
                    
                    # Format output message in Markdown
                    output_message = f"**Group : **[{group_name}](https://www.ransomware.live/#/profiles?id={group_name})"
                    
                    # Add classification tags if any
                    if classification_tags:
                        output_message += "\n\n🏷️ "
                        output_message += " | ".join(classification_tags)
                    
                    output_message += f"\n\n🗓 {discovered}"
                    
                    if description:
                        output_message += f"\n\n🗒️ {description}"
                    
                    output_message += f"\n\n🌍 {website_link}"
                    output_message += url
                    
                    # Prepare title
                    title = "🏴‍☠️ 🔒 "
                    
                    # Add country emoji to title
                    if ".cn" in post_title_lower or ".中国" in post_title_lower or country == "CN":
                        title += " 🇨🇳 "
                    elif ".fr" in post_title_lower or country == "FR":
                        title += " 🇫🇷 "
                    elif ".us" in post_title_lower or ".美国" in post_title_lower or country == "US":
                        title += " 🇺🇸 "
                    elif ".ru" in post_title_lower or ".俄罗斯" in post_title_lower or country == "RU":
                        title += " 🇷🇺 "
                    
                    title += post_title.replace(".*", "")
                    title += " by "
                    title += group_name
                    
                    # Process only new victims (compare with last discovered date)
                    try:
                        last_discovered = FileConfig.get('Ransomware', group_name)
                    except KeyError:
                        FileConfig.set('Ransomware', group_name, " = ?")
                        last_discovered = FileConfig.get('Ransomware', group_name)
                    
                    if last_discovered.endswith("?"):
                        FileConfig.set('Ransomware', group_name, discovered)
                        # Send notification for new group
                        if options.Debug:
                            print(f"New group: {group_name} = {title} ({discovered})")
                        else:
                            send_dingtalk(webhook, secret, output_message, title)
                            time.sleep(3)
                    else:
                        if last_discovered < discovered:
                            FileConfig.set('Ransomware', group_name, discovered)
                            # Send notification for updated group
                            if options.Debug:
                                print(f"Updated group: {group_name} = {title} ({discovered})")
                            else:
                                send_dingtalk(webhook, secret, output_message, title)
                                time.sleep(3)
                
                # Write configuration file after all updates
                with open(ConfigurationFilePath, 'w', encoding='utf-8') as file_handle:
                    FileConfig.write(file_handle)
                    print("Successfully wrote configuration file for PRO API")
                    
            except Exception as e:
                print(f"Error processing PRO API response: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to free API if PRO response processing fails
                print("Falling back to Free API due to response processing error")
                use_pro = False
        except requests.RequestException as e:
            print(f"Error fetching data from API PRO: {e}")
            # Print response content for debugging
            try:
                if hasattr(e.response, 'content'):
                    print(f"API PRO response content: {e.response.content[:500]}...")
            except Exception:
                pass
            # Fallback to free API if PRO fails
            print("Falling back to Free API")
            use_pro = False
    else:
        if not use_pro:
            print("PRO API disabled: use_pro is False")
        if not api_key:
            print("PRO API disabled: api_key is not set")

    if not use_pro:
        # Use free API as fallback
        try:
            data = requests.get("https://data.ransomware.live/posts.json", timeout=10)
            print(f"Free API call successful, status code: {data.status_code}")
        except requests.RequestException as e:
            print(f"Error fetching data from free API: {e}")
            return  # Exit function if both APIs fail

        entries = data.json()
        for entry in entries:
            # Apply filters for free API
            # Filter by country
            country_filter = filters.get("countries", [])
            if country_filter:
                # Check if post_title contains any country domain or name
                post_title = entry["post_title"].lower()
                country_match = False
                for country in country_filter:
                    if country.lower() in post_title or f".{country.lower()}" in post_title:
                        country_match = True
                        break
                if not country_match:
                    continue

            # Filter by attack type (simplified for free API)
            attack_type_filter = filters.get("attack_types", [])
            if attack_type_filter:
                # Free API doesn't provide attack type, so we skip this filter
                pass

            # Filter by group
            group_filter = filters.get("groups", [])
            if group_filter and entry["group_name"] not in group_filter:
                continue

            date_activity = entry["discovered"]

            # Correction for issue #1 : https://github.com/adminlove520/CTI_bot/issues/1
            try:
                tmp_object = FileConfig.get('Ransomware', entry["group_name"])
            except KeyError:
                FileConfig.set('Ransomware', entry["group_name"], " = ?")
                tmp_object = FileConfig.get('Ransomware', entry["group_name"])

            if tmp_object.endswith("?"):
                FileConfig.set('Ransomware', entry["group_name"], date_activity)
            else:
                if tmp_object >= date_activity:
                    continue
            #else:
            #    FileConfig.set('Ransomware', entry["group_name"], entry["discovered"])

            if entry['post_url']:
                url_md5 = hashlib.md5(entry['post_url'].encode('utf-8')).hexdigest()
                url = f"\n\n📸 [Screenshot](https://images.ransomware.live/screenshots/posts/{url_md5}.png)"
            else:
                url = ""

            if entry['website']:
                website = f"[{entry['website']}]({entry['website']})"
            else:
                search_query = entry["post_title"].replace(".*", "")
                website = f"[Search Google](https://www.google.com/search?q={search_query})"

            # Add classification tags and emojis
            classification_tags = []

            # Country tag
            post_title = entry["post_title"]
            if ".cn" in post_title or ".中国" in post_title:
                classification_tags.append("🇨🇳 中国")
            elif ".fr" in post_title:
                classification_tags.append("🇫🇷 法国")
            elif ".us" in post_title or ".美国" in post_title:
                classification_tags.append("🇺🇸 美国")
            elif ".ru" in post_title or ".俄罗斯" in post_title:
                classification_tags.append("🇷🇺 俄罗斯")

            # Attack type tag (simplified)
            description = entry.get("description", "").lower()
            if "cyberattack" in description or "attack" in description:
                classification_tags.append("⚔️ cyberattack")
            elif "nego" in description or "negotiation" in description:
                classification_tags.append("💬 nego")
            elif "data" in description and "leak" in description:
                classification_tags.append("📊 data leak")

            output_message = ("**Group : **"
                              f"[{entry['group_name']}](https://www.ransomware.live/#/profiles?id={entry['group_name']})")

            # Add classification tags if any
            if classification_tags:
                output_message += "\n\n🏷️ "
                output_message += " | ".join(classification_tags)

            output_message += "\n\n🗓 "
            output_message += entry["discovered"]

            if entry.get("description"):
                output_message += "\n\n🗒️ "
                output_message += entry["description"]

            output_message += "\n\n🌍 "
            output_message += website
            output_message += url


            title = "🏴‍☠️ 🔒 "

            # Add country emoji to title
            if ".cn" in post_title or ".中国" in post_title:
                title += " 🇨🇳 "
            elif ".fr" in post_title:
                title += " 🇫🇷 "
            elif ".us" in post_title or ".美国" in post_title:
                title += " 🇺🇸 "
            elif ".ru" in post_title or ".俄罗斯" in post_title:
                title += " 🇷🇺 "

            title += entry["post_title"].replace(".*", "")
            title += " by "
            title += entry["group_name"]

            if options.Debug:
                print(entry["group_name"] + " = " + title + " ("  + entry["discovered"]+"")
            else:
                send_dingtalk(webhook, secret, output_message, title)
                time.sleep(3)

            FileConfig.set('Ransomware', entry["group_name"], entry["discovered"])

        # Write configuration file after all updates
        with open(ConfigurationFilePath, 'w', encoding='utf-8') as file_handle:
            FileConfig.write(file_handle)


# ---------------------------------------------------------------------------
# Add nice Emoji in front of title
# ---------------------------------------------------------------------------
def emoji(feed):
    """
    Return appropriate emoji based on feed name.

    Args:
        feed (str): The name of the feed

    Returns:
        str: An emoji string to prefix the feed title
    """
    # Emoji mapping dictionary
    emoji_map = {
        "Leak-Lookup": '💧 ',
        "VERSION": '🔥 ',
        "DataBreaches": '🕳 ',
        "FR-CERT Alertes": '🇫🇷 ',
        "FR-CERT Avis": '🇫🇷 ',
        "EU-ENISA Publications": '🇪🇺 ',
        "Cyber-News": '🕵🏻‍♂️ ',
        "Bleeping Computer": '💻 ',
        "Microsoft Sentinel": '🔭 ',
        "Hacker News": '📰 ',
        "Cisco": '📡 ',
        "Securelist": '📜 ',
        "ATT": '📞 ',
        "Google TAG": '🔬 ',
        "DaVinci Forensics": '📐 ',
        "VirusBulletin": '🦠 ',
        "Information Security Magazine": '🗞 ',
        "US-CERT CISA": '🇺🇸 ',
        "NCSC": '🇬🇧 ',
        "SANS": '🌍 ',
        "malpedia": '📖 ',
        "Unit42": '🚓 ',
        "Microsoft Security": 'Ⓜ️ ',
        "Checkpoint Research": '🏁 ',
        "Proof Point": '🧾 ',
        "RedCanary": '🦆 ',
        "MSRC Security Update": '🚨 ',
        "CIRCL Luxembourg": '🇱🇺 '
    }

    # Return emoji from mapping or default
    return emoji_map.get(feed, '📢')


# ---------------------------------------------------------------------------
# Function fetch RSS feeds
# ---------------------------------------------------------------------------
def get_rss_from_url(rss_item):
    """
    Fetch and process RSS feeds.

    Args:
        rss_item (list): List containing RSS URL and feed name

    Processes each entry in the RSS feed, checks for new content,
    and sends notifications to DingTalk.
    """
    news_feed = feedparser.parse(rss_item[0])
    date_activity = ""
    # print('DEBUG --> ' +  rss_item[1])

    for rss_object in reversed(news_feed.entries):

        try:
            date_activity = time.strftime('%Y-%m-%dT%H:%M:%S', rss_object.published_parsed)
        except AttributeError:
            date_activity = time.strftime('%Y-%m-%dT%H:%M:%S', rss_object.updated_parsed)


        try:
            tmp_object = FileConfig.get('Rss', rss_item[1])
        except KeyError:
            FileConfig.set('Rss', rss_item[1], " = ?")
            tmp_object = FileConfig.get('Rss', rss_item[1])

        if tmp_object.endswith("?"):
            FileConfig.set('Rss', rss_item[1], date_activity)
        else:
            if(tmp_object >= date_activity):
                continue

        output_message = f"**Date:** {date_activity}\n"
        # output_message += "**Title:** " + rss_object.title + "\n"
        output_message += f"**Source:** {rss_item[1]}\n"
        output_message += f"**Read more:** {rss_object.link}\n"

        title = emoji(rss_item[1])
        title += " " + rss_object.title

        if rss_item[1] == "VERSION":
                title ='🔥 A NEW VERSION IS AVAILABLE : ' + rss_object.title

        if options.Debug:
            print(title + " : " + rss_object.title + " (" + date_activity + ")")
        else:
            send_dingtalk(webhook_feed, secret_feed, output_message, title)
            time.sleep(3)

        FileConfig.set('Rss', rss_item[1], date_activity)

    with open(ConfigurationFilePath, 'w', encoding='utf-8') as file_handle:
        FileConfig.write(file_handle)

# ---------------------------------------------------------------------------
# Function fetch Red Flag domains
# ---------------------------------------------------------------------------
def get_red_flag_domains():
    """
    Fetch red flag domains from red.flag.domains.

    Directly uses T-1 (previous day) date as requested, downloads the text file,
    and sends notifications to DingTalk.
    """
    now = datetime.now()
    format_str = "%Y-%m-%d"
    yesterday = now - timedelta(days=1)
    yesterday = yesterday.strftime(format_str)

    try:
        tmp_object = FileConfig.get('Misc',"redflagdomains")
    except KeyError:
        FileConfig.set('Misc', "redflagdomains", str(yesterday))
        tmp_object = str(yesterday)

    tmp_object = datetime.strptime(tmp_object, '%Y-%m-%d')
    yesterday_dt = datetime.strptime(yesterday, '%Y-%m-%d')
    yesterday_dt = yesterday_dt.date()
    tmp_object = tmp_object.date()

    # Directly use yesterday's date as requested (T-1)
    check_date = yesterday
    
    # 使用正确的下载链接格式
    url = f"https://dl.red.flag.domains/daily/{check_date}.txt"
    
    try:
        response = urllib.request.urlopen(url, timeout=10)
        # Check if response is successful
        if response.getcode() == 200:
            # 读取文本内容
            content = response.read().decode('utf-8')
            
            # 格式化输出信息（使用Markdown格式）
            output_message = ""
            domains = content.strip().split('\n')
            for domain in domains:
                if domain.strip():
                    output_message += f"- 🔴 {domain.strip()}\n"
            
            title = "🚩 Red Flag Domains créés ce jour (" +  str(check_date) + ")"
            FileConfig.set('Misc', "redflagdomains", str(check_date))
            
            if options.Debug:
                print(title)
                print(output_message)
            else:
                send_dingtalk(webhook_feed, secret_feed, output_message, title)
                time.sleep(3)
        else:
            print(f"Error fetching Red Flag Domains from {url}: HTTP {response.getcode()}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"URL {url} returned 404, no domains published for this date")
        else:
            print(f"HTTP Error fetching {url}: {e}")
    except urllib.error.URLError as e:
        print(f"Network Error fetching {url}: {e}")
    except Exception as e:
        print(f"Error processing Red Flag Domains from {url}: {e}")
    with open(ConfigurationFilePath, 'w', encoding='utf-8') as file_handle:
        FileConfig.write(file_handle)

# ---------------------------------------------------------------------------
# Function Send Feeds Reminder
# ---------------------------------------------------------------------------
def send_reminder():
    """
    Send monthly feeds reminder.

    Compiles a list of active feeds and sends a monthly reminder
    notification to DingTalk.
    """
    now = datetime.now()
    format_str = "%Y-%m-%d"
    today = now.strftime(format_str)
    lastmonth = now - timedelta(days=31)
    lastmonth = lastmonth.strftime(format_str)
    try:
        tmp_object = FileConfig.get('Misc',"reminder")
    except KeyError:
        FileConfig.set('Misc', "reminder", str(lastmonth))
        tmp_object = str(lastmonth)

    tmp_object = datetime.strptime(tmp_object, '%Y-%m-%d')
    today = datetime.strptime(today, '%Y-%m-%d')
    lastmonth = datetime.strptime(lastmonth, '%Y-%m-%d')

    if tmp_object < lastmonth:
        title = "🤔 Monthly Feeds Reminder"
        if options.Debug:
            print(title)
        output_message="Feeds : <br>"
        with open('Feed.csv', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rss_feed_list = list(reader)

        for rss_item in rss_feed_list:
            if '#' in str(rss_item[0]):
                continue
            feed = feedparser.parse(rss_item[0])
            try:
                published_date = feed.entries[0].published
                output_message += f"{emoji(rss_item[1])} {rss_item[1]}  ({published_date})<br>"
            except AttributeError:
                try:
                    updated_date = feed.entries[0].updated
                    output_message += f"{emoji(rss_item[1])} {rss_item[1]}  ({updated_date})<br>"
                except AttributeError:
                    continue
        if options.Domains:
            output_message += "Misc : <br>🚩 Red Flag Domains<br>"
        output_message += ("Ransomware :<br>🏴‍☠️ 🔒 Ransomware Leaks"
                         "<br><br>Coded with ❤️ by JMousqueton"
                         "<BR>Code : https://github.com/adminlove520/CTI_bot")
        today = today.strftime(format_str)
        FileConfig.set('Misc', "reminder", str(today))
        if options.Debug:
            print(output_message)
        else:
            send_dingtalk(webhook_ioc, secret_ioc, output_message, title)

    with open(ConfigurationFilePath, 'w', encoding='utf-8') as file_handle:
        FileConfig.write(file_handle)


# ---------------------------------------------------------------------------
# Log
# ---------------------------------------------------------------------------
def create_log_string(rss_item):
    """
    Create and print log string.

    Args:
        rss_item (str): The name of the feed or item being checked

    Prints a log message with timestamp and sleeps for 2 seconds.
    """
    log_string = "[*]" + time.ctime()
    log_string += " " + "checked " + rss_item
    if not options.Quiet:
        print(log_string)
    time.sleep(2)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 2.2.0")
    parser.add_option("-q", "--quiet",
                      action="store_true",
                      dest="Quiet",
                      default=False,
                      help="Quiet mode")
    parser.add_option("-D", "--debug",
                      action="store_true",
                      dest="Debug",
                      default=False,
                      help="Debug mode : only output on screen nothing send to MS Teams",)
    parser.add_option("-d", "--domain",
                      action="store_true",
                      dest="Domains",
                      default=False,
                      help="Enable Red Flag Domains source",)
    parser.add_option("-r", "--reminder",
                      action="store_true",
                      dest="Reminder",
                      default=False,
                      help="Enable monthly reminder of Feeds")
    (options, args) = parser.parse_args()

    # Get DingTalk Webhook and Secret from environment variables (首先从.env读取，然后从系统环境变量读取)
    webhook_feed=os.getenv('DINGTALK_WEBHOOK_FEED')
    secret_feed=os.getenv('DINGTALK_SECRET_FEED')
    webhook_ransomware=os.getenv('DINGTALK_WEBHOOK_RANSOMWARE')
    secret_ransomware=os.getenv('DINGTALK_SECRET_RANSOMWARE')
    webhook_ioc=os.getenv('DINGTALK_WEBHOOK_IOC')
    secret_ioc=os.getenv('DINGTALK_SECRET_IOC')

    # expects the configuration file in the same directory as this script by default, replace if desired otherwise
    ConfigurationFilePath = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'Config.txt')

    # Make some simple checks before starting
    if sys.version_info < (3, 10):
        sys.exit("Please use Python 3.10+")
    if (webhook_feed is None and not options.Debug):
        sys.exit("Please use a DINGTALK_WEBHOOK_FEED variable")
    if (secret_feed is None and not options.Debug):
        sys.exit("Please use a DINGTALK_SECRET_FEED variable")
    if (webhook_ransomware is None and not options.Debug):
        sys.exit("Please use a DINGTALK_WEBHOOK_RANSOMWARE variable")
    if (secret_ransomware is None and not options.Debug):
        sys.exit("Please use a DINGTALK_SECRET_RANSOMWARE variable")
    if (webhook_ioc is None and not options.Debug):
        sys.exit("Please use a DINGTALK_WEBHOOK_IOC variable")
    if (secret_ioc is None and not options.Debug):
        sys.exit("Please use a DINGTALK_SECRET_IOC variable")

    if not exists(ConfigurationFilePath):
        sys.exit("Please add a Config.txt file")
    if not exists("./Feed.csv"):
        sys.exit("Please add the Feed.csv file")

    # Read the Config.txt file
    # ConfigurationFilePath = "./Config.txt" ##path to configuration file
    FileConfig = ConfigParser()
    FileConfig.read(ConfigurationFilePath)

    with open('Feed.csv', newline='') as f:
        reader = csv.reader(f)
        RssFeedList = list(reader)

    #for RssItem in RssFeedList:
    #    if '#' in str(RssItem[0]):
    #        continue
    #    GetRssFromUrl(RssItem)
    #    CreateLogString(RssItem[1])

    get_ransomware_updates()
    create_log_string("Ransomware List")

    if options.Domains:
        get_red_flag_domains()
        create_log_string("Red Flag Domains")

    if options.Reminder:
        send_reminder()
        create_log_string("Reminder")
