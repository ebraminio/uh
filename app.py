#!/usr/bin/env python3

import json
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from flask import Flask, request, Response

app = Flask(__name__)


@app.route('/uploadhelper-ir/tasnimgallery/<path:url>')
def tasnimgallery(url):
    try:
        url = 'http://www.tasnimnews.com/' + url
        page = urllib.request.urlopen(
            urllib.parse.quote(url, safe='~@#$&()*!+=:;,.?/\''))
        soup = BeautifulSoup(page.read(), 'html.parser')
        article = soup.select_one('body.photos article.media')
        images = map(lambda x: {
            'link': x['href'],
            'thumb': x.find('img')['src']
        }, article.select('.row a'))
        result = {
            'title': article.select_one('h1.title').text.strip(),
            'reporter': article.select_one('h4.reporter').text.strip(),
            'time': article.select_one('time').text.strip(),
            'lead': article.select_one('h3.lead').text.strip(),
            'result': list(images)
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
    response = Response('', content_type='application/json;charset=utf8')
    response.headers['Access-Control-Allow-Origin'] = "*"
    return response

if __name__ == '__main__':
    app.run()
