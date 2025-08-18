"""
主函数
"""

import asyncio
import logging

from search_job import search
from template import get_prompt
from util.common import filter_job_details
from util.fs import write_text, read_json
from util.input import collect_user_input
from local_type import UserInput, JobDetailItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main(user_input: UserInput, job_details: list[JobDetailItem]):
    if not user_input['user_job_details']:
        _, job_details = await search(user_input)
    else:
        job_details = filter_job_details(job_details, user_input)

    if not job_details:
        logger.warning("没有找到职位信息")
        return

    prompt = get_prompt(job_details, user_input)
    write_text(prompt, 'data/prompt.txt')
    logger.info(f'prompt saved to data/prompt.txt')
    logger.info(prompt[:100] + '...' + prompt[-100:]
                if len(prompt) > 100 else prompt)


if __name__ == "__main__":
    job_details = read_json('data/jobdetail.json')
    exist_job_details = len(job_details) > 0

    user_input = collect_user_input(exist_job_details)
    asyncio.run(main(user_input, job_details))
