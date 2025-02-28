import json
import asyncio
import os
from client import PinterestClient
from utils import logger
from config import MAX_CONCURRENT

async def fetch_with_limit(board_id, uname, board_slug, semaphore):
    async with semaphore:
        async with PinterestClient() as client:
            return board_id, await client.board.get(board_id, uname, board_slug)

async def main():
    # Pinterest配置
    uname = "sunneth7623"
    board_slug = "伪厚涂"

    # Pin ID列表
    ids = ['604538018670785766']  # 您的完整ID列表

    # 创建并发限制
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    try:
        # 执行所有任务
        tasks = [
            fetch_with_limit(board_id, uname, board_slug, semaphore)
            for board_id in ids
        ]
        results = await asyncio.gather(*tasks)

        # 保存结果
        save_dir = '厚涂'
        os.makedirs(save_dir, exist_ok=True)
        for board_id, images in results:
            with open(f'{save_dir}/{board_id}.json', 'w') as f:
                json.dump(images, f)
    except Exception as e:
        logger.error(f"执行过程中出现错误: {e}")

if __name__ == '__main__':
    asyncio.run(main())