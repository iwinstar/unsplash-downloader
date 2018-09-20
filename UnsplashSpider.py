# -*- author: iwinstar -*-
# -*- encoding: utf-8 -*-
# -*- datetime: 2018/09/10 08:09:08 -*-

import scrapy
import sqlite3
import threading
import datetime
import json
import sys

from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

reload(sys)
sys.setdefaultencoding('utf8')


class UnsplashSpider(scrapy.Spider):
    name = "UnsplashSpider"

    COLOR_GREEN = '\033[92m'
    COLOR_RED = '\033[91m'
    COLOR_END = '\033[0m'

    db_file = "database/picture.db"
    cp_file = "checkpoint/spider"

    def __init__(self):
        super(UnsplashSpider, self).__init__()

        self.time_begin = datetime.datetime.now()
        self.time_end = None

        self.page_begin = 1
        self.page_end = 2700
        self.page_size = 30
        self.page_step = 30
        self.page_items = {}
        self.check_point = None

        self.initial_page()
        self.initial_table()

        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def start_requests(self):

        # use official client_id inside Chrome plugin
        url_pre = "https://api.unsplash.com/photos/?client_id="
        client_id = "fa60305aa82e74134cabc7093ef54c8e2c370c47e73152f72371c828daedfcd7"
        url_page, url_page_size = "&page=", "&per_page=" + str(self.page_size)

        conn = sqlite3.connect(self.db_file)
        semaphore = threading.Semaphore(1)

        # spider pictures and store them in database
        for page_index in range(self.page_begin, self.page_end + 1):
            yield scrapy.Request(url=url_pre + client_id + url_page + str(page_index) + url_page_size,
                                 callback=lambda response, conn=conn, semaphore=semaphore, page_index=page_index:
                                 self.save_data(response, conn, semaphore, page_index))

    def parse(self, response):
        pass

    def save_data(self, response, conn, semaphore, page_index):
        pictures = json.loads(response.body_as_unicode())
        self.page_items[page_index] = len(pictures)

        print "%sSpider page: %4d, pictures: %2d%s" % \
              (self.COLOR_RED, page_index, len(pictures), self.COLOR_END)

        if pictures:
            for picture in pictures:
                id_str = picture["id"]
                created_at = datetime.datetime.strptime(picture["created_at"][0:19], '%Y-%m-%dT%H:%M:%S')
                updated_at = datetime.datetime.strptime(picture["updated_at"][0:19], '%Y-%m-%dT%H:%M:%S')
                width = picture["width"]
                height = picture["height"]
                color = picture["color"]
                description = str(picture["description"]).replace('"', "'")
                likes = picture["likes"]
                user_name = str(picture["user"]["name"]).replace('"', "'")
                url = picture["urls"]["raw"]
                pre = url.split('/')[-1]
                pre = pre.split('?')[0]
                file_name = pre if pre.split(".")[-1] in ["jpg", "png"] else pre + ".jpg"

                sql = 'insert into picture values ("%s", "%s", "%s", %s, %s, "%s", "%s", %s, "%s", "%s", "%s");' \
                      % (id_str, created_at, updated_at, width, height, color,
                         description, likes, user_name, file_name, url)

                conn.execute(sql)

            semaphore.acquire()
            conn.commit()
            semaphore.release()

    def initial_page(self):
        with open(self.cp_file, 'r') as fr:
            checkpoint = fr.read()
            fr.close()

        if checkpoint:
            self.page_end = int(checkpoint) + self.page_step

    def initial_table(self):
        conn = sqlite3.connect(self.db_file)

        # prepare database
        conn.execute("drop table if exists picture")
        conn.execute("create table if not exists picture ("
                     "id varchar(255),"
                     "created_at datetime,"
                     "updated_at datetime,"
                     "width integer,"
                     "height integer,"
                     "color varchar(10),"
                     "description varchar(255),"
                     "likes integer,"
                     "user_name varchar(255),"
                     "file_name varchar(255),"
                     "url varchar(255));")
        conn.execute("vacuum")
        conn.close()

    def spider_closed(self, spider):
        # record checkpoint
        for (page_index, page_item) in self.page_items.items():
            if 0 < page_item < self.page_size:
                self.check_point = page_index

        if not self.check_point:
            self.check_point = self.page_end

        with open(self.cp_file, 'w') as fw:
            fw.write(str(self.check_point))
            fw.close()

        # query statistics
        conn = sqlite3.connect(self.db_file)
        cursor = conn.execute("select count(*) from picture")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        self.time_end = datetime.datetime.now()
        seconds = (self.time_end - self.time_begin).total_seconds()
        hms = "{:0>8}".format(datetime.timedelta(seconds=seconds))

        print "%sPage: %s -> %s, Checkpoint: %s, Total spider pictures: %s, Total Time: %s%s" % \
              (self.COLOR_GREEN, self.page_begin, self.page_end,
               self.check_point, count, hms, self.COLOR_END)
