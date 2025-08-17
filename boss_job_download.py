#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boss直聘AI Agent岗位爬虫 - Playwright版本
logger.
"""

import os
import json
import asyncio
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlparse, parse_qs
from datetime import datetime
import pandas as pd
from typing import TypeVar, List
from config import SiteConfig
from local_type import JobDetailItem, JobDetailResponse, JobListItem, JobListResponse
from playwright.async_api import async_playwright, Page, Playwright, Browser, Route
from playwright.async_api import BrowserContext as Context
from playwright_stealth import Stealth
import logging
from util.fs import exists_file, write_json, delete_file
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


T = TypeVar('T', JobListItem, JobDetailItem)


class BossSpider:
    def __init__(self, site_config: SiteConfig):
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: Context | None = None
        self.page: Page | None = None
        self.site_config: SiteConfig = site_config
        self.current_page: int = 1
        self.page_size: int = 10
        self.start_interval_check_login_status: bool = False
        self.is_login: bool = False
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.login_check_thread = None

    async def init(self):
        """异步初始化方法"""
        await self.init_browser()

    async def init_browser(self):
        """初始化浏览器"""
        if self.playwright:
            return

        custom_languages = ('zh-CN', 'en')
        stealth = Stealth(
            navigator_languages_override=custom_languages,
            init_scripts_only=True
        )

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        if not self.browser:
            raise Exception("浏览器初始化失败")

        self.context = await self.browser.new_context(
            storage_state=self.site_config.auth_path if exists_file(self.site_config.auth_path) else None)
        if not self.context:
            raise Exception("上下文初始化失败")

        await stealth.apply_stealth_async(self.context)

        self.page = await self.context.new_page()
        if not self.page:
            raise Exception("页面初始化失败")

    async def close_browser(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
            self.page = None
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def save_auth(self):
        """保存认证信息"""
        if not self.context:
            raise Exception("页面未初始化")

        if self.is_login:
            logger.info("保存认证信息")
            await self.context.storage_state(path=self.site_config.auth_path)
        else:
            logger.info("删除认证信息")
            delete_file(self.site_config.auth_path)

    async def detect_login_status(self, need_goto: bool = True):
        """检测登录状态"""
        if not self.page:
            raise Exception("页面未初始化")

        try:
            if need_goto:
                await self.page.goto(self.site_config.urls.home_page_url)
            user_name = await self.page.locator('[ka=header-username]').all()
            self.is_login = len(user_name) > 0
        except Exception as e:
            logger.error(f"检测登录状态时出错: {e}")
            self.is_login = False

    def has_login(self):
        """是否已登录"""
        return self.is_login

    async def handle_joblist_response(self, route: Route, job_list: list[JobListItem]):
        """处理岗位列表响应"""
        # 监听请求参数
        qs = parse_qs(urlparse(route.request.url).query)
        next_page = int(qs.get('page', ['1'])[0])
        self.page_size = int(qs.get('pageSize', ['10'])[0])
        if self.current_page != next_page:
            self.current_page = next_page

        try:
            original = await route.fetch()
            body = await original.body()
            json_data: JobListResponse = json.loads(body.decode('utf-8'))
            if json_data.get('code') == 0:
                job_list.extend(json_data.get('zpData', {}).get('jobList', []))
                write_json(job_list, 'data/joblist.json')

            body = json.dumps(json_data).encode('utf-8')

            await route.fulfill(
                status=original.status,
                headers=original.headers,
                body=body
            )
        except Exception as e:
            logger.error(f"处理响应时出错: {e}")
            # 出错时继续请求
            await route.continue_()

    async def handle_detail_response(self, route: Route, job_detail: list[JobDetailItem]):
        """处理岗位详情响应"""
        try:
            original = await route.fetch()
            body = await original.body()
            json_data: JobDetailResponse = json.loads(body.decode('utf-8'))
            if json_data.get('code') == 0:
                job_detail.append(json_data.get('zpData', {}))
                write_json(job_detail, 'data/jobdetail.json')

            body = json.dumps(json_data).encode('utf-8')

            await route.fulfill(
                status=original.status,
                headers=original.headers,
                body=body
            )
        except Exception as e:
            logger.error(f"处理响应时出错: {e}")
            # 出错时继续请求
            await route.continue_()

    def get_job_list_url(self, keyword: str, city: str) -> str:
        """获取岗位列表URL"""
        city_id = self.site_config.city_id_map.get(city)
        if not city_id:
            raise Exception(f"城市{city}不存在")
        keyword_encoded = quote(keyword)
        return f'{self.site_config.urls.search_page_url}?query={keyword_encoded}&city={city_id}'

    async def scroll_page(self, max_pages: int):
        """滚动页面"""
        if not self.page:
            raise Exception("页面未初始化")

        last_height = 0
        while self.current_page <= max_pages - 1:
            current_height = await self.page.evaluate("document.body.scrollHeight")
            # 如果高度没有变化，则认为已经滚动到底部
            if current_height == last_height:
                logger.warning("页面高度没有变化，认为已经滚动到底部")
                break
            last_height = current_height
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(random.uniform(1, 2))

        logger.info(f"共滚动 {self.current_page} 页")

    async def click_all_jobs(self):
        """点击所有岗位"""
        if not self.page:
            raise Exception("页面未初始化")

        job_list = await self.page.locator('.card-area .job-name').all()
        # 页面默认会加载第一条，所以先点击第二条，再点击第一条，确保能触发详情页的请求
        job_list = [job_list[1], job_list[0]] + job_list[2:]
        logger.info(f"共找到 {len(job_list)} 个岗位")
        for job in tqdm(job_list, desc="流量岗位详情 🔎"):
            await job.click()
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(random.uniform(1, 2))

    async def search_ai_agent_jobs(self, city="北京", max_pages=3):
        """搜索AI Agent岗位"""
        if not self.page:
            raise Exception("页面未初始化")

        keywords = ["AI Agent"]
        job_list: list[JobListItem] = []
        job_detail: list[JobDetailItem] = []

        await self.page.route(f'{self.site_config.urls.job_list_url}**', lambda route: self.handle_joblist_response(route, job_list))
        await self.page.route(f'{self.site_config.urls.job_detail_url}**', lambda route: self.handle_detail_response(route, job_detail))

        for keyword in keywords:
            logger.info(f"\n搜索关键词: {keyword}")
            # 获取职位列表
            url = self.get_job_list_url(keyword, city)
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(random.uniform(3, 5))
            await self.scroll_page(max_pages)  # 滚动页面
            await self.click_all_jobs()  # 点击所有岗位列表

        filtered_jobs = self.filter_jobs(job_list)
        filtered_job_details = self.filter_jobs(job_detail)

        logger.info(f"共找到 {len(filtered_jobs)} 个岗位")
        return filtered_jobs, filtered_job_details

    def filter_jobs(self, jobs: List[T]) -> List[T]:
        """过滤AI Agent相关岗位"""
        black_keywords = ['产品', '运营', '设计', '市场', '销售', '客服',
                          '行政', '财务', '法务', '人力', '公关', '其他', '实习', '兼职', '实习生']
        filtered = []
        encryptJobIds: set[str] = set()  # 用于去重

        for job in jobs:
            if job is None:
                continue

            # 检查是否为JobListItem类型（有encryptJobId和jobName键）
            if 'encryptJobId' in job and 'jobName' in job:
                encryptJobId = job.get('encryptJobId', '')
                job_name = job.get('jobName', '').lower()

            # 检查是否为JobDetailItem类型（有jobInfo键）
            elif 'jobInfo' in job:
                encryptJobId = job.get('jobInfo', {}).get('encryptId', '')
                job_name = job.get('jobInfo', {}).get('jobName', '').lower()

            if encryptJobId in encryptJobIds:
                continue

            success = True
            for keyword in black_keywords:
                if keyword.lower() in job_name:
                    success = False
                    break

            if not success:
                continue

            encryptJobIds.add(encryptJobId)
            filtered.append(job)

        limit = self.page_size * self.current_page
        return filtered[:limit]

    def save_to_excel(self, jobs, filename=None):
        """保存到Excel"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"boss_ai_agent_jobs_{timestamp}.xlsx"

        df = pd.DataFrame(jobs)
        df.to_excel(filename, index=False)
        logger.info(f"已保存到: {filename}")
        logger.info(f"总岗位数: {len(jobs)}")

    async def run(self, city="深圳", max_pages=1):
        """运行爬虫"""
        job_list, job_detail = await self.search_ai_agent_jobs(city, max_pages)
        write_json(job_list, 'data/joblist.json')
        write_json(job_detail, 'data/jobdetail.json')


async def main():
    """主函数"""
    site_name = 'ZHIPIN'
    site_config = SiteConfig(site_name)
    spider = BossSpider(site_config)
    await spider.init()
    await spider.detect_login_status(need_goto=True)

    cities = ["北京", "上海", "深圳", "广州"]

    logger.info("可选择的城市:")
    for i, city in enumerate(cities, 1):
        logger.info(f"{i}. {city}")

    choice = input("选择城市编号 (1-4，默认深圳): ").strip()
    await spider.detect_login_status(need_goto=False)
    await spider.save_auth()

    if choice.isdigit() and 1 <= int(choice) <= 4:
        city = cities[int(choice) - 1]
    else:
        city = "深圳"

    logger.info(f"选择城市: {city}")

    jobs = await spider.run(city, max_pages=1)
    if jobs:
        logger.info("爬取完成！结果已保存到Excel文件")

if __name__ == "__main__":
    asyncio.run(main())
