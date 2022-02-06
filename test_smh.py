from pathlib import Path
import pytest
from smh_parse import SMHParse
import re


def get_ts(file_name):
    return re.search("([0-9]{14})", file_name).group(1)

def test_extract_json():

    for file in Path("fixtures/valid").glob("smh_*.html"):
        ts =  get_ts(file.name)
        html = read_html(file.resolve())
        smh = SMHParse()
        js = smh._extract_json(html, ts)
        keys_found = len(js.keys())
        assert keys_found in [32,33]

class Response():
    def __init__(self, html, ts):
        self.body = html
        self.meta = {'snapshot': [None, ts]}

def test_broken_json_fails_gracefully():
    ts = "20210116225909"
    f = f"fixtures/errors/smh_{ts}.html"
    html = read_html(f)
    smh = SMHParse()
    data = smh.parse(Response(html,ts))
    assert data == []

    

def test_articles():
    for file in Path("fixtures/valid").glob("smh_*.html"):
        ts = get_ts(file.name)
        html = read_html(file.resolve())
        smh = SMHParse()
        js = smh._extract_json(html, ts)
        articles = list(smh._extract_articles(js))
        assert len(articles) > 20

def read_html(file):
    data = open(file,"r", encoding="utf8").read()
    if data[0:2] == '\'b' or data[0:2] == "b\'":
        return data[2:-1]
    return data