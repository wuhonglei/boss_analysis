#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boss直聘AI Agent岗位爬虫 - Playwright版本
"""

import asyncio
import random
import requests
from datetime import datetime
import pandas as pd
from local_type import JobListQueryParams, JobDetailQueryParams, JobListItem, ZpDataInJobList, JobListResponse, JobDetailResponse, JobDetail
from config import HEADERS


class BossSpider:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    async def get_job_list(self, params: JobListQueryParams):
        """获取页面"""
        base_url = 'https://www.zhipin.com/wapi/zpgeek/search/joblist.json'
        try:
            response = self.session.get(
                base_url, params=params)  # type: ignore
            data: JobListResponse = response.json()
            return data['zpData']['jobList']
        except Exception as e:
            print(f"获取岗位列表出错: {str(e)}")
            return []

    async def get_job_detail(self, params: JobDetailQueryParams) -> JobDetail | None:
        """获取岗位详情"""
        base_url = 'https://www.zhipin.com/wapi/zpgeek/job/detail.json'
        try:
            response = self.session.get(
                base_url, params=params)  # type: ignore
            data: JobDetailResponse = response.json()
            return data['zpData']
        except Exception as e:
            print(f"获取岗位详情出错: {str(e)}")
            return None

    async def search_jobs(self, keyword, city="深圳", page=1) -> list[JobDetail]:
        """搜索岗位"""
        try:
            params = JobListQueryParams(query=keyword, city=city, page=page)
            job_list = await self.get_job_list(params)
            tasks = []
            for job in job_list:
                params = JobDetailQueryParams(
                    securityId=job['securityId'], lid=job['lid'])
                tasks.append(self.get_job_detail(params))
            job_details: list[JobDetail] = await asyncio.gather(*tasks)
            return job_details

        except Exception as e:
            print(f"搜索出错: {str(e)}")
            return []

    async def search_ai_agent_jobs(self, city="北京", max_pages=3):
        """搜索AI Agent岗位"""
        keywords = ["AI Agent"]
        all_jobs = []

        for keyword in keywords:
            print(f"\n搜索关键词: {keyword}")
            for page in range(1, max_pages + 1):
                jobs = await self.search_jobs(keyword, city, page)
                if jobs:
                    all_jobs.extend(jobs)
                await asyncio.sleep(random.uniform(2, 4))

        return self.filter_jobs(all_jobs)

    def filter_jobs(self, jobs: list[JobDetail]) -> list[JobDetail]:
        """过滤AI Agent相关岗位"""
        black_keywords = ['产品', '运营', '设计', '市场', '销售',
                          '客服', '行政', '财务', '法务', '人力', '公关', '其他']
        filtered = []

        for job in jobs:
            if job is None:
                continue

            job_name = job.get('jobInfo', {}).get('jobName', '').lower()
            for keyword in black_keywords:
                if keyword.lower() in job_name:
                    continue
                filtered.append(job)

        return filtered

    def save_to_excel(self, jobs, filename=None):
        """保存到Excel"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"boss_ai_agent_jobs_{timestamp}.xlsx"

        df = pd.DataFrame(jobs)
        df.to_excel(filename, index=False)
        print(f"已保存到: {filename}")
        print(f"总岗位数: {len(jobs)}")

    async def run(self, city="深圳", max_pages=1):
        """运行爬虫"""
        try:
            print(f"开始爬取城市: {city}")

            jobs = await self.search_ai_agent_jobs(city, max_pages)

            # 去重
            unique_jobs = []
            seen_names = set()
            for job in jobs:
                name = job.get('岗位名称', '')
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_jobs.append(job)

            print(f"去重后共 {len(unique_jobs)} 个岗位")

            if unique_jobs:
                self.save_to_excel(unique_jobs)

            return unique_jobs
        except Exception as e:
            print(f"爬取出错: {str(e)}")
            return []


async def main():
    """主函数"""
    cities = ["北京", "上海", "深圳", "广州"]

    print("可选择的城市:")
    for i, city in enumerate(cities, 1):
        print(f"{i}. {city}")

    choice = input("选择城市编号 (1-4，默认深圳): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= 4:
        city = cities[int(choice) - 1]
    else:
        city = "深圳"

    print(f"选择城市: {city}")

    spider = BossSpider()
    jobs = await spider.run(city, max_pages=1)

    if jobs:
        print("爬取完成！结果已保存到Excel文件")

if __name__ == "__main__":
    asyncio.run(main())
