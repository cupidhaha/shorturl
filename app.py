#encoding=utf8
import flask
import redis
from base36 import base36encode, base36decode
from flask import Flask, request

# redis map: ShortUrl.Urls table: number:url
# redis map: ShortUrl.Alias table: number:alias
# redis map: ShortUrl.Url-Number table: url:number

REDIS_COUNT = 'ShortUrl.Count'
REDIS_NUMBER2URL = 'ShortUrl.Num2Urls'
REDIS_URL2NUMBER = 'ShortUrl.Url2Nums'

app = Flask(__name__)
r = redis.StrictRedis(host='localhost', port=6379, db=0)
if r.get(REDIS_COUNT) is None:
    r.set(REDIS_COUNT,0)

r.hset(REDIS_NUMBER2URL, str(base36decode('a')), "http://www.qq.com")
r.hset(REDIS_NUMBER2URL, str(base36decode('b')), "http://www.sina.com")

r.hset(REDIS_URL2NUMBER, "http://www.qq.com", str(base36decode('a')))
r.hset(REDIS_URL2NUMBER, "http://www.sina.com", str(base36decode('b')))

table = {
"a":"http://www.qq.com",
"b":"http://www.sina.com"
}

def redis_get_url_by_key(key):
    if len(key) > 0 and r.hexists(REDIS_NUMBER2URL, base36decode(key)):
        return r.hget(REDIS_NUMBER2URL, base36decode(key))
    return None

def redis_get_alias_by_url(url):
    if r.hexists(REDIS_URL2NUMBER, url):
        number = int(r.hget(REDIS_URL2NUMBER, url))
        if number <= int(r.get(REDIS_COUNT)):
            return base36encode(number)
    return None

def redis_get_unused_number():
    while r.hexists(REDIS_NUMBER2URL, r.get(REDIS_COUNT)):
        r.incr(REDIS_COUNT)
    return r.get(REDIS_COUNT)

def redis_set_number_url(number, url):
    r.hset(REDIS_NUMBER2URL, str(number), url)
    old_number = r.hget(REDIS_URL2NUMBER, url) 
    if old_number is not None and int(old_number) < number:
        return 

    r.hset(REDIS_URL2NUMBER, url, str(number))
    return

@app.route("/<key>")
def short_url(key):
    url = redis_get_url_by_key(key)
    if url is None:
        return "No redirect!"
    return flask.redirect(url)

@app.route("/create")
def hello():
    url = request.args.get("url", "")
    alias = request.args.get("alias", "")
    origin_url = redis_get_url_by_key(alias)
    if origin_url == url:
        return "%s is created!" % alias;
    if origin_url is None and len(alias) > 0:
        redis_set_number_url(base36decode(alias), url)
        return "%s is created!" % alias;
    alias = redis_get_alias_by_url(url)
    if alias is not None:
        return "%s is created!" % alias;

    count = int(redis_get_unused_number())
    alias = base36encode(count)
    redis_set_number_url(count, url)
    return "%s is created!" % alias;

@app.route("/")
def index():
    return """ 
<form action="create" method="get" name="f">
<table align="center" cellpadding="5" class="create-form"><tr><td>
<b>Enter a long URL to make tiny:</b><br />
<input type="hidden" name="source" value="indexpage">
<input type="text" name="url" size="30"><input type="submit" name="submit" value="Make TinyURL!">
<hr>
	Custom alias (optional):<br />
	<tt>http://刘媛.cn/</tt><input type="text" name="alias" value="" size="12" maxlength="30"><br />
	<small>May contain letters, numbers, and dashes.</small>
	</td></tr></table>
</form>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
