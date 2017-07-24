
from Crypto.Cipher import AES

import re
import os
import json
import time
import hashlib
import random
import base64
import binascii
import requests

modulus = ('00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7'
           'b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280'
           '104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932'
           '575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b'
           '3ece0462db0a22b8e7')
nonce = '0CoJUm6Qyw8W8jud'
pubKey = '010001'

def createSecretKey(size):
    return binascii.hexlify(os.urandom(size))[:16]

def encrypted_request(text):
    text = json.dumps(text)
    secKey = createSecretKey(16)
    encText = aesEncrypt(aesEncrypt(text, nonce), secKey)
    encSecKey = rsaEncrypt(secKey, pubKey, modulus)
    data = {'params': encText, 'encSecKey': encSecKey}
    return data

def aesEncrypt(text, secKey):
    pad = 16 - len(text) % 16
    text = text + chr(pad) * pad
    encryptor = AES.new(secKey, 2, '0102030405060708')
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext).decode('utf-8')
    return ciphertext

def rsaEncrypt(text, pubKey, modulus):
    text = text[::-1]
    rs = pow(int(binascii.hexlify(text), 16), int(pubKey, 16), int(modulus, 16))
    return format(rs, 'x').zfill(256)

params = {
    'csrf_token': ''
}
headers = {
  'Accept': '*/*',
  'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
  'Connection': 'keep-alive',
  'Content-Type': 'application/x-www-form-urlencoded',
  'Referer': 'http://music.163.com',
  'Host': 'music.163.com',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'
}

def get_lyric(song_id, proxies = {}):
    host = 'http://music.163.com'
    headers = {
        'Referer': 'http://music.163.com',
        'Cookie': 'appver=1.5.2',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    action = '/api/song/lyric?os=osx&id=%s&lv=-1&kv=-1&tv=-1' % song_id
    url = host + action
    r = requests.get(url, headers = headers)
    return json.loads(r.text)

def get_mp3url(song_id, proxies = {}):
    host = 'http://music.163.com'
    action = '/weapi/song/enhance/player/url'
    url = host + action
    br = 999000
    text = {
        'ids': [song_id],
        'br': br,
        'csrf_token': ''
    }
    data = encrypted_request(text)
    r = requests.post(url, params = params, data=data, headers=headers, proxies=proxies)
    return json.loads(r.text)

def get_artist_albums(artist_id, limit = 30, offset = 0, proxies = {}):
    host = 'http://music.163.com'
    action = '/weapi/artist/albums/%s' % artist_id
    url = host + action
    text = {
        'offset': offset,
        'total': True,
        'limit': limit,
        "csrf_token": ""
    }
    data = encrypted_request(text)
    r = requests.post(url, params = params, data=data, headers=headers, proxies=proxies)
    return json.loads(r.text)

def get_album(album_id, proxies = {}):
    host = 'http://music.163.com'
    action = '/weapi/v1/album/%s' % album_id
    url = host + action
    text = {
        'csrf_token': ''
    }
    data = encrypted_request(text)
    r = requests.post(url, params = params, data=data, headers=headers, proxies=proxies)
    return json.loads(r.text)

if __name__ == '__main__':

    proxies = {'http': '110.73.31.223:8123'}

    print(get_lyric('185662'), proxies)

    print(get_mp3url('185662'), proxies)

    # get_artist_albums('6452')
    # get_album('2537184')
