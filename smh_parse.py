import re
import json
import logging
from scrapy.item import Item, Field


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
        js = self._extract_json(
            str(response.body), response.meta['snapshot'][1])
        return self._extract_articles(js)

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
            "INITIAL_STATE = (.+?)</", body)

        if raw is None:
            raw = re.search("INITIAL_STATE = (.+)", body)

        js = raw.group(1)
        if 'JSON.parse' in js:
            js = js.replace("JSON.parse(\"", "")[:-3]
        try:
            j = json.loads(re.sub("\\\\(.)", r"\1", js))
            if type(j) == str:
                j = json.loads(j)
            self.js = j
            return j
        except Exception as e:
            self.logger.exception(e)
            output = {"snapshot": ts, "error": e}
            self.js = output
            return output
