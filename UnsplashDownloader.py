# -*- author: iwinstar -*-
# -*- encoding: utf-8 -*-
# -*- datetime: 2018/09/10 08:10:08 -*-

import sqlite3
import urllib
import threadpool
import os
import time
import sys
from PIL import Image


class UnsplashDownloader:
    def __init__(self, pictures, folder, threads=10):
        self.pictures = pictures
        self.folder = folder
        self.threads = threads

    def run(self):
        # use thread pool to download pictures
        pool = threadpool.ThreadPool(self.threads)
        requests = threadpool.makeRequests(self.downloader, self.pictures)
        [pool.putRequest(req) for req in requests]
        pool.wait()

    def downloader(self, created_at, file_name, url):
        try:
            full_name = self.folder + '/' + file_name

            if os.path.exists(full_name):
                print '%s exits.' % file_name
            else:
                # download file
                print 'Downloading: %s' % file_name

                urllib.urlretrieve(url, full_name)

                # initialize change_time to picture's upload_time
                change_time = time.mktime(time.strptime(created_at, '%Y-%m-%d %H:%M:%S'))

                # get picture's last modified time stored in exif
                try:
                    exif = Image.open(full_name)._getexif()

                    if exif and exif.get(306):
                        # python don't provide interface to change file's create_time under mac
                        # so, here we just modify change_time, known as ctime
                        # more introduction about exif format: http://www.exiv2.org/tags.html
                        change_time = time.mktime(time.strptime(exif.get(306), '%Y:%m:%d %H:%M:%S'))
                except Exception, e:
                    print "%s exception %s" % (file_name, e)

                os.utime(full_name, (change_time, change_time))
        except urllib.ContentTooShortError:
            print 'Network Error, re-download:' + url
            self.downloader(created_at, file_name, url)


if __name__ == "__main__":

    COLOR_BEGIN = '\033[93m'
    COLOR_END = '\033[0m'

    db_file = "database/picture.db"
    cp_file = "checkpoint/download"

    # get params
    folder_path = sys.argv[1]

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    # read checkpoint
    condition = None
    with open(cp_file, 'r') as fr:
        checkpoint = fr.read()
        fr.close()

    if checkpoint:
        condition = "where created_at > '%s'" % checkpoint

    # get all picture urls
    conn = sqlite3.connect(db_file)
    cursor = conn.execute("select created_at, file_name, url from picture %s order by created_at asc" % condition)

    pictures = []
    for picture in cursor:
        pictures.append((list(picture), None))
        checkpoint = picture[0]

    # threads shouldn't be very large
    pd = UnsplashDownloader(pictures, folder_path, threads=10)
    pd.run()

    # record checkpoint
    with open(cp_file, 'w') as fw:
        fw.write(checkpoint)
        fw.close()

    print "%sCheckpoint: %s, Download %s pictures%s" % (COLOR_BEGIN, checkpoint, len(pictures), COLOR_END)
