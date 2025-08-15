#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫配置文件
"""

# 城市配置
CITIES = {
    "北京": "101010100",
    "上海": "101020100",
    "深圳": "101280600",
    "广州": "101280100",
    "杭州": "101210100",
    "成都": "101270100",
    "南京": "101190100",
    "武汉": "101200100",
    "西安": "101110100",
    "苏州": "101190400"
}

# 爬虫配置
SPIDER_CONFIG = {
    'max_pages': 5,           # 最大爬取页数
    'page_size': 15,          # 每页岗位数量
    'timeout': 10,            # 请求超时时间(秒)
}

# 输出配置
OUTPUT_CONFIG = {
    'excel_filename': 'boss_ai_agent_jobs_{timestamp}.xlsx',
    'csv_filename': 'boss_ai_agent_jobs_{timestamp}.csv',
    'json_filename': 'boss_ai_agent_jobs_{timestamp}.json'
}

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.zhipin.com/',
    'Origin': 'https://www.zhipin.com'
}
