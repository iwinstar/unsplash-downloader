#!/bin/sh

name=`basename $0`

cd $(cd `dirname $0`; pwd)

case $1 in

    s|spider)
        scrapy runspider UnsplashSpider.py -s LOG_ENABLED=False
        ;;
    d|download)
        if [ $# != 2 ]; then
            echo "Usage: $name [d|download] FULL_PATH_TO_STORE_PICTURES"
            exit -1
        fi

        python3 UnsplashDownloader.py "$2"
        ;;
    *)
        echo "Usage: $name [s|spider|d|download]"
        exit 1
        ;;
esac

exit 0
