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
from config import SiteConfig
from local_type import JobDetailItem, JobDetailResponse, JobListItem, JobListResponse, UserInput, JobItemOrDetailItem
from playwright.async_api import async_playwright, Page, Playwright, Browser, Route
from playwright.async_api import BrowserContext as Context
from playwright_stealth import Stealth
import logging
from util.fs import exists_file, write_json, delete_file, read_json
from util.common import filter_job_list, get_unique_job_list, get_unique_job_details
from tqdm import tqdm
import time
import questionary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BossSpider:
    def __init__(self, site_config: SiteConfig):
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: Context | None = None
        self.page: Page | None = None
        self.site_config: SiteConfig = site_config
        self.is_login: bool = False
        self.current_page: int = 1
        self.job_list: list[JobListItem] = []
        self.job_details: list[JobDetailItem] = []

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

    async def handle_detail_response(self, route: Route, job_details: list[JobDetailItem]):
        """处理岗位详情响应"""
        try:
            logger.info(f"处理岗位详情响应: {route.request.url}")
            original = await route.fetch()
            body = await original.body()
            json_data: JobDetailResponse = json.loads(body.decode('utf-8'))
            if json_data.get('code') == 0:
                job_details.append(json_data.get('zpData', {}))

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

    async def scroll_page(self, user_input: UserInput, job_index: int):
        """滚动页面"""
        logger.info(f"尝试滚动页面, 目标岗位数量: {user_input['max_size']}")

        if not self.page:
            logger.error("页面未初始化")
            raise Exception("页面未初始化")

        last_height = 0
        while len(filter_job_list(self.job_list, user_input)) < user_input['max_size'] * job_index:
            current_height = await self.page.evaluate("document.body.scrollHeight")
            # 如果高度没有变化，则认为已经滚动到底部
            if current_height == last_height:
                logger.warning("页面高度没有变化，认为已经滚动到底部")
                break
            last_height = current_height
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(random.uniform(1, 2))

        logger.info(
            f"共检索到 {len(filter_job_list(self.job_list, user_input))} 个岗位")

    async def click_all_jobs(self, filtered_job_list: list[JobListItem]):
        """点击所有岗位"""
        if not self.page:
            raise Exception("页面未初始化")

        logger.info("开始点击所有岗位")

        job_list = await self.page.locator('.card-area .job-name').all()
        if len(job_list) < 2:
            logger.warning("没有找到岗位")
            return

        encrypt_job_ids = [job['encryptJobId'] for job in filtered_job_list]
        # 页面默认会加载第一条，所以先点击第二条，再点击第一条，确保能触发详情页的请求
        new_job_list = []
        for job in job_list:
            try:
                href = await job.get_attribute('href') or ''
                current_encrypt_job_id = href.split('/')[-1].split('.')[0]
                if current_encrypt_job_id in encrypt_job_ids:
                    new_job_list.append(job)
            except Exception as e:
                logger.error(f"获取岗位链接时出错: {e}")
                continue

        if len(new_job_list) < 2:
            logger.warning("没有找到岗位")
            return

        new_job_list = [new_job_list[1], new_job_list[0]] + new_job_list[2:]
        for job in tqdm(new_job_list, desc="点击岗位详情 🔎"):
            if self.page.is_closed():
                logger.warning("页面已关闭, 退出")
                return
            try:
                await job.click()
                await self.page.wait_for_load_state('load')
                await asyncio.sleep(random.uniform(1, 3))
            except Exception as e:
                logger.error(f"点击岗位时出错: {e}")
                continue

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

    async def search_job(self, job_name: str):
        """搜索岗位"""
        if not self.page:
            raise Exception("页面未初始化")

        page_url = self.page.url
        url_obj = urlparse(page_url)

        logger.info(f"搜索岗位: {job_name}")
        logger.info(f"当前页面: {url_obj.path}")

        input_locators = [
            'input.ipt-search',  # 首页
            '.search-input-box input',  # 搜索页
        ]

        for input_locator in input_locators:
            input_locator = self.page.locator(input_locator)
            if await input_locator.count() > 0:
                await input_locator.fill(job_name)
                await input_locator.press('Enter')
                await self.page.wait_for_load_state('load')
                await asyncio.sleep(random.uniform(2, 4))
                return

        raise Exception(f"未找到搜索框: {job_name}")

    async def search(self, user_input: UserInput):
        """搜索AI Agent岗位"""
        if not self.page:
            raise Exception("页面未初始化")

        await self.page.route(f'{self.site_config.urls.job_list_url}**', lambda route: self.handle_joblist_response(route, self.job_list))
        await self.page.route(f'{self.site_config.urls.job_detail_url}**', lambda route: self.handle_detail_response(route, self.job_details))

        logger.info("请直接在打开的页面中搜索你想要的岗位信息, 然后点击搜索按钮, 如果想退出, 请直接关闭浏览器")
        await self.detect_login_status(need_goto=False)
        await self.save_auth()

        for job_index, job_name in enumerate(user_input['job_names'], 1):
            logger.info(f"开始搜索第 {job_index} 个岗位: {job_name}")
            # 获取职位列表
            await self.search_job(job_name)
            await self.scroll_page(user_input, job_index)  # 滚动页面
            await asyncio.sleep(random.uniform(2, 4))
            # 点击所有岗位列表
            await self.click_all_jobs(filter_job_list(self.job_list, user_input))

        logger.info(
            f"开始过滤岗位, 过滤前: {len(self.job_list)} 个岗位列表, {len(self.job_details)} 个岗位详情")
        filtered_jobs = get_unique_job_list(self.job_list)
        filtered_job_details = get_unique_job_details(self.job_details)

        logger.info(
            f"过滤完成, 共找到 {len(filtered_job_details)} 个岗位详情, {len(filtered_jobs)} 个岗位列表")
        return filtered_jobs, filtered_job_details

    def save_to_json(self, job_list: list[JobListItem], job_detail: list[JobDetailItem]):
        """保存到JSON"""
        write_json(job_list, 'data/joblist.json')
        write_json(job_detail, 'data/jobdetail.json')


async def search(user_input: UserInput):
    """主函数"""
    site_name = 'ZHIPIN'
    site_config = SiteConfig(site_name)
    spider = BossSpider(site_config)
    await spider.init_browser()
    await spider.detect_login_status(need_goto=True)
    if not spider.has_login():
        logger.warning("未登录, 最多只能检索 15 个职位, 跳过登录继续执行")
        confirm = await questionary.confirm("当前未登录, 是否继续搜索(请在页面完成登录，登录后按回车)?", default=True).ask_async()
        if not confirm:
            await spider.close_browser()
            return [], []

    job_list, job_details = await spider.search(user_input=user_input)
    spider.save_to_json(job_list, job_details)
    await spider.close_browser()
    return job_list, job_details


if __name__ == "__main__":
    user_input: UserInput = read_json('data/user_input.json')  # type:ignore
    asyncio.run(search(user_input))
