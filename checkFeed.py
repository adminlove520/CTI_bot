#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check RSS feeds for validity and remove invalid ones
"""

import argparse
import csv
import feedparser
import yaml
import time

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def load_config(config_file):
    """
    Load configuration from YAML file
    :param config_file: Path to config file
    :return: Config dictionary
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error parsing config file {config_file}: {e}")
        return None
    except IOError as e:
        print(f"Error reading config file {config_file}: {e}")
        return None


def check_rss_feed(url):
    """
    Check if an RSS feed is valid
    :param url: RSS feed URL
    :return: Tuple (is_valid, reason)
    """
    try:
        # feedparser.parse() in version 6.0.10 doesn't support timeout parameter
        # Use a different approach to handle timeouts
        import socket
        
        # Set default socket timeout
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(10)
        
        try:
            feed = feedparser.parse(url)
            
            # Check if feed was parsed successfully
            if feed.bozo == 1:
                return False, f"Parsing error: {feed.bozo_exception}"
            
            # Check if there are any entries
            if not feed.entries:
                return False, "No entries found in feed"
            
            # Check if feed has necessary fields
            try:
                # Try to access published date
                if hasattr(feed.entries[0], 'published'):
                    return True, f"OK (published: {feed.entries[0].published[:10]})"
                # Try to access updated date
                elif hasattr(feed.entries[0], 'updated'):
                    return True, f"OK (updated: {feed.entries[0].updated[:10]})"
                else:
                    return True, "OK (no date field)"
            except IndexError:
                return False, "No entries found in feed"
        finally:
            # Restore original socket timeout
            socket.setdefaulttimeout(original_timeout)
    except Exception as e:
        return False, f"Unexpected error: {e}"


def read_feeds_from_csv(feed_file):
    """
    Read RSS feeds from CSV file
    :param feed_file: Path to CSV file
    :return: List of RSS feeds
    """
    feeds = []
    comments = []
    try:
        with open(feed_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                if row[0].startswith('#'):
                    comments.append(row)
                else:
                    feeds.append(row)
    except IOError as e:
        print(f"Error reading feeds from {feed_file}: {e}")
    return comments, feeds


def write_feeds_to_csv(comments, valid_feeds, feed_file):
    """
    Write RSS feeds to CSV file
    :param comments: List of comment lines
    :param valid_feeds: List of valid RSS feeds
    :param feed_file: Path to CSV file
    """
    try:
        with open(feed_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write comments first
            for comment in comments:
                writer.writerow(comment)
            # Write valid feeds
            for feed in valid_feeds:
                writer.writerow(feed)
        print(f"Successfully wrote {len(valid_feeds)} valid feeds to {feed_file}")
    except IOError as e:
        print(f"Error writing feeds to {feed_file}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Check RSS feeds for validity')
    parser.add_argument('-f', '--feed-file', default='Feed.csv', help='Path to Feed.csv file')
    parser.add_argument('-c', '--config', default='config_rss.yaml', help='Path to config file')
    parser.add_argument('--remove-invalid', action='store_true', help='Remove invalid feeds from CSV')
    parser.add_argument('--report-only', action='store_true', help='Only generate report, do not modify files')
    args = parser.parse_args()

    # Load configuration (not used yet, but available for future enhancements)
    config = load_config(args.config)
    
    # Read existing feeds
    comments, feeds = read_feeds_from_csv(args.feed_file)
    
    print(f"Checking {len(feeds)} RSS feeds...")
    print("=" * 80)
    
    valid_feeds = []
    invalid_feeds = []
    
    # Check each feed
    for feed in feeds:
        url = feed[0]
        name = feed[1] if len(feed) > 1 else 'Untitled'
        
        print(f"Checking {name} ({url})...", end=" ")
        is_valid, reason = check_rss_feed(url)
        
        if is_valid:
            print(f"{color.GREEN}✅ {reason}{color.END}")
            valid_feeds.append(feed)
        else:
            print(f"{color.RED}❌ {reason}{color.END}")
            invalid_feeds.append((feed, reason))
        
        # Add a small delay to avoid overwhelming servers
        time.sleep(0.5)
    
    print("=" * 80)
    print(f"\nSummary:")
    print(f"Valid feeds: {len(valid_feeds)}")
    print(f"Invalid feeds: {len(invalid_feeds)}")
    
    if invalid_feeds:
        print(f"\nInvalid feeds list:")
        for feed, reason in invalid_feeds:
            name = feed[1] if len(feed) > 1 else 'Untitled'
            print(f"  - {name} ({feed[0]}): {reason}")
    
    # Write back to CSV if requested
    if args.remove_invalid and not args.report_only:
        if invalid_feeds:
            write_feeds_to_csv(comments, valid_feeds, args.feed_file)
            print(f"\nRemoved {len(invalid_feeds)} invalid feeds from {args.feed_file}")
        else:
            print(f"\nNo invalid feeds to remove")
    
    # Generate commit message
    if invalid_feeds:
        commit_msg = "Update RSS feeds: removed invalid feeds\n\n"
        for feed, reason in invalid_feeds:
            name = feed[1] if len(feed) > 1 else 'Untitled'
            commit_msg += f"- Removed {name} ({feed[0]}): {reason}\n"
        
        # Write commit message to file for use in GitHub Actions
        try:
            with open('commit_message.txt', 'w', encoding='utf-8') as f:
                f.write(commit_msg.strip())
            print(f"\nCommit message written to commit_message.txt")
        except IOError as e:
            print(f"Error writing commit message: {e}")


if __name__ == '__main__':
    main()