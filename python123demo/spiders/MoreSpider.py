import json
import random
import re

import scrapy
import tomd

from python123demo.articleItem import ArticleItem
from python123demo.redistool.connectionPool import redisConnectionPool
from python123demo.userItem import UserItem


class moreSpider(scrapy.Spider):
    name = "moreSpider"
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
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safri/536.3", \
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
        'User-Agent': ua,
        "X-Juejin-Src":"web"
    }

    tagId = "58c668d70ce46300547ad4df"
    pages = 1
    url = "https://timeline-merger-ms.juejin.im/v1/get_tag_entry?src=web&tagId={}&page={}&pageSize=20&sort=rankIndex"
    def start_requests(self):

        url = self.url.format(self.tagId,self.pages)
        urls = [url]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.insertQueue, headers=self.headers)

    # 预先将所有的标签url放入队列
    def insertQueue(self, response):
        tagId = self.getSpopValue()
        while tagId != None:
            tagId = self.getSpopValue()
            url = self.url.format(tagId, 1)
            yield scrapy.Request(url=url, callback=self.parse, headers=self.headers, dont_filter=True)
        self.parse(response)

    def parse(self, response):
        if "timeline-merger-ms.juejin.im/v1/get_tag_entry" in response.url:
            # 截取id和分页
            tagId = re.findall(r"https://timeline-merger-ms.juejin.im/v1/get_tag_entry\?src=web&tagId=(.+?)&", response.url)[0]
            pages = int(re.findall(r"&page=(.+?)&", response.url)[0])
            body = json.loads(str(response.body,"utf-8"))
            if "failed" not in body['m']:
                if len(body['d']['entrylist']) > 0:
                    for value in body['d']['entrylist']:
                        if "https://juejin.im/post" in value['originalUrl']:
                            yield scrapy.Request(url=value['originalUrl'], callback=self.parse, headers=self.headers, dont_filter=True)
                    # 加载数据
                    pages += 1
                    url = self.url.format(tagId, pages)
                    yield scrapy.Request(url=url, callback=self.parse, headers=self.headers,dont_filter=True)

        if "https://juejin.im/post" in response.url and "#comment" not in response.url:

            article = ArticleItem()

            # 文章id作为id
            article['id'] = str(response.url).split("/")[-1]

            # 标题
            article['title'] = response.css(
                "#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > h1::text").extract_first()

            # 内容
            parameter = response.css(
                "#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > div.article-content").extract_first()
            article['content'] = self.parseToMarkdown(parameter)

            # 作者
            article['author'] = response.css(
                "#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > div:nth-child(6) > meta:nth-child(1)::attr(content)").extract_first()

            # 创建时间
            createTime = response.css(
                "#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > div.author-info-block > div > div > time::text").extract_first()
            createTime = str(createTime).replace("年", "-").replace("月", "-").replace("日", "")
            article['createTime'] = createTime

            # 阅读量
            article['readNum'] = int(str(response.css(
                "#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > div.author-info-block > div > div > span::text").extract_first()).split(
                " ")[1])
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
            article['commentNum'] = response.css(
                "#juejin > div.view-container > main > div > div.article-suspended-panel.article-suspended-panel > div.comment-btn.panel-btn.comment-adjust.with-badge::attr(badge)").extract_first()
            if article['commentNum'] == None:
                article['commentNum'] = 0

            # 文章链接
            article['link'] = response.url

            yield article

            # 将作者链接存入队列
            yield scrapy.Request(url = response.css("#juejin > div.view-container > main > div > div.main-area.article-area.shadow > article > div:nth-child(6) > meta:nth-child(2)::attr(content)").extract_first(), callback=self.parse, headers=self.headers, dont_filter=True)


        # 用户数据
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

    def getSpopValue(self):
        if self.redis != None:
            if self.redis.exists("tagList"):
                result = eval(str(self.redis.spop("tagList"),encoding = "utf-8"))
                if result['_values']['id']:
                    return result['_values']['id']
                else:
                    return None
            else:
                return None
        else:
            self.redis = self.redisConnection.getClient()
            self.getSpopValue()

    def parseToMarkdown(self, param):
        return tomd.Tomd(str(param)).markdown

    def parseInt(self, param):
        if param == None:
            return 0
        else:
            return param


