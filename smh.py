from datetime import timedelta, datetime
import logging
import os
import sys
from typing import List, Tuple, Dict
from itsdangerous import json
import requests
import scrapy
import re


class SMHSpider(scrapy.Spider):
    name = "smh"

    def start_requests(self):
        url = "smh.com.au"
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s",)
        start_date = datetime(2021,1,1)
        end_date = datetime.now()
        snapshots = all_snapshots(url, start_date, end_date)[:10]
        for snapshot in snapshots:
            ts_str = snapshot[1]
            file_output = f"output/smh_{ts_str}.html"
            if os.path.exists(file_output):
                continue
            url = snapshot[2]
            wm_url = f"https://web.archive.org/web/{ts_str}id_/{url}"
            yield scrapy.Request(url=wm_url, callback=self.parse, meta={"snapshot": snapshot})
    
    def download(self, response):
        ts_str = response.meta['snapshot'][1]
        file_output = f"output/smh_{ts_str}.html"
        logging.debug(f"Saving file: {file_output}")
        if not os.path.exists("output"):
            os.mkdir("output")
        print(response.body, file=open(file_output,"w",encoding="utf8"))
    
    def parse(self, response):
        ts = response.meta['snapshot'][1]
        raw = re.search("INITIAL_STATE = (JSON.parse\()?(.+?)(\))?;?<",str(response.body))
        if raw is None:
            logging.info(f"No JSON in {ts}")
            yield {"snapshot": ts}
        
        raw = raw.group(2)
        j = json.loads(json.loads(raw.replace("\\\\(.)", r"\1")))
        content_unit_groups = [ug for ug in j['page']['/']['index']['contentUnitGroups'] if ug['label'] in ["News well","Everything else"]]
        
        for content_unit_group in content_unit_groups:
            cug_type = content_unit_group['label']
            units = content_unit_group['contentUnits']
            for content_unit in units:
                content_unit_id = content_unit['id']
                for asset in content_unit['assets']:
                    if asset['assetType'] != 'article':
                        continue
                    
                    about = asset['asset']['about']
                    headline = asset['asset']['headlines']['headline']
                    byline = asset['asset']['byline']
                    word_count = asset['asset']['wordCount']
                    cat = asset['category']['name']
                    id = asset['id']
                    first_published = asset['dates']['firstPublished']
                    modified = asset['dates']['modified']
                    published = asset['dates']['published']

                    yield dict(
                        about=about,
                        headline=headline,
                        byline=byline,
                        word_count=word_count,
                        cat=cat,
                        id=id,
                        first_published=first_published,
                        modified=modified,
                        published=published,
                        cug_type=cug_type,
                        snapshot=ts,
                        content_unit_id=content_unit_id
                    ) 

        


    

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

