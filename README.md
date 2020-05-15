# Unsplash Downloader

![language](https://img.shields.io/badge/language-Python/Shell-orange.svg)
![repo size](https://img.shields.io/github/repo-size/badges/shields.svg)
![license](https://img.shields.io/hexpm/l/plug.svg) 
![Gitter](https://img.shields.io/gitter/room/nwjs/nw.js.svg)

> Until 2020.05.15, Total spider 192607 pictures, 1.43 TiB

### Introduction
I love pictures on Unsplash uploaded by photographers worldwide. They are so beautiful and professional. I want to download them to local disk as material library, so here we are.

Unsplash provide API to access their database, but limited to 50 requests per hour. This will take 120+ hours to download them all. So I use a spider, it can get all pictures metadata within minutes, then download with multi-thread. 

### Prepare

> Notice: the follow commands should also run under this environment

```bash
# download source code
git clone https://github.com/iwinstar/unsplash-downloader.git
cd unsplash-downloader

# install dependency
pip3 install -r requirements.txt
```

### Usage
#### Step 1: Spider

Spider pictures, and store metadata in local database.

```bash
scrapy runspider UnsplashSpider.py
```

or

```bash
./unsplash.sh s
./unsplash.sh spider
```

or

```bash
alias us="/Users/xxx/git/unsplash-downloader/unsplash.sh"
us s
us spider
```

#### Step 2: Download

download pictures with 10 threads by default. 

It will modify local file's change time to picture's last modify time stored in exif.

```bash
python3 UnsplashDownloader.py FULL_PATH_TO_STORE_PICTURES
```

or

```bash
./unsplash.sh d path
./unsplash.sh download path
```

or
```bash
alias us="/Users/xxx/git/unsplash-downloader/unsplash.sh"
us d path
us download path
```
