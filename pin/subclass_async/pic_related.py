import httpx
import asyncio
from ..utils import logger
from typing import List, Dict, Any

class PicRelated:
    """相关图片操作类"""

    def __init__(self, client):
        """
        初始化相关图片操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get(self, pin_id: str) -> List[Dict[str, Any]]:
        """
        获取相关图片

        参数:
            pin_id: 图片ID
        返回:
            相关图片列表
        """
        cursor = None
        images = []

        while True:
            # 显示进度
            i_len = len(images)
            logger.debug(f"获取相关图片 [ {i_len} / ? ]")

            try:
                batch, cursor = await self._fetch_batch(pin_id, cursor)
                images.extend(batch)

                # 如果没有下一页，退出循环
                if not cursor:
                    break
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        i_len = len(images)
        logger.success(f"找到 {i_len} 张相关图片{'s' if i_len > 1 else ''}")
        return images

    def _build_variables(self, pin_id: str, cursor: str = None) -> Dict[str, Any]:
        """构建GraphQL变量"""
        variables = {
            "pinId": pin_id,
            "count": 12,
            "source": None,
            "searchQuery": None,
            "topLevelSource": None,
            "topLevelSourceDepth": None,
            "contextPinIds": None,
            "isDesktop": True
        }

        if cursor:
            variables["cursor"] = cursor

        return variables

    async def _fetch_batch(self, pin_id: str, cursor: str = None) -> tuple:
        """获取一批数据"""
        variables = self._build_variables(pin_id, cursor)
        query_hash = "a24165ab531bf5e03fa822c022620fd6e3104759d690e59413a3f097f9e8f751"

        for t in (15, 30, 40, 50, 60):
            try:
                r = await self.client.client.post(
                    'https://www.pinterest.com/_graphql/',
                    json={
                        "queryHash": query_hash,
                        "variables": variables
                    }
                )
                data = r.json()

                # 提取数据和下一页信息
                result = data['data']['v3RelatedPinsForPinSeoQuery']['data']['connection']
                batch = [edge['node'] for edge in result['edges']]
                page_info = result['pageInfo']

                # 如果没有下一页，返回None作为cursor
                next_cursor = page_info['endCursor'] if page_info['hasNextPage'] else None

                return batch, next_cursor

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                await asyncio.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"获取相关图片失败: pin_id={pin_id}")