"""
主函数
"""

import asyncio
import logging

from search_job import search
from template import get_prompt
from util.common import filter_job_details
from util.fs import write_text
from util.input import collect_user_input
from local_type import UserInput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main(user_input: UserInput):
    _, job_details, search_keywords = await search()
    job_details = filter_job_details(job_details, user_input)
    prompt = get_prompt(job_details, search_keywords, user_input)
    write_text(prompt, 'data/prompt.txt')
    logger.info(f'prompt saved to data/prompt.txt')
    logger.info(prompt[:100] + '...' + prompt[-100:]
                if len(prompt) > 100 else prompt)


if __name__ == "__main__":
    user_input = collect_user_input()
    asyncio.run(main(user_input))
