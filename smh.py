from datetime import timedelta, datetime
import logging
import os
import sys
from typing import List, Tuple, Dict
import json
import requests
import scrapy
from scrapy.shell import inspect_response
import re
from smh_parse import SMHParse

class SMHSpider(scrapy.Spider):
    name = "smh"

    def start_requests(self):
        url = "smh.com.au"
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                            format="%(asctime)s [%(levelname)s] %(message)s",)
        start_date = datetime(2021, 1, 1)
        end_date = datetime.now()
        snapshots = all_snapshots(url, start_date, end_date)
        for snapshot in snapshots:
            ts_str = snapshot[1]
            file_output = f"output/smh_{ts_str}.html"
            if os.path.exists(file_output) or os.path.exists(file_output.replace("output", "errors")):
                continue
            url = snapshot[2]
            wm_url = f"https://web.archive.org/web/{ts_str}id_/{url}"
            yield scrapy.Request(url=wm_url, callback=self.parse, meta={"snapshot": snapshot})

    def download(self, response):
        ts_str = response.meta['snapshot'][1]
        file_output = f"output/smh_{ts_str}.html"
        if not os.path.exists("output"):
            os.mkdir("output")
        print(str(response.body), file=open(file_output, "w", encoding="utf8"))

    def parse(self, response):
        try:
            smh = SMHParse()
            articles = smh.parse(response)
            for article in articles:
                yield article
        except Exception as e:
            inspect_response(response, self)
            yield {"snapshot": response.meta['snapshot'][1], "error": e}

  

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
