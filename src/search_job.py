#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boss直聘AI Agent岗位爬虫 - Playwright版本
logger.
"""

import json
import asyncio
import random
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
import time

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
        logger.info("浏览器初始化完成, 打开了新页面")
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
        logger.info("浏览器关闭完成")

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

        logger.info("开始检测登录状态")

        try:
            if need_goto:
                await self.page.goto(self.site_config.urls.home_page_url)
            user_name = await self.page.locator('[ka=header-username]').all()
            self.is_login = len(user_name) > 0
            logger.info(f"登录状态: {self.is_login}")
        except Exception as e:
            logger.error(f"检测登录状态时出错: {e}")
            self.is_login = False

    def has_login(self):
        """是否已登录"""
        return self.is_login

    async def handle_joblist_response(self, route: Route, job_list: list[JobListItem]):
        """处理岗位列表响应"""
        logger.info(f"处理岗位列表响应: {route.request.url}")

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
            logger.info(f"处理岗位详情响应: {route.request.url}")
            original = await route.fetch()
            body = await original.body()
            json_data: JobDetailResponse = json.loads(body.decode('utf-8'))
            if json_data.get('code') == 0:
                job_detail.append(json_data.get('zpData', {}))
                # write_json(job_detail, 'data/jobdetail.json')

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
        logger.info(f"滚动页面: {max_pages} 页")

        if not self.page:
            logger.error("页面未初始化")
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

        logger.info("开始点击所有岗位")

        job_list = await self.page.locator('.card-area .job-name').all()
        if len(job_list) < 2:
            logger.warning("没有找到岗位")
            return

        # 页面默认会加载第一条，所以先点击第二条，再点击第一条，确保能触发详情页的请求
        job_list = [job_list[1], job_list[0]] + job_list[2:][:5]
        for job in tqdm(job_list, desc="流量岗位详情 🔎"):
            if self.page.is_closed():
                logger.warning("页面已关闭, 退出")
                return

            await job.click()
            await self.page.wait_for_load_state('load')
            await asyncio.sleep(random.uniform(1, 3))

    async def wait_for_url_change(self, initial_url: str, timeout: int = 60):
        """等待地址栏变化"""
        start_time = time.time()
        while self.page and not self.page.is_closed():
            if self.page.url != initial_url:
                logger.info(f"地址栏变化为 {self.page.url}")
                return True
            await asyncio.sleep(random.uniform(1, 3))
            if time.time() - start_time > timeout:  # 超时
                return False
        return False

    async def get_search_keywords(self):
        """获取搜索关键词"""
        if not self.page:
            raise Exception("页面未初始化")

        search_keywords = await self.page.locator('.search-input-box input').input_value()
        return search_keywords.strip()

    async def search(self, max_pages=3):
        """搜索AI Agent岗位"""
        if not self.page:
            raise Exception("页面未初始化")

        search_keywords: set[str] = set()
        job_list: list[JobListItem] = []
        job_detail: list[JobDetailItem] = []

        await self.page.route(f'{self.site_config.urls.job_list_url}**', lambda route: self.handle_joblist_response(route, job_list))
        await self.page.route(f'{self.site_config.urls.job_detail_url}**', lambda route: self.handle_detail_response(route, job_detail))

        logger.info("请直接在打开的页面中搜索你想要的岗位信息, 然后点击搜索按钮, 如果想退出, 请直接关闭浏览器")
        await self.page.wait_for_url(f'{self.site_config.urls.search_page_url}**', timeout=0)
        last_url = self.page.url
        logger.info(f"地址栏变化为 {last_url}")

        while self.page and not self.page.is_closed():
            await self.save_auth()
            await self.page.wait_for_load_state('load')
            await asyncio.sleep(random.uniform(1, 3))
            logger.info(f"页面加载完成")

            keyword = await self.get_search_keywords()
            if keyword:
                search_keywords.add(keyword)

            # 获取职位列表
            await self.scroll_page(max_pages)  # 滚动页面
            await self.click_all_jobs()  # 点击所有岗位列表

            # 监听地址栏 url 是否发生变化，只有变化了才继续执行
            changed = await self.wait_for_url_change(last_url)
            if not changed:
                logger.warning("地址栏没有变化, 退出")
                break
            last_url = self.page.url

        logger.info(
            f"开始过滤岗位, 过滤前: {len(job_list)} 个岗位列表, {len(job_detail)} 个岗位详情")
        filtered_jobs = self.filter_jobs(job_list)
        filtered_job_details = self.filter_jobs(job_detail)

        logger.info(
            f"过滤完成, 共找到 {len(filtered_job_details)} 个岗位详情, {len(filtered_jobs)} 个岗位列表")
        return filtered_jobs, filtered_job_details, list(search_keywords)

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

    def save_to_json(self, job_list: list[JobListItem], job_detail: list[JobDetailItem], search_keywords: list[str]):
        """保存到JSON"""
        write_json(job_list, 'data/joblist.json')
        write_json(job_detail, 'data/jobdetail.json')
        write_json(search_keywords, 'data/search_keywords.json')


async def search():
    """主函数"""
    site_name = 'ZHIPIN'
    site_config = SiteConfig(site_name)
    spider = BossSpider(site_config)
    await spider.init_browser()
    await spider.detect_login_status(need_goto=True)
    job_list, job_detail, search_keywords = await spider.search(max_pages=1)
    spider.save_to_json(job_list, job_detail, search_keywords)
    await spider.close_browser()
    return job_list, job_detail, search_keywords


if __name__ == "__main__":
    asyncio.run(search())
