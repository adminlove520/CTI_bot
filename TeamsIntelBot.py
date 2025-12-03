#!/usr/bin/env python3  
# -*- coding: utf-8 -*- 
#----------------------------------------------------------------------------
# Created By  : Anonymous @adminlove520
# Original By : VX-Underground 
# Created Date: 28/09/2025
# Version     : 0.0.0 (2025-09-28)
# Modified By : 将推送方式改为钉钉webhook+签名
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Imports 
# ---------------------------------------------------------------------------
import feedparser
import time, requests
import csv # Feed.csv
import sys # Python version 
import json, hashlib, hmac, base64 # Ransomware feed via ransomware.live 
from configparser import ConfigParser
import os # Webhook OS Variable and Github action 
from os.path import exists
from optparse import OptionParser
import urllib.request
from bs4 import BeautifulSoup # parse redflag 
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
import yaml # For loading ransomware config

# 加载.env文件中的环境变量
load_dotenv()

# ---------------------------------------------------------------------------
# Function to send DingTalk card with webhook and signature
# ---------------------------------------------------------------------------
def Send_DingTalk(webhook_url:str, secret:str, content:str, title:str) -> int:
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
    full_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
    
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
        json=payload
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
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        return default_config
    
    try:
        with open(config_file, 'r') as f:
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

# ---------------------------------------------------------------------------
# Fetch Ransomware attacks from https://www.ransomware.live 
# ---------------------------------------------------------------------------
def GetRansomwareUpdates():
    
    # Load ransomware config
    ransomware_config = load_ransomware_config().get("ransomware", {})
    use_pro = ransomware_config.get("use_pro", False)
    api_key = ransomware_config.get("api_key", "")
    filters = ransomware_config.get("filters", {})
    
    # Get push settings
    push_settings = ransomware_config.get("push_settings", {})
    webhook = push_settings.get("webhook_url", webhook_ransomware)
    secret = push_settings.get("secret", secret_ransomware)
    
    Data = None
    
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
            Data = response
            print(f"API PRO call successful, status code: {response.status_code}")
            print(f"API PRO response content length: {len(response.content)} bytes")
        except requests.RequestException as e:
            print(f"Error fetching data from API PRO: {e}")
            # Print response content for debugging
            try:
                if hasattr(e.response, 'content'):
                    print(f"API PRO response content: {e.response.content[:500]}...")
            except:
                pass
            # Fallback to free API if PRO fails
            use_pro = False
    
    if not use_pro or Data is None:
        # Use free API as fallback
        try:
            Data = requests.get("https://data.ransomware.live/posts.json", timeout=10)
            print(f"Free API call successful, status code: {Data.status_code}")
        except requests.RequestException as e:
            print(f"Error fetching data from free API: {e}")
            return  # Exit function if both APIs fail
    
    try:
        entries = Data.json()
        for Entries in entries:
            # Apply filters for free API
            if not use_pro:
                # Filter by country
                country_filter = filters.get("countries", [])
                if country_filter:
                    # Check if post_title contains any country domain or name
                    post_title = Entries["post_title"].lower()
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
                if group_filter and Entries["group_name"] not in group_filter:
                    continue
            
            DateActivity = Entries["discovered"]
            
            # Correction for issue #1 : https://github.com/adminlove520/CTI_bot/issues/1
            try:
                TmpObject = FileConfig.get('Ransomware', Entries["group_name"])
            except:
                FileConfig.set('Ransomware', Entries["group_name"], " = ?")
                TmpObject = FileConfig.get('Ransomware', Entries["group_name"])
            
            if TmpObject.endswith("?"):
                FileConfig.set('Ransomware', Entries["group_name"], DateActivity)
            else:
                if(TmpObject >= DateActivity):
                    continue
            #else:
            #    FileConfig.set('Ransomware', Entries["group_name"], Entries["discovered"])
            
            if Entries['post_url']:
                url_md5 = hashlib.md5(Entries['post_url'].encode('utf-8')).hexdigest()
                url = "<br><br><b>Screenshot :</b> <a href='https://images.ransomware.live/screenshots/posts/" +  url_md5 + ".png'> 📸 </a>"
            else: 
                url = ""
            
            if Entries['website']:
                website = "<a href=\"" + Entries['website'] + "\">" + Entries['website'] + "</a>"
            else: 
                website =  "<a href=\"https://www.google.com/search?q=" +  Entries["post_title"].replace(".*", "") + "\">" + Entries["post_title"] + "</a>"
            
            # Add classification tags and emojis
            classification_tags = []
            
            # Country tag
            post_title = Entries["post_title"]
            if ".cn" in post_title or ".中国" in post_title:
                classification_tags.append("🇨🇳 中国")
            elif ".fr" in post_title:
                classification_tags.append("🇫🇷 法国")
            elif ".us" in post_title or ".美国" in post_title:
                classification_tags.append("🇺🇸 美国")
            elif ".ru" in post_title or ".俄罗斯" in post_title:
                classification_tags.append("🇷🇺 俄罗斯")
            
            # Attack type tag (simplified)
            description = Entries.get("description", "").lower()
            if "cyberattack" in description or "attack" in description:
                classification_tags.append("⚔️ cyberattack")
            elif "nego" in description or "negotiation" in description:
                classification_tags.append("💬 nego")
            elif "data" in description and "leak" in description:
                classification_tags.append("📊 data leak")
            
            OutputMessage = "<b>Group : </b>"
            OutputMessage += "<a href=\"https://www.ransomware.live/#/profiles?id="
            OutputMessage += Entries["group_name"]
            OutputMessage += "\">"
            OutputMessage += Entries["group_name"]
            OutputMessage += "</a>"
            
            # Add classification tags if any
            if classification_tags:
                OutputMessage += "<br><br>🏷️ "
                OutputMessage += " | ".join(classification_tags)
            
            OutputMessage += "<br><br>🗓 "
            OutputMessage += Entries["discovered"]
            
            if Entries.get("description"):
                OutputMessage += "<br><br>🗒️ "
                OutputMessage += Entries["description"]
            
            OutputMessage += "<br><br>🌍 " 
            OutputMessage += website 
            OutputMessage += url
            
            
            Title = "🏴‍☠️ 🔒 "      

            # Add country emoji to title
            if ".cn" in post_title or ".中国" in post_title:
                Title += " 🇨🇳 "
            elif ".fr" in post_title:
                Title += " 🇫🇷 "
            elif ".us" in post_title or ".美国" in post_title:
                Title += " 🇺🇸 "
            elif ".ru" in post_title or ".俄罗斯" in post_title:
                Title += " 🇷🇺 "

            Title += Entries["post_title"].replace(".*", "") 
            Title += " by "
            Title += Entries["group_name"]

            if options.Debug:
                print(Entries["group_name"] + " = " + Title + " ("  + Entries["discovered"]+")")
            else:
                Send_DingTalk(webhook, secret, OutputMessage, Title)
                time.sleep(3)

            FileConfig.set('Ransomware', Entries["group_name"], Entries["discovered"])
    
    with open(ConfigurationFilePath, 'w') as FileHandle:
        FileConfig.write(FileHandle)


# ---------------------------------------------------------------------------
# Add nice Emoji in front of title   
# ---------------------------------------------------------------------------
def Emoji(feed):
    # Nice emoji :) 
    match feed:
        case "Leak-Lookup":
            Title = '💧 '
        case "VERSION":
            Title = '🔥 '
        case "DataBreaches":
            Title = '🕳 '
        case "FR-CERT Alertes" | "FR-CERT Avis":
            Title = '🇫🇷 '
        case "EU-ENISA Publications":
            Title = '🇪🇺 '
        case "Cyber-News":
            Title = '🕵🏻‍♂️ '
        case "Bleeping Computer":
            Title = '💻 '
        case "Microsoft Sentinel":
            Title = '🔭 '
        case "Hacker News":
            Title = '📰 '
        case "Cisco":
            Title = '📡 '
        case "Securelist":
            Title = '📜 '
        case "ATT":
            Title = '📞 '
        case "Google TAG":
            Title = '🔬 '
        case "DaVinci Forensics":
            Title = '📐 '
        case "VirusBulletin":
            Title = '🦠 '
        case "Information Security Magazine":
            Title = '🗞 '
        case "US-CERT CISA":
            Title = '🇺🇸 '
        case "NCSC":
            Title = '🇬🇧 '
        case "SANS":
            Title = '🌍 '
        case "malpedia":
            Title = '📖 '
        case "Unit42":
            Title = '🚓 '
        case "Microsoft Security":
            Title = 'Ⓜ️ '
        case "Checkpoint Research":
            Title = '🏁 '
        case "Proof Point":
            Title = '🧾 '
        case "RedCanary":
            Title = '🦆 '
        case "MSRC Security Update":
            Title = '🚨 '
        case "CIRCL Luxembourg":
            Title = '🇱🇺 '
        case _:
            Title = '📢 '
    return Title


# ---------------------------------------------------------------------------
# Function fetch RSS feeds  
# ---------------------------------------------------------------------------
def GetRssFromUrl(RssItem):
    NewsFeed = feedparser.parse(RssItem[0])
    DateActivity = ""
    IsInitialRun = False
    #print('DEBUG --> ' +  RssItem[1])

    for RssObject in reversed(NewsFeed.entries):

        try:
            DateActivity = time.strftime('%Y-%m-%dT%H:%M:%S', RssObject.published_parsed)
        except: 
            DateActivity = time.strftime('%Y-%m-%dT%H:%M:%S', RssObject.updated_parsed)
        
        
        try:
            TmpObject = FileConfig.get('Rss', RssItem[1])
        except:
            FileConfig.set('Rss', RssItem[1], " = ?")
            TmpObject = FileConfig.get('Rss', RssItem[1])

        if TmpObject.endswith("?"):
            FileConfig.set('Rss', RssItem[1], DateActivity)
        else:
            if(TmpObject >= DateActivity):
                continue

        OutputMessage = "Date: " + DateActivity
        OutputMessage += "<br>"
        # OutputMessage += "Title:<b> " + RssObject.title
        OutputMessage += "Source:<b> " + RssItem[1]
        OutputMessage += "</b><br>"
        OutputMessage += "Read more: " + RssObject.link
        OutputMessage += "<br>"

        Title = Emoji(RssItem[1])
        Title += " " + RssObject.title

        if RssItem[1] == "VERSION":
                Title ='🔥 A NEW VERSION IS AVAILABLE : ' + RssObject.title
       
        if options.Debug:
            print(Title + " : " + RssObject.title + " (" + DateActivity + ")")
        else:
            Send_DingTalk(webhook_feed, secret_feed, OutputMessage, Title)
            time.sleep(3)
        
        FileConfig.set('Rss', RssItem[1], DateActivity)

    with open(ConfigurationFilePath, 'w') as FileHandle:
        FileConfig.write(FileHandle)

# ---------------------------------------------------------------------------
# Function fetch Red Flag domains 
# ---------------------------------------------------------------------------
def GetRedFlagDomains():
    now = datetime.now()
    format = "%Y-%m-%d"
    today = now.strftime(format)
    yesterday = now - timedelta(days=1)
    yesterday = yesterday.strftime(format)

    try:
        TmpObject = FileConfig.get('Misc',"redflagdomains")
    except:
        FileConfig.set('Misc', "redflagdomains", str(yesterday))
        TmpObject = str(yesterday)

    TmpObject = datetime.strptime(TmpObject, '%Y-%m-%d')
    today = datetime.strptime(today, '%Y-%m-%d')

    today = today.date()
    TmpObject = TmpObject.date()

    if(TmpObject < today):
        url="https://red.flag.domains/posts/"+ str(today) + "/"
        try:
            response = urllib.request.urlopen(url)
            soup = BeautifulSoup(response, 
                                'html.parser', 
                                from_encoding=response.info().get_param('charset'))
            # response_status = response.status
            #if soup.findAll("meta", property="og:description"):
            #    OutputMessage = soup.find("meta", property="og:description")["content"][4:].replace('.wf ','').replace('.yt ','').replace('.re ','').replace('[','').replace(']','')
            div = soup.find("div", {"class": "content", "itemprop": "articleBody"})
            for p in div.find_all("p"):
                #OutputMessage = re.sub("[\[\]]", "", (p.get_text()))
                OutputMessage = re.sub(r"[\[\]]", "", (p.get_text()))
            Title = "🚩 Red Flag Domains créés ce jour (" +  str(today) + ")"
            FileConfig.set('Misc', "redflagdomains", str(today))
            if options.Debug:
                print(Title)
                print(OutputMessage)
            else:
                Send_DingTalk(webhook_feed, secret_feed, OutputMessage.replace('\n','<br>'), Title)
                time.sleep(3)
        except:
            pass 
    with open(ConfigurationFilePath, 'w') as FileHandle:
        FileConfig.write(FileHandle)

# ---------------------------------------------------------------------------
# Function Send Feeds Reminder 
# ---------------------------------------------------------------------------
def SendReminder():
    now = datetime.now()
    format = "%Y-%m-%d"
    today = now.strftime(format)
    lastmonth = now - timedelta(days=31)
    lastmonth = lastmonth.strftime(format)
    try:
        TmpObject = FileConfig.get('Misc',"reminder")
    except:
        FileConfig.set('Misc', "reminder", str(lastmonth))
        TmpObject = str(lastmonth)
   
    TmpObject = datetime.strptime(TmpObject, '%Y-%m-%d')
    today = datetime.strptime(today, '%Y-%m-%d')
    lastmonth = datetime.strptime(lastmonth, '%Y-%m-%d')
    
    if(TmpObject < lastmonth):
        Title = "🤔 Monthly Feeds Reminder"
        if options.Debug:
            print(Title)
        OutputMessage="Feeds : "
        OutputMessage += "<br>"
        with open('Feed.csv', newline='') as f:
            reader = csv.reader(f)
            RssFeedList = list(reader)

        for RssItem in RssFeedList:
            if '#' in str(RssItem[0]):
                continue
            Feed = feedparser.parse(RssItem[0])
            try:
                OutputMessage += Emoji(RssItem[1]) + RssItem[1] + "  (" + Feed.entries[0].published + ")"
                OutputMessage += "<br>"
            except:
                try:
                    OutputMessage += Emoji(RssItem[1]) + RssItem[1] + "  (" + Feed.entries[0].updated + ")"
                    OutputMessage += "<br>"
                except:
                    continue
        if options.Domains: 
            OutputMessage += "Misc : "
            OutputMessage += "<br>"
            OutputMessage += "🚩 Red Flag Domains"
            OutputMessage += "<br>"
        OutputMessage += "Ransomware :"
        OutputMessage += "<br>"
        OutputMessage += "🏴‍☠️ 🔒 Ransomware Leaks"
        OutputMessage += "<br><br>"
        OutputMessage += "Coded with ❤️ by JMousqueton"
        OutputMessage += "<BR>"
        OutputMessage += "Code : https://github.com/adminlove520/CTI_bot"
        today = today.strftime(format)
        FileConfig.set('Misc', "reminder", str(today))
        if options.Debug:
            print(OutputMessage)
        else: 
            Send_DingTalk(webhook_ioc, secret_ioc, OutputMessage, Title)

    with open(ConfigurationFilePath, 'w') as FileHandle:
        FileConfig.write(FileHandle)


# ---------------------------------------------------------------------------
# Log  
# ---------------------------------------------------------------------------
def CreateLogString(RssItem):
    LogString = "[*]" + time.ctime()
    LogString += " " + "checked " + RssItem
    if not options.Quiet: 
        print(LogString)
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
    if (str(webhook_feed) == "None" and not options.Debug):
             sys.exit("Please use a DINGTALK_WEBHOOK_FEED variable")
    if (str(secret_feed) == "None" and not options.Debug):
             sys.exit("Please use a DINGTALK_SECRET_FEED variable")
    if (str(webhook_ransomware) == "None" and not options.Debug):
             sys.exit("Please use a DINGTALK_WEBHOOK_RANSOMWARE variable")
    if (str(secret_ransomware) == "None" and not options.Debug):
             sys.exit("Please use a DINGTALK_SECRET_RANSOMWARE variable")
    if (str(webhook_ioc) == "None" and not options.Debug):
             sys.exit("Please use a DINGTALK_WEBHOOK_IOC variable")
    if (str(secret_ioc) == "None" and not options.Debug):
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

    GetRansomwareUpdates()
    CreateLogString("Ransomware List")
    
    if options.Domains: 
        GetRedFlagDomains()
        CreateLogString("Red Flag Domains")

    if options.Reminder:
        SendReminder()
        CreateLogString("Reminder")
