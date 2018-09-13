# -*- author: steve.cmm
# -*- encoding: utf-8 -*-
# Usage: scrapy runspider UnsplashSpider.py

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

    db_file = "database/picture.db"
    cp_file = "checkpoint/spider"

    def __init__(self):
        self.spider_begin = 1
        self.spider_end = 2700

        self.initial_range()
        self.initial_table()

        dispatcher.connect(self.closed, signals.spider_closed)

    def start_requests(self):

        # use official client_id inside Chrome plugin
        url_pre = "https://api.unsplash.com/photos/?client_id="  #
        client_id = "fa60305aa82e74134cabc7093ef54c8e2c370c47e73152f72371c828daedfcd7"
        url_page, url_page_size = "&page=", "&per_page=30"

        conn = sqlite3.connect(self.db_file)
        semaphore = threading.Semaphore(1)

        # scrapy pictures and store them in database
        for i in range(self.spider_begin, self.spider_end):
            yield scrapy.Request(url=url_pre + client_id + url_page + str(i) + url_page_size,
                                 callback=lambda response, conn=conn, semaphore=semaphore, page=str(i):
                                 self.save_data(response, conn, semaphore, page))

    def parse(self, response):
        pass

    def save_data(self, response, conn, semaphore, page):
        pictures = json.loads(response.body_as_unicode())

        if pictures:

            # store checkpoint
            if len(pictures) < 30:
                with open(self.cp_file, 'w') as f:
                    f.write(page)
                    f.close()

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

                select_sql = "select count(*) from picture where id = '%s'" % id_str
                cursor = conn.execute(select_sql)

                if cursor.fetchone()[0]:
                    sql = "update picture set likes = %s where id = '%s'" % (likes, id_str)
                else:
                    sql = 'insert into picture values ("%s", "%s", "%s", %s, %s, "%s", "%s", %s, "%s", "%s", "%s");' \
                          % (id_str, created_at, updated_at, width, height, color,
                             description, likes, user_name, file_name, url)

                conn.execute(sql)

            semaphore.acquire()
            conn.commit()
            semaphore.release()

    def initial_range(self):
        with open(self.cp_file, 'r') as f:
            checkpoint = f.read()

            if checkpoint:
                self.spider_begin = int(checkpoint)
                self.spider_end = int(checkpoint) + 10

            f.close()

    def initial_table(self):
        conn = sqlite3.connect(self.db_file)

        # prepare database
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
        conn.close()

    def closed(self, spider):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.execute("select count(*) from picture")
        print "Total spider pictures: " + str(cursor.fetchone()[0])

        cursor.close()
        conn.close()
