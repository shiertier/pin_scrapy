import httpx
import time
import urllib.parse
import asyncio
from http.cookies import SimpleCookie
from fake_useragent import UserAgent
from config import VER
from utils import logger
from typing import List, Dict, Any
import json
from bs4 import BeautifulSoup

class Board:
    """画板操作类"""

    def __init__(self, client):
        """
        初始化画板操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get(self, board_id, uname=None, board_slug=None, section_slug=None):
        """
        获取画板内容

        参数:
            board_id: 画板ID
            uname: 用户名
            board_slug: 画板slug
            section_slug: 分区slug
        """
        board = {
            'board': {
                'id': board_id,
            },
            'section': None
        }
        if uname and board_slug:
            shortform = '/'.join([uname, board_slug, section_slug]) if section_slug else '/'.join([uname, board_slug])
        else:
            shortform = None
        bookmark = None
        images = []

        while bookmark != '-end-':
            options = self._build_options(board, section_slug, bookmark)

            # 显示进度
            i_len = len(images) - 1 if len(images) > 0 else 0
            logger.debug(f"获取所有图片 [ {i_len} / ? ]")

            # 发送请求获取数据
            try:
                batch, bookmark = await self._fetch_batch(options, shortform)
                images.extend(batch)
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        i_len = len(images)
        logger.success(f"找到 {i_len} 张图片{'s' if i_len > 1 else ''}")
        return images

    def _build_options(self, board, section_slug, bookmark=None):
        """构建请求参数"""
        options = {
            'isPrefetch': 'false',
            'board_id': board['board']['id'],
            'field_set_key': 'react_grid_pin',
            'filter_section_pins': 'true',
            'layout': 'default',
            'page_size': 25,
            'redux_normalize_feed': 'true',
        }

        if section_slug:
            options.update({'section_id': board['section']['id']})
        if bookmark:
            options.update({'bookmarks': [bookmark]})

        return options

    async def _fetch_batch(self, options, shortform=None):
        """获取一批数据"""
        post_d = urllib.parse.urlencode({
            'data': {
                'options': options,
                'context': {}
            },
            '_': int(time.time()*1000)
        }).replace('+', '').replace('%27', '%22').replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

        for t in (15, 30, 40, 50, 60):
            try:
                r = await self.client.client.get(
                    'https://www.pinterest.com/resource/BoardFeedResource/get/',
                    params=post_d
                )
                data = r.json()
                batch = data['resource_response']['data']
                bookmark = data['resource']['options']['bookmarks'][0]
                return batch, bookmark

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                await asyncio.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"获取此板块/分区失败: {shortform}")

class AccountBoards:
    """账号画板操作类"""

    def __init__(self, client):
        """
        初始化账号画板操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get_all(self, username: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有画板

        参数:
            username: 用户名
        返回:
            画板列表
        """
        bookmark = None
        boards = []

        while bookmark != '-end-':
            options = self._build_options(username, bookmark)

            # 显示进度
            b_len = len(boards) - 1 if len(boards) > 0 else 0
            logger.debug(f"获取所有板块 [ {b_len} / ? ]")

            try:
                batch, bookmark = await self._fetch_batch(options, username)
                boards.extend(batch)
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        b_len = len(boards)
        logger.success(f"找到 {b_len} 个板块{'s' if b_len > 1 else ''}")
        return boards

    def _build_options(self, username: str, bookmark: str = None) -> Dict[str, Any]:
        """构建请求参数"""
        options = {
            'isPrefetch': 'false',
            'privacy_filter': 'all',
            'sort': 'alphabetical',
            'field_set_key': 'profile_grid_item',
            'username': username,
            'page_size': 25,
            'group_by': 'visibility',
            'include_archived': 'true',
            'redux_normalize_feed': 'true',
        }

        if bookmark:
            options.update({'bookmarks': [bookmark]})

        return options

    async def _fetch_batch(self, options: Dict[str, Any], username: str) -> tuple:
        """获取一批数据"""
        post_d = urllib.parse.urlencode({
            'source_url': username,
            'data': {
                'options': options,
                'context': {}
            },
            '_': int(time.time()*1000)
        }).replace('+', '').replace('%27', '%22').replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

        for t in (15, 30, 40, 50, 60):
            try:
                r = await self.client.client.get(
                    'https://www.pinterest.com/resource/BoardsResource/get/',
                    params=post_d
                )
                data = r.json()
                batch = data['resource_response']['data']
                bookmark = data['resource']['options']['bookmarks'][0]
                return batch, bookmark

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                await asyncio.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"获取此用户名失败: {username}")

class BoardRelated:
    """相关画板图片操作类"""

    def __init__(self, client):
        """
        初始化相关画板图片操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get(self, board_id: str) -> List[Dict[str, Any]]:
        """
        获取相关画板的图片

        参数:
            board_id: 画板ID
        返回:
            图片列表
        """
        bookmark = None
        images = []

        while bookmark != '-end-':
            options = self._build_options(board_id, bookmark)

            # 显示进度
            i_len = len(images) - 1 if len(images) > 0 else 0
            logger.debug(f"获取相关图片 [ {i_len} / ? ]")

            try:
                batch, bookmark = await self._fetch_batch(options)
                images.extend(batch)
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        i_len = len(images)
        logger.success(f"找到 {i_len} 张相关图片{'s' if i_len > 1 else ''}")
        return images

    def _build_options(self, board_id: str, bookmark: str = None) -> Dict[str, Any]:
        """构建请求参数"""
        # options = {
        #     'isPrefetch': 'false',
        #     'board_id': board_id,
        #     'field_set_key': 'react_grid_pin',  # 与Board类保持一致
        #     'page_size': 25,
        #     'redux_normalize_feed': 'true',
        # }
        options = {
            "add_vase": 'true',
            'id': board_id,
            'type': 'board',
            "__track__referrer": 20,
        }
        if bookmark:
            options.update({'bookmarks': [bookmark]})

        return options

    async def _fetch_batch(self, options: Dict[str, Any]) -> tuple:
        """获取一批数据"""
        post_d = urllib.parse.urlencode({
            'data': {
                'options': options,
                'context': {}
            },
            '_': int(time.time()*1000)
        }).replace('+', '').replace('%27', '%22').replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

        for t in (15, 30, 40, 50, 60):
            try:
                r = await self.client.client.get(
                    'https://www.pinterest.com/resource/BoardContentRecommendationResource/get',
                    params=post_d
                )
                data = r.json()
                batch = data['resource_response']['data']
                bookmark = data['resource']['options']['bookmarks'][0]
                return batch, bookmark

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                await asyncio.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"获取相关图片失败: board_id={options['board_id']}")

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

class PicData:
    """图片数据操作类"""

    def __init__(self, client):
        """
        初始化图片数据操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get(self, pin_id: str) -> Dict[str, Any]:
        """
        获取图片详细数据

        参数:
            pin_id: 图片ID
        返回:
            图片详细数据
        """
        try:
            r = await self.client.client.get(
                f"https://www.pinterest.com/pin/{pin_id}/"
            )

            # 解析HTML获取数据
            soup = BeautifulSoup(r.text, "html.parser")

            # 查找包含数据的script标签
            for script in soup.find_all("script"):
                if script.get("data-relay-response") == "true":
                    data = json.loads(script.string)
                    pin_data = data["response"]["data"]["v3GetPinQuery"]["data"]
                    return pin_data

            raise Exception("Pin data not found")

        except Exception as e:
            logger.error(f"获取图片数据失败: {e}")
            raise Exception(f"获取图片数据失败: pin_id={pin_id}")

class SearchBoards:
    """画板搜索操作类"""

    def __init__(self, client):
        """
        初始化画板搜索操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get_all(self, query: str) -> List[str]:
        """
        搜索画板

        参数:
            query: 搜索关键词
        返回:
            画板ID列表
        """
        bookmark = None
        board_ids = set()  # 使用set去重

        while True:
            # 显示进度
            b_len = len(board_ids)
            logger.debug(f"获取搜索结果 [ {b_len} / ? ]")

            try:
                batch, bookmark = await self._fetch_batch(query, bookmark)
                # 提取画板ID并添加到集合中
                for board in batch:
                    board_ids.add(board['id'])

                # 如果没有下一页，退出循环
                if bookmark == "-end-" or bookmark == '%22-end-%22':
                    break
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        b_len = len(board_ids)
        logger.success(f"找到 {b_len} 个画板{'s' if b_len > 1 else ''}")
        return list(board_ids)

    def _build_options(self, query: str, bookmark: str = None) -> Dict[str, Any]:
        """构建请求参数"""
        options = {
            'applied_unified_filters': None,
            'appliedProductFilters': "---",
            'article': None,
            'auto_correction_disabled': False,
            'corpus': None,
            'customized_rerank_type': None,
            'domains': None,
            'dynamicPageSizeExpGroup': "enabled_275",
            'filters': None,
            'journey_depth': None,
            'page_size': None,
            'price_max': None,
            'price_min': None,
            'query_pin_sigs': None,
            'query': query,
            'redux_normalize_feed': True,
            'request_params': None,
            'rs': "content_type_filter",
            'scope': "boards",
            'selected_one_bar_modules': None,
            'seoDrawerEnabled': False,
            'source_id': None,
            'source_module_id': None,
            'source_url': f"/search/boards/?q={urllib.parse.quote(query)}&rs=content_type_filter",
            'top_pin_id': None,
            'top_pin_ids': None
        }

        if bookmark:
            options['bookmarks'] = [bookmark]

        return options

    async def _fetch_batch(self, query: str, bookmark: str = None) -> tuple:
        """获取一批数据"""
        options = self._build_options(query, bookmark)

        post_d = urllib.parse.urlencode({
            'data': {
                'options': options,
                'context': {}
            },
            '_': int(time.time()*1000)
        }).replace('+', '').replace('%27', '%22').replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

        for t in (15, 30, 40, 50, 60):
            try:
                r = await self.client.client.get(
                    'https://www.pinterest.com/resource/BaseSearchResource/get/',
                    params=post_d
                )
                data = r.json()
                batch = data['resource_response']['data']['results']
                bookmark = data['resource']['options']['bookmarks'][0]
                return batch, bookmark

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                await asyncio.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"搜索画板失败: query={query}")

class SearchPics:
    """图片搜索操作类"""

    def __init__(self, client):
        """
        初始化图片搜索操作类

        参数:
            client: PinterestClient实例
        """
        self.client = client

    async def get_all(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索图片

        参数:
            query: 搜索关键词
        返回:
            图片列表
        """
        bookmark = None
        images = []

        while True:
            # 显示进度
            i_len = len(images)
            logger.debug(f"获取搜索结果 [ {i_len} / ? ]")

            try:
                batch, bookmark = await self._fetch_batch(query, bookmark)
                images.extend(batch)

                # 如果没有下一页，退出循环
                if bookmark == "-end-" or bookmark == '%22-end-%22':
                    break
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break

        i_len = len(images)
        logger.success(f"找到 {i_len} 张图片{'s' if i_len > 1 else ''}")
        return images

    def _build_options(self, query: str, bookmark: str = None) -> Dict[str, Any]:
        """构建请求参数"""
        options = {
            'applied_unified_filters': None,
            'appliedProductFilters': "---",
            'article': None,
            'auto_correction_disabled': False,
            'corpus': None,
            'customized_rerank_type': None,
            'domains': None,
            'dynamicPageSizeExpGroup': None,
            'filters': None,
            'journey_depth': None,
            'page_size': None,
            'price_max': None,
            'price_min': None,
            'query_pin_sigs': None,
            'query': query,
            'redux_normalize_feed': True,
            'request_params': None,
            'rs': "content_type_filter",
            'scope': "pins",  # 与SearchBoards的区别
            'selected_one_bar_modules': None,
            'seoDrawerEnabled': False,
            'source_id': None,
            'source_module_id': None,
            'top_pin_id': None,
            'top_pin_ids': None
        }

        if bookmark:
            options['bookmarks'] = [bookmark]

        return options

    async def _fetch_batch(self, query: str, bookmark: str = None) -> tuple:
        """获取一批数据"""
        options = self._build_options(query, bookmark)

        post_d = urllib.parse.urlencode({
            'data': {
                'options': options,
                'context': {}
            },
            '_': int(time.time()*1000)
        }).replace('+', '').replace('%27', '%22').replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

        for t in (15, 30, 40, 50, 60):
            try:
                r = await self.client.client.get(
                    'https://www.pinterest.com/resource/BaseSearchResource/get/',
                    params=post_d
                )
                data = r.json()

                # 修正数据提取路径
                batch = data['resource_response']['data']['results']
                bookmark = data['resource_response'].get('bookmark')  # 使用get避免KeyError

                # 如果没有bookmark，说明是最后一页
                if not bookmark:
                    bookmark = '-end-'

                return batch, bookmark

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"请求超时,重试中... ({t}s)")
                await asyncio.sleep(5)
                if t == 60:  # 最后一次重试失败
                    raise Exception(f"搜索图片失败: query={query}")

class PinterestClient:
    """Pinterest API客户端"""

    def __init__(self, ver_i=2, proxies=None, cookie_file=None):
        """
        初始化Pinterest客户端

        参数:
            ver_i: API版本索引
            proxies: 代理设置
            cookie_file: cookie文件路径
        """
        self.ver_i = ver_i
        self.proxies = proxies
        self.cookie_file = cookie_file
        self.ua = UserAgent()
        self.client = None
        self.pic_data = PicData(self)  # 初始化图片数据操作实例
        self.pic_related = PicRelated(self)  # 初始化相关图片操作实例
        self.board = Board(self)  # 初始化画板操作实例
        self.board_related = BoardRelated(self)  # 初始化相关画板操作实例
        self.account_boards = AccountBoards(self)  # 初始化账号画板操作实例
        self.search_boards = SearchBoards(self)  # 初始化画板搜索操作实例
        self.search_pics = SearchPics(self)  # 初始化图片搜索操作实例

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.client:
            await self.client.aclose()

    async def connect(self):
        """建立连接"""
        # 处理cookie
        cookies = None
        if self.cookie_file:
            try:
                with open(self.cookie_file) as f:
                    rawdata = f.read()
                my_cookie = SimpleCookie()
                my_cookie.load(rawdata)
                cookies = {key: morsel.value for key, morsel in my_cookie.items()}
            except Exception as e:
                logger.warning(f"读取cookie文件失败: {e}")

        # 设置headers
        headers = {
            'User-Agent': self.ua.chrome,
            'Accept': 'application/json, text/javascript, */*, q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.pinterest.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'X-APP-VERSION': VER[self.ver_i] if self.ver_i in (1, 2) else None,
            'X-Pinterest-AppState': 'active',
            'X-Pinterest-PWS-Handler': 'www/[username]/[slug]/[section_slug].js',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'Trailers'
        }

        # 创建异步客户端
        self.client = httpx.AsyncClient(
            headers=headers,
            cookies=cookies,
            proxies=self.proxies,
            timeout=60.0,
            follow_redirects=True
        )