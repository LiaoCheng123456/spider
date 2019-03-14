import random
import scrapy
import tomd

from python123demo.articleItem import ArticleItem
from python123demo.redistool.connectionPool import redisConnectionPool


class mingyan(scrapy.Spider):
    name = "runSpiderByIndex"
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
        for i in nextPage:
            if nextPage is not None:
                url = response.urljoin(i)
                # 必须是掘金的链接才进入
                if "juejin.im" in str(url):
                    # 存入redis
                    if self.insertRedis(url) == True:
                        yield scrapy.Request(url=url, callback=self.parse,headers=self.headers,dont_filter=True)

        if "/post/" in response.url and "#comment" not in response.url:
            article = ArticleItem()

            # 文章id作为id
            article['id'] = str(response.url).split("/")[-1]

            # 标题
            article['title'] = response.css("#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > h1::text").extract_first()

            # 内容
            parameter = response.css("#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > div.article-content").extract_first()
            article['content'] = self.parseToMarkdown(parameter)

            # 作者
            article['author'] = response.css("#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > div:nth-child(6) > meta:nth-child(1)::attr(content)").extract_first()

            # 创建时间
            createTime = response.css("#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > div.author-info-block > div > div > time::text").extract_first()
            createTime = str(createTime).replace("年", "-").replace("月", "-").replace("日","")
            article['createTime'] = createTime

            # 阅读量
            article['readNum'] = int(str(response.css("#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > div.author-info-block > div > div > span::text").extract_first()).split(" ")[1])
            if article['readNum'] == None:
                article['readNum'] = 0

            # 点赞数
            badge = response.css(
                "#juejin > div.view-container > main > div > div.article-suspended-panel.article-suspended-panel > div.like-btn.panel-btn.like-adjust.with-badge::attr(badge)").extract_first()
            if badge == None:
                article['praise'] = 0
            else:
                article['praise'] = badge

            # 评论数
            article['commentNum'] = response.css("#juejin > div.view-container > main > div > div.article-suspended-panel.article-suspended-panel > div.comment-btn.panel-btn.comment-adjust.with-badge::attr(badge)").extract_first()
            if article['commentNum'] == None:
                article['commentNum'] = 0

            # 文章链接
            article['link'] = response.url

            yield article

    def parseToMarkdown(self, param):
        return tomd.Tomd(str(param)).markdown



    # url 存入redis，如果能存那么就没有该链接，如果不能存，那么就存在该链接

    def insertRedis(self, url):
        if self.redis != None:
            return self.redis.sadd("articleUrlList", url) == 1
        else:
            self.redis = self.redisConnection.getClient()
            self.insertRedis(url)