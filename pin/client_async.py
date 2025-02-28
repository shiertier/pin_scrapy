import httpx
from http.cookies import SimpleCookie
from fake_useragent import UserAgent
from .config import VER
from .utils import logger
from .subclass_async.board import Board
from .subclass_async.account_boards import AccountBoards
from .subclass_async.board_related import BoardRelated
from .subclass_async.pic_related import PicRelated
from .subclass_async.pic_data import PicData
from .subclass_async.search_boards import SearchBoards
from .subclass_async.search_pics import SearchPics


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