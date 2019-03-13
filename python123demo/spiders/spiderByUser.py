import random
import scrapy
import tomd

from python123demo.redistool.connectionPool import redisConnectionPool
from python123demo.userItem import UserItem


class mingyan(scrapy.Spider):
    name = "runSpiderByUser"
    redisConnection = redisConnectionPool()
    redis = redisConnection.getClient()
    user_agent_list = [ \
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1" \
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11", \
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6", \
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6", \
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1", \
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5", \
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5", \
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3", \
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3", \
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3", \
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3", \
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3", \
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3", \
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3", \
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3", \
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3", \
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24", \
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
    ]
    allowed_domains = ["juejin.im"]
    ua = random.choice(user_agent_list)

    headers = {
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://gupiao.baidu.com/',
        'User-Agent': ua
    }
    def start_requests(self):
        urls = ['https://juejin.im']
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, headers=self.headers)

    def parse(self, response):

        nextPage = response.css("a::attr(href)").extract()
        for i in range(len(nextPage)):
            url = random.choice(nextPage)
            if url is not None:
                parseUrl = response.urljoin(url)
                if "juejin.im" in str(parseUrl):
                    if self.insertRedis(url) == False:
                        yield scrapy.Request(url=parseUrl, callback=self.parse,headers=self.headers,dont_filter=False)
            nextPage.remove(url)

        length = str(response.url).split("/")
        if "/user/" in response.url and len(length) == 5:
            userItem = UserItem()

            # 用户id
            userItem['id'] = length[4]

            # 用户名
            userItem['username'] = self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.major-area > div.user-info-block.block.shadow > div.info-box.info-box > div.top > h1::text").extract_first())

            # 注册时间
            userItem['registerTime'] = self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.minor-area > div > div.more-block.block > div > div.item-count > time::text").extract_first())
            userItem['registerTime'] = str(userItem['registerTime']).replace("年", "-").replace("月", "-").replace("日", "")

            # 标签
            userItem['tag'] = self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.major-area > div.user-info-block.block.shadow > div.info-box.info-box > div.position > span > span::text").extract())

            # 简介
            userItem['brief'] = self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.major-area > div.user-info-block.block.shadow > div.info-box.info-box > div.intro > span::text").extract_first())

            # 发布文章数量
            userItem['publishedArticlesNum'] = self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.major-area > div.list-block > div > div.list-header > div > a:nth-child(3) > div.item-count::text").extract_first())

            # 沸点文章数量
            userItem['hotNum'] = self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.major-area > div.list-block > div > div.list-header > div > a:nth-child(4) > div.item-count::text").extract_first())

            # 分享文章数量
            userItem['shareNum'] = self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.major-area > div.list-block > div > div.list-header > div > a:nth-child(5) > div.item-count::text").extract_first())

            # 对别人的文章点赞数量
            userItem["initiatePraise"] = self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.major-area > div.list-block > div > div.list-header > div > div:nth-child(6) > div:nth-child(2)::text").extract_first())

            # 发布小册数量
            userItem['publishedBookNum'] = self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.major-area > div.list-block > div > div.list-header > div > a:nth-child(8) > div.item-count::text").extract_first())

            # 共获赞数量
            userItem['praiseCountNum'] = str(self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.minor-area > div > div.stat-block.block.shadow > div.block-body > div:nth-child(2) > span > span::text").extract_first())).replace(",","")

            # 所有文章共被阅读次数
            userItem['articleReadCountNum'] = str(self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.minor-area > div > div.stat-block.block.shadow > div.block-body > div:nth-child(3) > span > span::text").extract_first())).replace(",","")

            # 一共关注了多少人
            userItem['attentionPeopleNum'] = str(self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.minor-area > div > div.follow-block.block.shadow > a:nth-child(1) > div.item-count::text").extract_first())).replace(",","")

            # 有多少人关注了这个用户（粉丝）
            userItem['fans'] = str(self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.minor-area > div > div.follow-block.block.shadow > a:nth-child(2) > div.item-count::text").extract_first())).replace(",","")

            # 收藏的文章数量
            userItem['collectArticleNum'] = str(self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.minor-area > div > div.more-block.block > a:nth-child(1) > div.item-count::text").extract_first())).replace(",","")

            # 关注的标签数量
            userItem['attentionTagNum'] = str(self.parseInt(response.css("#juejin > div.view-container > main > div.view.user-view > div.minor-area > div > div.more-block.block > a:nth-child(2) > div.item-count::text").extract_first())).replace(",","")

            yield userItem

    def parseToMarkdown(self, param):
        return tomd.Tomd(str(param)).markdown

    def parseInt(self, param):
        if param == None:
            return 0
        else:
            return param



    # url 存入redis，如果能存那么就没有该链接，如果不能存，那么就存在该链接

    def insertRedis(self, url):
        if self.redis != None:
            result = self.redis.sadd("urlList", url)
            if result == 1:
                return True
            else:
                return False
        else:
            self.redis = self.redisConnection.getClient()
            self.insertRedis(url)