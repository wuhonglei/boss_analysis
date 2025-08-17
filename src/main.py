"""
主函数
"""

import asyncio
import logging

from search_job import search
from template import get_prompt
from util.fs import write_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    _, job_detail, search_keywords = await search()
    prompt = get_prompt(job_detail, search_keywords)
    write_text(prompt, 'data/prompt.txt')
    logger.info(f'prompt saved to data/prompt.txt')
    logger.info(prompt[:100] + '...' if len(prompt) > 100 else prompt)


if __name__ == "__main__":
    asyncio.run(main())
