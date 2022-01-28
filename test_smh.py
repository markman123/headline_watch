import pytest
from smh_parse import SMHParse

def test_extract_json():
    s = ["20210101021523","20210603114911", "20220101005700"]
    for ts in s:
        f = f"fixtures/smh_{ts}.html"
        html = read_html(f)
        smh = SMHParse()
        js = smh._extract_json(html, ts)
        assert len(js.keys()) == 32


def test_articles():
    s = ["20210101021523","20210603114911", "20220101005700"]
    for ts in s:
        f = f"fixtures/smh_{ts}.html"
        html = read_html(f)
        smh = SMHParse()
        js = smh._extract_json(html, ts)
        articles = list(smh._extract_articles(js))
        assert len(articles) > 20

def read_html(file):
    data = open(file,"r", encoding="utf8").read()
    if data[0:2] == '\'b':
        return data[2:-1]
    return data