#!/usr/bin/env python3

import json
import urllib.parse
import re
import calverter
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, Response
from PIL import Image
import base64
import io


app = Flask(__name__)


@app.route('/uploadhelper-ir/tasnimgallery/<path:url>')
def tasnimgallery(url):
    try:
        if re.match(r'^http://(www\.)?tasnimnews\.com/', url) is None:
            raise Exception('Not supported link')

        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        article = soup.select_one('body.photos article.media')
        images = map(lambda x: {
            'link': x['href'],
            'thumb': x.find('img')['src']
        }, article.select('.row a'))
        result = {
            'title': article.select_one('h1.title').text.strip(),
            'reporter': article.select_one('h4.reporter').text.strip(),
            'time': parsedate(article.select_one('time').text.strip()),
            'lead': article.select_one('h3.lead').text.strip(),
            'images': list(images),
            'url': url
        }
    except Exception as e:
        result = {"error": str(e)}

    response = Response(
        json.dumps(result, indent=1, ensure_ascii=False),
        content_type='application/json;charset=utf8')

    # TODO: This should be limited
    response.headers['Access-Control-Allow-Origin'] = "*"

    return response


@app.route('/uploadhelper-ir/tasnimcrop/<path:url>')
def tasnimcrop(url):
    format = request.args.get('format')
    if re.match(r'^http://newsmedia\.tasnimnews\.com/', url) is None:
        raise Exception('Not supported link')

    img = Image.open(io.BytesIO(requests.get(url).content))
    img2 = img.crop(
        (0, 0, img.size[0], img.size[1] - int(img.size[0] / 800 * 24)))
    img_io = io.BytesIO()
    img2.save(img_io, 'JPEG')
    img_io.seek(0)
    if format == 'base64':
        b64 = base64.b64encode(img_io)
        response = Response(b64, content_type='text/plain')
    else:
        response = Response(img_io, content_type='image/jpeg')

    response.headers['Access-Control-Allow-Origin'] = "*"
    return response

if __name__ == '__main__':
    app.run()

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
    date = re.sub(r'[۰-۹]', lambda x: chr(ord(x.group(0)) - distance), date)
    m = re.match(r'(\d\d?) ([^ ]*) (\d{4}) - (\d\d?):(\d\d?)', date)
    jd = cal.jalali_to_jd(int(m.group(3)), months[m.group(2)], int(m.group(1)))
    greg = cal.jd_to_gregorian(jd)
    return '%d-%d-%d' % greg + ' %s:%s' % (m.group(4), m.group(5))
