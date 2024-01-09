import io
import re
import os.path
import urllib.parse

from flask import (
    send_file,
    url_for,
    redirect,
    abort,
    jsonify,
    request,
    make_response,
)

from . import mdict, get_mdict, get_db, Config
from . import helper


regex_word_link = re.compile(r"^(@@@LINK=)(.+)$")
# img src
regex_src_schema = re.compile(r'([ "]src=["\'])(/|file:///)?(?!data:)(.+?["\'])')
# http://.../
regex_href_end_slash = re.compile(r'([ "]href=["\'].+?)(/)(["\'])')
# sound://
regex_href_schema_sound = re.compile(r'([ "]href=["\'])(sound://)([^#].+?["\'])')
# entry://
regex_href_schema_entry = re.compile(r'([ "]href=["\'])(entry://)([^#].+?["\'])')
# /xxx/xxx.css
regex_href_no_schema = re.compile(
    r'([ "]href=["\'])(?!http://|https://|sound://|entry://)([^#].+?["\'])'
)

# css
regex_css = re.compile(r'(<link.*? )(href)(=".+?>)')
# js
regex_js = re.compile(r'(<script.*? )(src)(=".+?>)')


@mdict.route("/")
def index():
    return jsonify(
        [
            {
                "title": "Search Suggestions",
                "description": "Search for word suggestions",
                "href": url_for(".query_part", part="", _external=True),
                "examples": [
                    {
                        "request": url_for(".query_part", part="appl", _external=True),
                        "response": """{
"suggestion": [
"Applied",
"applaud",
"applause",
"apple",
"apple pie",
"apple sauce",
"apple seed",
"apple tree",
"apple-pie",
"apple-sauce",
"apple-seed",
"apple-tree",
"applejack",
"applet",
"appliance",
"applicability",
"applicable",
"applicant",
"application",
"applicator",
"applied",
"applique",
"apply"
]
}""",
                    }
                ],
            },
            {
                "title": "Search Word",
                "description": "Search for word definition",
                "href": url_for(".query_word_lite", word="", _external=True),
                "examples": [
                    {
                        "request": url_for(
                            ".query_word_lite", word="apple", _external=True
                        ),
                        "response": """<div id="class_FA96C0A7-B3C9-33CF-89DB-6FD82264DD07">
    <div class="mdict">
        <link rel="stylesheet" href="http://127.0.0.1:5000/uuid_FA96C0A7-B3C9-33CF-89DB-6FD82264DD07/resource/css/reset.css">
        <link rel="stylesheet" href="http://127.0.0.1:5000/uuid_FA96C0A7-B3C9-33CF-89DB-6FD82264DD07/resource/css/mdict.css">
        <div class="mdict-title">
            <img style="height:16px !important;
                    border-radius:.25rem !important;
                    vertical-align:baseline !important" src="http://127.0.0.1:5000/uuid_FA96C0A7-B3C9-33CF-89DB-6FD82264DD07/resource/logo.ico"/>Online Etymology DictionaryNew

        </div>
        <li>
            <link rel="stylesheet" href="http://127.0.0.1:5000/uuid_FA96C0A7-B3C9-33CF-89DB-6FD82264DD07/resource/Online Etymology DictionaryNew.css">
            <div class="word--C9UPa">
                <div>
                    <h1 class="word__name--TTbAA" title="Origin and meaning of apple">apple (n.)</h1>
                    <section class="word__defination--2q7ZH">
                        <object>
                            Old English <span class="foreign">æppel</span>
                            &quot;apple; any kind of fruit; fruit in general,&quot;from Proto-Germanic <span class="foreign">*ap(a)laz</span>
                            (source also of Old Saxon, Old Frisian, Dutch <span class="foreign">appel</span>
                            , Old Norse <span class="foreign">eple</span>
                            , Old High German <span class="foreign">apful</span>
                            , German <span class="foreign">Apfel</span>
                            ), from PIE <span class="foreign">*ab(e)l-</span>
                            &quot;apple &quot;(source also of Gaulish <span class="foreign">avallo</span>
                            &quot;fruit;&quot;Old Irish <span class="foreign">ubull</span>
                            , Lithuanian <span class="foreign">obuolys</span>
                            , Old Church Slavonic <span class="foreign">jabloko</span>
                            &quot;apple &quot;), but the exact relation and original sense of these is uncertain (compare <span class="crossreference">melon</span>
                            ).
<blockquote>A roted eppel amang þe holen, makeþ rotie þe yzounde. [&quot;Ayenbite of Inwit,&quot;1340]
</blockquote>
                            In Middle English and as late as 17c., it was a generic term for all fruit other than berries but including nuts (such as Old English <span class="foreign">fingeræppla</span>
                            &quot;dates,&quot;literally &quot;finger-apples;&quot;Middle English <span class="foreign">appel of paradis</span>
                            &quot;banana,&quot;c. 1400). Hence its grafting onto the unnamed &quot;fruit of the forbidden tree &quot;in Genesis. Cucumbers, in one Old English work, are <span class="foreign">eorþæppla</span>
                            , literally &quot;earth-apples &quot;(compare French <span class="foreign">pomme de terre</span>
                            &quot;potato,&quot;literally &quot;earth-apple;&quot;see also <span class="crossreference">melon</span>
                            ). French <span class="foreign">pomme</span>
                            is from Latin <span class="foreign">pomum</span>
                            &quot;apple; fruit &quot;(see <span class="crossreference">Pomona</span>
                            ).
<blockquote>As far as the forbidden fruit is concerned, again, the Quran does not mention it explicitly, but according to traditional commentaries it was not an apple, as believed by Christians and Jews, but wheat. [&quot;The Heart of Islam: Enduring Values for Humanity,&quot;Seyyed Hossein Nasr, 2002]
</blockquote>
                            <span class="foreign">Apple of Discord</span>
                            (c. 1400) was thrown into the wedding of Thetis and Peleus by Eris (goddess of chaos and discord), who had not been invited, and inscribed <span class="foreign">kallisti</span>
                            &quot;To the Prettiest One.&quot;Paris, elected to choose which goddess should have it, gave it to Aphrodite, offending Hera and Athene, with consequences of the Trojan War, etc.
<br>
                            <br>
                            <span class="foreign">Apple of one‘s eye</span>
                            (Old English), symbol of what is most cherished, was the pupil, supposed to be a globular solid body. <span class="foreign">Apple-polisher</span>
                            &quot;one who curries favor &quot;first attested 1928 in student slang. The image in the phrase <span class="foreign">upset the apple cart</span>
                            &quot;spoil the undertaking &quot;is attested from 1788. <span class="foreign">Road-apple</span>
                            &quot;horse dropping &quot;is from 1942.
                        </object>
                    </section>
                </div>
            </div>
            <div class="related--32LCi">
                <h1 class="related__title--2BB_n" title="words related to apple">Related Words</h1>
                <ul class="related__container--22iKI">
                    <a title="Origin and meaning of applejack" data-entry-url="https://127.0.0.1:5000/query/applejack?uuid=FA96C0A7-B3C9-33CF-89DB-6FD82264DD07" href="entry://applejack">
                        <li class="related__word--3Si0N">applejack</li>
                    </a>
                    <a title="Origin and meaning of apple-pie" data-entry-url="https://127.0.0.1:5000/query/apple-pie?uuid=FA96C0A7-B3C9-33CF-89DB-6FD82264DD07" href="entry://apple-pie">
                        <li class="related__word--3Si0N">apple-pie</li>
                    </a>
                    <a title="Origin and meaning of apple-sauce" data-entry-url="https://127.0.0.1:5000/query/apple-sauce?uuid=FA96C0A7-B3C9-33CF-89DB-6FD82264DD07" href="entry://apple-sauce">
                        <li class="related__word--3Si0N">apple-sauce</li>
                    </a>
                    <a title="Origin and meaning of apple-seed" data-entry-url="https://127.0.0.1:5000/query/apple-seed?uuid=FA96C0A7-B3C9-33CF-89DB-6FD82264DD07" href="entry://apple-seed">
                        <li class="related__word--3Si0N">apple-seed</li>
                    </a>
                    <a title="Origin and meaning of apple-tree" data-entry-url="https://127.0.0.1:5000/query/apple-tree?uuid=FA96C0A7-B3C9-33CF-89DB-6FD82264DD07" href="entry://apple-tree">
                        <li class="related__word--3Si0N">apple-tree</li>
                    </a>
                    <a title="Origin and meaning of berry" data-entry-url="https://127.0.0.1:5000/query/berry?uuid=FA96C0A7-B3C9-33CF-89DB-6FD82264DD07" href="entry://berry">
                        <li class="related__word--3Si0N">berry</li>
                    </a>
                    <a title="Origin and meaning of melon" data-entry-url="https://127.0.0.1:5000/query/melon?uuid=FA96C0A7-B3C9-33CF-89DB-6FD82264DD07" href="entry://melon">
                        <li class="related__word--3Si0N">melon</li>
                    </a>
                    <a title="Origin and meaning of pineapple" data-entry-url="https://127.0.0.1:5000/query/pineapple?uuid=FA96C0A7-B3C9-33CF-89DB-6FD82264DD07" href="entry://pineapple">
                        <l i class="related__word--3Si0N">pineapple
        </li>
</a>
<a title="Origin and meaning of Pomona" data-entry-url="https://127.0.0.1:5000/query/Pomona?uuid=FA96C0A7-B3C9-33CF-89DB-6FD82264DD07" href="entry://Pomona">
    <li class="related__word--3Si0N">Pomona</li>
</a>
</ul></div></div></div><script src="http://127.0.0.1:5000/static/js/mdict.js"></script>
""",
                    },
                ],
            },
        ]
    )


@mdict.route("/search")
def query_part():
    part = request.args.get("part", default="", type=str)
    contents = set()
    for uuid, item in get_mdict().items():
        if item["type"] == "app":
            continue
        if item["enable"]:
            content = item["query"].get_mdx_keys(get_db(uuid), part)
            contents |= set(content)
    return jsonify(suggestion=sorted(contents))


@mdict.route("/uuid_<uuid>/resource/<path:resource>", methods=["GET", "POST"])
def query_resource(uuid, resource):
    """query mdict resource file: mdd"""
    resource = resource.strip()
    item = get_mdict().get(uuid)
    if not item:
        abort(404)

    # file, load from cache, local, static, mdd
    fname = os.path.join(item["root_path"], resource)
    # check cache
    if resource in item:
        data = item["cache"][resource]
    elif os.path.exists(fname):
        # mdict local disk
        data = open(fname, "rb").read()
    else:
        # mdict mdd
        q = item["query"]
        if item["type"] == "app":
            with mdict.open_resource(os.path.join("static", resource)) as f:
                data = f.read()
        else:
            key = "\\%s" % "\\".join(resource.split("/"))
            data = q.mdd_lookup(get_db(uuid), key, ignorecase=True)
    if not data:
        # load from flask static
        if resource in ["logo.ico", "css/reset.css", "css/mdict.css"]:
            with mdict.open_resource(os.path.join("static", resource)) as f:
                data = f.read()

    if data:
        ext = resource.rpartition(".")[-1]
        if resource not in item and ext in ["css", "js", "png", "jpg", "woff2"]:
            if resource.endswith(".css"):
                try:
                    s_data = data.decode("utf-8")
                    s_data = helper.fix_css("#class_%s" % uuid, s_data)
                    data = s_data.encode("utf-8")
                    item["error"] = ""
                except Exception as err:
                    err_msg = "Error: %s - %s" % (resource, err.format_original_error())
                    print(err_msg)
                    item["error"] = err_msg
                    abort(404)
            if Config.MDICT_CACHE:
                item["cache"][resource] = data  # cache css file

        bio = io.BytesIO()
        bio.write(data)
        bio.seek(0)

        resp = make_response(send_file(bio, download_name=resource))
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    else:
        abort(404)


@mdict.route("/query")
def query_word_lite():
    word = request.args.get("word", default="", type=str)
    uuid = "all"

    def url_replace(mo):
        abs_url = mo.group(2)
        abs_url = urllib.parse.unquote(abs_url)
        if abs_url.startswith("sound://"):
            sound_url = url_for(
                ".query_resource",
                uuid=uuid,
                resource=abs_url[8:],
                _external=True,
                _scheme=scheme,
            )
            return (
                f' data-sound-url="{sound_url}"' + mo.group(1) + abs_url + mo.group(3)
            )
        elif abs_url.startswith("entry://"):
            entry_url = url_for(
                ".query_word_lite",
                uuid=uuid,
                word=abs_url[8:],
                _external=True,
                _scheme=scheme,
            )
            return (
                f' data-entry-url="{entry_url}"' + mo.group(1) + abs_url + mo.group(3)
            )
        elif abs_url.startswith("/static/"):
            abs_url2 = url_for(
                "static", filename=abs_url[8:], _external=True, _scheme=scheme
            )
        else:
            abs_url2 = re.sub(r"(?<!:)//", "/", abs_url)
        return mo.group(1) + abs_url2 + mo.group(3)

    scheme = "https"
    all_result = request.args.get("all_result", "") == "true"
    fallback = request.args.get("fallback", "").split(",")
    nohistory = request.args.get("nohistory", "") == "true"
    if not word:
        return abort(404)
    word = word.strip()

    html_contents = []
    found_word = False
    items = [item for _, item in get_mdict().items()]
    for item in items:
        # entry and word, load from mdx, db
        cur_uuid = item["uuid"]
        q = item["query"]
        if item["type"] == "app":
            records = q(word, item)
        else:
            records = q.mdx_lookup(get_db(cur_uuid), word, ignorecase=True)
        if not records:
            continue
        html = []
        html.append(f'<div id="class_{cur_uuid}">')
        html.append('<div class="mdict">')
        # add mdict_uuid by query_resource
        html.append(
            f"""<link rel="stylesheet"
                    href="{url_for(".query_resource", uuid=uuid, resource="css/reset.css", _external=True)}">"""
        )
        html.append(
            f"""<link rel="stylesheet"
                    href="{url_for(".query_resource", uuid=uuid, resource="css/mdict.css", _external=True)}">"""
        )
        if item["error"]:
            html.append('<div style="color: red;">%s</div>' % item["error"])
        html.append('<div class="mdict-title">')
        html.append(
            f"""<img
                    style="height:16px !important;
                    border-radius:.25rem !important;
                    vertical-align:baseline !important"
                    src="{url_for(".query_resource", uuid=cur_uuid, resource=item["logo"], _external=True)}"/>"""
        )
        html.append(item["title"])
        html.append("</div>")
        prefix_resource = (
            f'{url_for(".query_resource", uuid=cur_uuid, resource="", _external=True)}'
        )
        # prefix_entry = f'{url_for(".query_word_lite", uuid=cur_uuid, word="", _external=True)}'
        found_word = found_word or (cur_uuid != "gtranslate" and len(records) > 0)
        count = 1
        record_num = len(records)
        for record in records:
            if record.startswith("@@@LINK="):
                record_num -= 1
        for record in records:
            record = helper.fix_html(record)
            mo = regex_word_link.match(record)
            if mo:
                link = mo.group(2).strip()
                if "#" in link:
                    # anchor in current page
                    link, anchor = link.split("#")
                    return redirect(
                        url_for(
                            ".query_word_lite",
                            uuid=cur_uuid,
                            word=link,
                            fallback=",".join(fallback),
                            nohistory="true" if nohistory else "false",
                            _anchor=anchor,
                            _external=True,
                        )
                    )
                else:
                    if len(records) > 1 or len(items) > 1:
                        record = f"""<p>See also: <a data-entry-url="{url_for(".query_word_lite", uuid=cur_uuid, word=link, _external=True, _scheme=scheme)}" href="entry://{link}">{link}</a></p>"""
                    else:
                        return redirect(
                            url_for(
                                ".query_word_lite",
                                uuid=cur_uuid,
                                word=link,
                                fallback=",".join(fallback),
                                nohistory="true" if nohistory else "false",
                                _external=True,
                                _scheme=scheme,
                            )
                        )
            else:
                # remove http:// from sound:// and entry://
                record = regex_href_end_slash.sub(r"\1\3", record)
                # <img src="<add:resource/>...
                record = regex_src_schema.sub(r"\g<1>%s/\3" % prefix_resource, record)
                # <a href="sound://<add:resource/>...
                # record = regex_href_schema_sound.sub(r'\1\g<2>%s/\3' % prefix_resource[7:], record)
                # <a href="<add:resource/>image.png
                record = regex_href_no_schema.sub(
                    r"\g<1>%s/\2" % prefix_resource, record
                )
                # entry://
                # record = regex_href_schema_entry.sub(r'\1\g<2>%s\3' % prefix_entry[7:], record)

                # keep first css
                if count > 1:
                    record = regex_css.sub(r"\1data-\2\3", record)
                # keep last js
                if count < record_num:
                    record = regex_js.sub(r"\1data-\2\3", record)
                count += 1

            html.append(record)
        html.append("</div></div>")
        # 有两种事件处理方式：
        # chrome extension event handler 在第三方页面，使用插件里发声
        # 在独立页面，使用js发声
        html.append(
            f'<script src="{url_for(".static", filename="js/mdict.js", _external=True)}"></script>'
        )
        html = "\n".join(html)
        # fix url with "//"
        # css, image
        html = re.sub(r'( href=")(.+?)(")', url_replace, html)
        # script
        html = re.sub(r'( src=")(?!data:)(.+?)(")', url_replace, html)
        html_contents.append(html)
        if uuid != "all" and not all_result:
            break
    resp = make_response('<hr class="seprator" />'.join(html_contents))
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp
