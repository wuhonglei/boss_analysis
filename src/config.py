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
            'home_page_url': 'https://www.zhipin.com/web/geek/jobs',
            'search_page_url': 'https://www.zhipin.com/web/geek/jobs',
            'job_list_url': 'https://www.zhipin.com/wapi/zpgeek/search/joblist.json',
            'job_detail_url': 'https://www.zhipin.com/wapi/zpgeek/job/detail.json',
        },
        'auth_path': 'data/auth_zhipin.json'
    }
}

degree_map = {
    '本科': ['本科', '学士', '学历不限'],
    '硕士': ['本科', '硕士', '研究生', '学历不限'],
    '博士': ['硕士', '博士', '博士后', '学历不限'],
    '大专': ['大专', '学历不限'],
}

salary_map = [
    '20-30K',
    '30-50K',
    '50-100K',
]

# 会被忽略的职位
job_ignore_names = [
    '产品',
    '运营',
    '市场',
    '销售',
    '技术支持',
    '客服',
    '行政',
    '财务',
    '实习'
]

query_params_map = {
    'salary': [{
        'id': 402,
        'min': 0,
        'max': 3
    }, {
        'id': 403,
        'min': 3,
        'max': 6
    }, {
        'id': 404,
        'min': 5,
        'max': 10
    }, {
        'id': 405,
        'min': 10,
        'max': 20
    }, {
        'id': 406,
        'min': 20,
        'max': 50
    }, {
        'id': 407,
        'min': 50,
        'max': 100
    }],
    'experience': [{
        'id': 108,
        'value': '在校生'
    }, {
        'id': 102,
        'value': '应届生'
    }, {
        'id': 101,
        'value': '经验不限'
    }, {
        'id': 103,
        'min': 0,
        'max': 1
    }, {
        'id': 104,
        'min': 1,
        'max': 3
    }, {
        'id': 105,
        'min': 3,
        'max': 5
    }, {
        'id': 106,
        'min': 5,
        'max': 10
    }, {
        'id': 107,
        'min': 10,
        'max': 50
    }],
    'degree': [{
        'id': 202,
        'value': '大专'
    }, {
        'id': 203,
        'value': '本科'
    }, {
        'id': 204,
        'value': '硕士'
    }, {
        'id': 205,
        'value': '博士'
    }],
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
    auth_path: str

    def __init__(self, name: Literal['ZHIPIN']):
        self.name = name
        self.urls = SiteUrls(**SITE_CONFIG[name]['urls'])
        self.auth_path = SITE_CONFIG[name]['auth_path']
