from datetime import timedelta, datetime
import logging
import os
import sys
from typing import List, Tuple, Dict
import requests


def download_archives(url: str, start_date: datetime, end_date:datetime):
    snapshots = all_snapshots(url, start_date, end_date)
    download_snapshots(snapshots)

def download_snapshots(snapshots: List[List[str]]):
    logging.info(f"Downloads to complete: {len(snapshots)}")
    for snapshot in snapshots:
        if os.path.exists(f"output/smh_{snapshot[1]}.html"):
            logging.debug(f"Skipping: {snapshot[1]}")
            continue
        download_snapshot(snapshot)

def download_snapshot(snapshot: List[str]):
    ts_str = snapshot[1]
    url = snapshot[2]
    wm_url = f"https://web.archive.org/web/{ts_str}/{url}"
    resp = requests.get(wm_url)
    html = resp.text
    file_output = f"output/smh_{ts_str}.html"
    logging.debug(f"Saving file: {file_output}")
    print(html, file=open(file_output,"w",encoding="utf8"))

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

if __name__ == "__main__":
    url = "smh.com.au"
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",)
    start_date = datetime(2021,1,1)
    end_date = datetime.now()
    download_archives(url, start_date, end_date)
