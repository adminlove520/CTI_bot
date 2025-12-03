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

    response = requests.post(
        url=full_url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=10
    )
    return response.status_code # Should be 200

# ---------------------------------------------------------------------------
# Load ransomware config from YAML file
# ---------------------------------------------------------------------------
def load_ransomware_config(config_file="config_ransomware.yaml"):
    """
    Load ransomware configuration from YAML file
    :param config_file: Path to config file
    :return: Config dictionary
    """
    if not exists(config_file):
        # Create default config if file doesn't exist
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
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        return default_config

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Ensure backward compatibility for old filter names
        ransomware_config = config.get("ransomware", {})
        filters = ransomware_config.get("filters", {})

        # Convert old filter names to new ones if present
        if "countries" in filters and "country" not in filters:
            filters["country"] = filters.pop("countries")
        if "attack_types" in filters and "sector" not in filters:
            filters["sector"] = filters.pop("attack_types")
        if "groups" in filters and "group" not in filters:
            filters["group"] = filters.pop("groups")

        # Ensure default values
        if "date" not in filters:
            filters["date"] = "discovered"

        # Always prioritize environment variables over config file values
        # Get API key from environment variable if available
        api_key_env = os.getenv('RANSOMWARE_LIVE_API_KEY')
        if api_key_env:
            ransomware_config["api_key"] = api_key_env

        # Get enabled flag from environment variable if available
        enabled_env = os.getenv('RANSOMWARE_ENABLED')
        if enabled_env:
            ransomware_config["enabled"] = enabled_env.lower() == 'true'

        # Get use_pro flag from environment variable if available
        use_pro_env = os.getenv('RANSOMWARE_USE_PRO')
        if use_pro_env:
            ransomware_config["use_pro"] = use_pro_env.lower() == 'true'

        # Get push settings from environment variables if available
        push_settings = ransomware_config.get("push_settings", {})
        webhook_env = os.getenv('DINGTALK_WEBHOOK_RANSOMWARE')
        secret_env = os.getenv('DINGTALK_SECRET_RANSOMWARE')

        if webhook_env:
            push_settings["webhook_url"] = webhook_env
        if secret_env:
            push_settings["secret"] = secret_env

        ransomware_config["push_settings"] = push_settings
        config["ransomware"] = ransomware_config

        return config
    except yaml.YAMLError as e:
        print(f"Error parsing ransomware config: {e}")
        return {}
    except Exception as e:
        print(f"Error reading ransomware config: {e}")
        return {}

# ---------------------------------------------------------------------------
# Fetch Ransomware attacks from https://www.ransomware.live
# ---------------------------------------------------------------------------
def get_ransomware_updates():
    """
    Fetch ransomware updates from ransomware.live API.

    Loads configuration, fetches data from either PRO or free API,
    applies filters, and sends notifications to DingTalk.
    """

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
        if filters.get("year") and filters["year"]:
            params["year"] = ",".join(filters["year"])
        if filters.get("month") and filters["month"]:
            params["month"] = ",".join(filters["month"])
        # Note: date parameter is removed as it was causing 400 errors

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response
            print(f"API PRO call successful, status code: {response.status_code}")
            print(f"API PRO response content length: {len(response.content)} bytes")
        except requests.RequestException as e:
            print(f"Error fetching data from API PRO: {e}")
            # Print response content for debugging
            try:
                if hasattr(e.response, 'content'):
                    print(f"API PRO response content: {e.response.content[:500]}...")
            except Exception:
                pass
            # Fallback to free API if PRO fails
            use_pro = False

    if not use_pro or data is None:
        # Use free API as fallback
        try:
            data = requests.get("https://data.ransomware.live/posts.json", timeout=10)
            print(f"Free API call successful, status code: {data.status_code}")
        except requests.RequestException as e:
            print(f"Error fetching data from free API: {e}")
            return  # Exit function if both APIs fail

    try:
        entries = data.json()
        for entry in entries:
            # Apply filters for free API
            if not use_pro:
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
                url = "<br><br><b>Screenshot :</b> <a href='https://images.ransomware.live/screenshots/posts/" +  url_md5 + ".png'> 📸 </a>"
            else:
                url = ""

            if entry['website']:
                website = f"<a href=\"{entry['website']}\">{entry['website']}</a>"
            else:
                search_query = entry["post_title"].replace(".*", "")
                website = f'<a href="https://www.google.com/search?q={search_query}">{entry["post_title"]}</a>'

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

            output_message = ("<b>Group : </b>"
                              f"<a href=\"https://www.ransomware.live/#/profiles?id="
                              f"{entry['group_name']}\">"
                              f"{entry['group_name']}</a>")

            # Add classification tags if any
            if classification_tags:
                output_message += "<br><br>🏷️ "
                output_message += " | ".join(classification_tags)

            output_message += "<br><br>🗓 "
            output_message += entry["discovered"]

            if entry.get("description"):
                output_message += "<br><br>🗒️ "
                output_message += entry["description"]

            output_message += "<br><br>🌍 "
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
    except Exception as e:
        print(f"Error processing ransomware updates: {e}")


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

        output_message = "Date: " + date_activity
        output_message += "<br>"
        # output_message += "Title:<b> " + rss_object.title
        output_message += "Source:<b> " + rss_item[1]
        output_message += "</b><br>"
        output_message += "Read more: " + rss_object.link
        output_message += "<br>"

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

    Checks for new domains published today or yesterday (handling timezone differences),
    downloads the text file, and sends notifications to DingTalk.
    """
    now = datetime.now()
    format_str = "%Y-%m-%d"
    today = now.strftime(format_str)
    yesterday = now - timedelta(days=1)
    yesterday = yesterday.strftime(format_str)

    try:
        tmp_object = FileConfig.get('Misc',"redflagdomains")
    except KeyError:
        FileConfig.set('Misc', "redflagdomains", str(yesterday))
        tmp_object = str(yesterday)

    tmp_object = datetime.strptime(tmp_object, '%Y-%m-%d')
    today_dt = datetime.strptime(today, '%Y-%m-%d')
    yesterday_dt = datetime.strptime(yesterday, '%Y-%m-%d')

    today_dt = today_dt.date()
    yesterday_dt = yesterday_dt.date()
    tmp_object = tmp_object.date()

    # Check both today and yesterday due to timezone differences
    dates_to_check = [today, yesterday] if tmp_object < today_dt else [today]
    
    for check_date in dates_to_check:
        # 使用正确的下载链接格式
        url = f"https://dl.red.flag.domains/daily/{check_date}.txt"
        
        try:
            response = urllib.request.urlopen(url, timeout=10)
            # Check if response is successful
            if response.getcode() == 200:
                # 读取文本内容
                content = response.read().decode('utf-8')
                
                # 格式化输出信息
                output_message = ""
                domains = content.strip().split('\n')
                for domain in domains:
                    if domain.strip():
                        output_message += f"🔴 {domain.strip()}<br>"
                
                title = "🚩 Red Flag Domains créés ce jour (" +  str(check_date) + ")"
                FileConfig.set('Misc', "redflagdomains", str(check_date))
                
                if options.Debug:
                    print(title)
                    print(output_message)
                else:
                    send_dingtalk(webhook_feed, secret_feed, output_message, title)
                    time.sleep(3)
                # 如果今天的文件存在，就不需要检查昨天的了
                if check_date == today:
                    break
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
        sys.exit("Please add the Feed.cvs file")

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
