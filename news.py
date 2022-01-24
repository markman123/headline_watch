from datetime import timedelta, datetime
import logging
import os
import sys
from threading import Thread
from tracemalloc import Snapshot
from typing import List, Tuple, Dict
import requests
import scrapy


class NewsSpider(scrapy.Spider):
    name = "news"

    def start_requests(self):
        url = "news.com.au"
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s",)
        start_date = datetime(2021,1,1)
        end_date = datetime.now()
        snapshots = all_snapshots(url, start_date, end_date)
        for snapshot in snapshots:
            ts_str = snapshot[1]
            file_output = f"output/news_{ts_str}.html"
            if os.path.exists(file_output):
                continue
            url = snapshot[2]
            wm_url = f"https://web.archive.org/web/{ts_str}/{url}"
            yield scrapy.Request(url=wm_url, callback=self.parse, meta={"snapshot": snapshot})
    
    def parse(self, response):
        ts_str = response.meta['snapshot'][1]
        file_output = f"output/news_{ts_str}.html"
        logging.debug(f"Saving file: {file_output}")
        if not os.path.exists("output"):
            os.mkdir("output")
        print(response.body, file=open(file_output,"w",encoding="utf8"))

    

def all_snapshots(url: str, start_date: datetime, end_date: datetime) -> List[List[str]]:
    ts_start = start_date.strftime("%Y%m%d%H%M%S")
    ts_end = end_date.strftime("%Y%m%d%H%M%S")
    cdx_url = f"https://web.archive.org/cdx/search/cdx?url={url}&from={ts_start}&to={ts_end}"
    resp = requests.get(cdx_url)
    return parse_cdx(resp.text)

def parse_cdx(txt: str) -> List[List[str]]:
    lines: List[str] = txt.splitlines(keepends=False)
    split_lines = [line.split(" ") for line in lines]
    filtered = [line for line in split_lines if line[3] == "text/html"]
    return filtered

