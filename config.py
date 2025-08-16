#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫配置文件
"""

from dataclasses import dataclass
from typing import Literal

# 网站配置
SITE_CONFIG = {
    'ZHIPIN': {
        'urls': {
            'home_page_url': 'https://www.zhipin.com/?ka=header-home-logo',
            'search_page_url': 'https://www.zhipin.com/web/geek/jobs',
            'job_list_url': 'https://www.zhipin.com/wapi/zpgeek/search/joblist.json',
            'job_detail_url': 'https://www.zhipin.com/wapi/zpgeek/job/detail.json',
        },
        'city_id_map': {
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
    }
}


@dataclass
class SiteUrls:
    home_page_url: str
    search_page_url: str
    job_list_url: str
    job_detail_url: str


@dataclass
class SiteConfig:
    name: str
    urls: SiteUrls
    city_id_map: dict[str, str]

    def __init__(self, name: Literal['ZHIPIN']):
        self.name = name
        self.urls = SiteUrls(**SITE_CONFIG[name]['urls'])
        self.city_id_map = SITE_CONFIG[name]['city_id_map']
