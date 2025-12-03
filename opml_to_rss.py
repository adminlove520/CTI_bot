#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPML to RSS converter
将OPML文件转换为RSS格式，支持本地文件和远程URL
"""

import argparse
import csv
import os
import requests
import yaml
import xml.etree.ElementTree as ET


def parse_opml(opml_content):
    """
    解析OPML内容，提取RSS源
    :param opml_content: OPML文件内容
    :return: RSS源列表，每个元素为tuple(url, title)
    """
    rss_feeds = []
    try:
        root = ET.fromstring(opml_content)
        # 查找所有outline元素
        for outline in root.iter('outline'):
            # 检查是否为RSS源（有xmlUrl属性）
            if 'xmlUrl' in outline.attrib:
                url = outline.attrib['xmlUrl']
                title = outline.attrib.get('title', outline.attrib.get('text', 'Untitled'))
                rss_feeds.append((url, title))
    except ET.ParseError as e:
        print(f"Error parsing OPML: {e}")
    return rss_feeds


def get_opml_content(source):
    """
    获取OPML文件内容，支持本地文件和远程URL
    :param source: 本地文件路径或远程URL
    :return: OPML文件内容
    """
    if source.startswith(('http://', 'https://')):
        # 远程URL
        try:
            response = requests.get(source, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching OPML from {source}: {e}")
            return None
    else:
        # 本地文件
        try:
            with open(source, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError as e:
            print(f"Error reading OPML file {source}: {e}")
            return None


def load_config(config_file):
    """
    加载配置文件
    :param config_file: 配置文件路径
    :return: 配置字典
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


def merge_rss_feeds(existing_feeds, new_feeds):
    """
    合并现有RSS源和新RSS源，去重
    :param existing_feeds: 现有RSS源列表
    :param new_feeds: 新RSS源列表
    :return: 合并后的RSS源列表
    """
    # 使用集合去重，保留顺序
    seen_urls = set()
    merged_feeds = []
    
    # 先添加现有RSS源
    for feed in existing_feeds:
        url = feed[0]
        if url not in seen_urls:
            seen_urls.add(url)
            merged_feeds.append(feed)
    
    # 再添加新RSS源
    for url, title in new_feeds:
        if url not in seen_urls:
            seen_urls.add(url)
            merged_feeds.append((url, title))
    
    return merged_feeds


def read_existing_feeds(feed_file):
    """
    读取现有RSS源
    :param feed_file: Feed.csv文件路径
    :return: 现有RSS源列表
    """
    existing_feeds = []
    try:
        with open(feed_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith('#'):
                    existing_feeds.append(row)
    except IOError as e:
        print(f"Error reading existing feeds from {feed_file}: {e}")
    return existing_feeds


def write_feeds_to_csv(feeds, output_file):
    """
    将RSS源写入CSV文件
    :param feeds: RSS源列表
    :param output_file: 输出CSV文件路径
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for feed in feeds:
                writer.writerow(feed)
        print(f"Successfully wrote {len(feeds)} feeds to {output_file}")
    except IOError as e:
        print(f"Error writing feeds to {output_file}: {e}")


def main():
    parser = argparse.ArgumentParser(description='OPML to RSS converter')
    parser.add_argument('-c', '--config', default='config_rss.yaml', help='Config file path')
    parser.add_argument('-o', '--output', default='Feed.csv', help='Output CSV file path')
    parser.add_argument('--opml-file', help='Single OPML file to convert (overrides config)')
    parser.add_argument('--opml-url', help='Single OPML URL to convert (overrides config)')
    args = parser.parse_args()

    # 读取现有RSS源
    existing_feeds = read_existing_feeds(args.output)
    
    if args.opml_file or args.opml_url:
        # 处理单个OPML文件或URL
        if args.opml_file:
            opml_content = get_opml_content(args.opml_file)
        else:
            opml_content = get_opml_content(args.opml_url)
        
        if opml_content:
            new_feeds = parse_opml(opml_content)
            merged_feeds = merge_rss_feeds(existing_feeds, new_feeds)
            write_feeds_to_csv(merged_feeds, args.output)
    else:
        # 从配置文件读取OPML源
        config = load_config(args.config)
        if not config:
            return
        
        all_new_feeds = []
        
        # 遍历所有配置的RSS源
        for name, rss_config in config.get('rss', {}).items():
            if rss_config.get('enabled', False):
                print(f"Processing {name}...")
                
                # 确定OPML源
                opml_source = None
                if 'url' in rss_config:
                    opml_source = rss_config['url']
                elif 'filename' in rss_config:
                    opml_source = rss_config['filename']
                
                if opml_source:
                    opml_content = get_opml_content(opml_source)
                    if opml_content:
                        new_feeds = parse_opml(opml_content)
                        all_new_feeds.extend(new_feeds)
                        print(f"Found {len(new_feeds)} feeds in {name}")
        
        # 合并所有新RSS源和现有RSS源
        if all_new_feeds:
            merged_feeds = merge_rss_feeds(existing_feeds, all_new_feeds)
            write_feeds_to_csv(merged_feeds, args.output)
        else:
            print("No new feeds found from OPML sources")


if __name__ == '__main__':
    main()
