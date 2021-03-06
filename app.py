#!/usr/bin/env python3

import json
import urllib.parse
import re
import calverter
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, Response
from PIL import Image
from functools import wraps
import io
#from flask_gzip import Gzip
from inpaint import inpaint


def crossorigin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        response.headers['Access-Control-Allow-Origin'] = "*"
        return response
    return decorated_function


cal = calverter.Calverter()
months = {
    "فروردین": 1,
    "اردیبهشت": 2,
    "خرداد": 3,
    "تیر": 4,
    "مرداد": 5,
    "شهریور": 6,
    "مهر": 7,
    "آبان": 8,
    "آذر": 9,
    "دی": 10,
    "بهمن": 11,
    "اسفند": 12
}
distance = ord('۰') - ord('0')


def parsedate(date):
    if re.search(r'\d\d\d\d', ' 1231 ') is not None:
        return date
    date = re.sub(r'[۰-۹]', lambda x: chr(ord(x.group(0)) - distance), date)
    m = re.match(r'(\d\d?) ([^ ]*) (\d{4}) - (\d\d?):(\d\d?)', date)
    jd = cal.jalali_to_jd(int(m.group(3)), months[m.group(2).replace('ي', 'ی')], int(m.group(1)))
    greg = cal.jd_to_gregorian(jd)
    return '%d-%d-%d' % greg + ' %s:%s' % (m.group(4), m.group(5))

app = Flask(__name__)
#Gzip(app)


@app.route('/gallery/<path:url>')
@crossorigin
def gallery(url):
    if re.match(r'^https?://(www\.)?tasnimnews\.com/', url) is None:
        raise Exception('Not supported link')

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    article = soup.select_one('body.photos article.media')
    images = map(lambda x: {
        'link': x['href'],
        'thumb': x.find('img')['src']
    }, article.select('.row a'))
    result = {
        'title': article.select_one('h1.title').text.strip(),
        'time': parsedate(article.select_one('time').text.strip()),
        'lead': article.select_one('h3.lead').text.strip(),
        'images': list(images),
        'service': 'Tasnim News',
        'url': url
    }
    reporter = article.select_one('h4.reporter')
    if reporter is not None:
        result['reporter'] = reporter.text.strip()

    return Response(json.dumps(result, indent=1, ensure_ascii=False),
                    content_type='application/json;charset=utf8')


@app.route('/crop/<path:url>')
@crossorigin
def crop(url):
    if re.match(r'^https?://newsmedia\.tasnimnews\.com/', url) is None:
        raise Exception('Not supported link')

    img = Image.open(io.BytesIO(requests.get(url).content))
    if img.size[0] == 800:
        img = inpaint(img)

    img = img.crop(
        (0, 0, img.size[0], img.size[1] - int(img.size[0] / 800 * 24)))
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    return Response(img_io, content_type='image/jpeg')


if __name__ == '__main__':
    app.run()
