import re
from urllib.request import Request, urlopen
from html.parser import HTMLParser
import json

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._skip_depth=0
        self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag.lower() in {'script','style','noscript'}: self._skip_depth+=1
    def handle_endtag(self, tag):
        if tag.lower() in {'script','style','noscript'} and self._skip_depth: self._skip_depth-=1
    def handle_data(self, data):
        if not self._skip_depth:
            c=' '.join(data.split())
            if c: self.parts.append(c)
    def text(self): return '\n'.join(self.parts)

urls = [
    ("https://www.tiandiyou.com/youxigonglue/6041.html", "天地游"),
    ("https://www.bilibili.com/read/cv48145110", "B站专栏"),
]

for url, name in urls:
    print(f"\n=== {name} ===")
    try:
        r=Request(url, headers={'User-Agent':'Mozilla/5.0'})
        html=urlopen(r,timeout=15).read().decode('utf-8','replace')
        p=TextExtractor(); p.feed(html)
        text=p.text()
        codes = re.findall(r'\b[A-Z0-9]{8,20}\b', text)
        print(f"Text len: {len(text)}, codes found: {len(codes)}")
        for line in text.split('\n'):
            low = line.lower()
            if re.search(r'兑换|礼包|激活|redeem|code|gift|GENSHIN', low):
                print(f"  > {line.strip()[:200]}")
    except Exception as e:
        print(f"Error: {e}")
