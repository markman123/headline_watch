import re
import json
import logging
import sys
from scrapy.item import Item, Field

def except_json_parse(self, body, ts, e):
    self.logger.exception(f"Invalid JSON: {ts}")
    print(body, file=open(f"errors/smh_{ts}.html","w",encoding="utf8"))
    output = {"snapshot": ts, "error": e}
    self.js = output
    return output

class Article(Item):
    about = Field()
    headline = Field()
    byline = Field()
    word_count = Field()
    cat = Field()
    id = Field()
    first_published = Field()
    modified = Field()
    published = Field()
    cug_type = Field()
    snapshot = Field()
    content_unit_id = Field()


class SMHParse:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse(self, response):
        self.response_body = str(response.body)
        self.ts = response.meta['snapshot'][1]
        try:
            js = self._extract_json(
             str(response.body), response.meta['snapshot'][1])
            return self._extract_articles(js)
        except Exception as e:
            return []

    def download(self, response_body):
        print(response_body, file=open(
            f"output/smh_{self.ts}.html", "w", encoding="utf8"))

    def _extract_articles(self, js):
        outputs = []
        content_unit_groups = [ug for ug in js['page']['/']['index']
                               ['contentUnitGroups'] if ug['label'] in ["News well", "Everything else"]]
        self.download(self.response_body)
        for content_unit_group in content_unit_groups:
            cug_type = content_unit_group['label']
            units = content_unit_group['contentUnits']
            for content_unit in units:
                content_unit_id = content_unit['id']
                assets = content_unit.get("assets", [])
                for asset in assets:
                    if asset['assetType'] != 'article':
                        continue

                    about = asset.get('asset', {}).get('about')
                    headline = asset.get('asset', {}).get(
                        'headlines', {}).get('headline')
                    byline = asset.get('asset', {}).get('byline')
                    word_count = asset.get('asset', {}).get('wordCount')
                    cat = asset.get('category', {}).get('name')
                    id = asset['id']
                    first_published = asset.get(
                        'dates', {}).get('firstPublished')
                    modified = asset.get('dates', {}).get('modified')
                    published = asset.get('dates', {}).get('published')
                    output = Article(
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
                        snapshot=self.ts,
                        content_unit_id=content_unit_id
                    )

                    outputs.append(output)
        return outputs

    def _extract_json(self, body, ts):
        self.response_body = body
        self.ts = ts
        raw = re.search(
            "INITIAL_STATE = (.+?)</script", body)

        if raw is None:
            raw = re.search("INITIAL_STATE = (.+)", body)

        js = raw.group(1)

        if 'JSON.parse' in js:
            js = js.replace("JSON.parse(\"", "")[:-3]
        try:
            j = json.loads(re.sub("\\\\(.)", r"\1", js))
        except:
            try:
                j = json.loads(re.sub("\\\\(.)", r"\1", js.replace("\\\\","\\")))
            except Exception as e:
                except_json_parse(self, body, ts, e)
                return
        try:

            if type(j) == str:
                j = json.loads(j)
            self.js = j
            return j
        except Exception as e:
            except_json_parse(self, body, ts, e)



def run_parse():
    if len(sys.argv) == 1:
        print("Usage: python smh_parse.py file_name")
        sys.exit(0)
    file_name = sys.argv[1]
    ts = re.search("([0-9]{14})", file_name).group(1)
    body = open(file_name, "r", encoding="utf8").read()
    smh = SMHParse()
    response = MockResponse(body, ts)
    smh.parse(response)

class MockResponse():
    def __init__(self, html, ts):
        self.body = html
        self.meta = {'snapshot': [None, ts]}


if __name__ == "__main__":
    run_parse()