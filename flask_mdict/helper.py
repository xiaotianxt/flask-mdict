import re
import uuid
import os.path
import sqlite3
import logging
from collections import OrderedDict

from . import Config
from .dbdict_query import DBDict
from .mdict_query2 import IndexBuilder2


logger = logging.getLogger(__name__)

regex_style = re.compile(r"<style.+?</style>", re.DOTALL | re.IGNORECASE)
regex_ln = re.compile(r"<(p|br|tr)[^>]*?>", re.IGNORECASE)
regex_tag = re.compile(r"<[^>]+?>")


def init_flask_mdict():
    db_name = Config.DB_NAMES.get("app_db")
    db = sqlite3.connect(db_name)
    c = db.cursor()
    # history
    sql = 'SELECT name FROM sqlite_master WHERE type="table" AND name="history";'
    row = c.execute(sql).fetchone()
    if not row:
        sql = "CREATE TABLE history(word TEXT PRIMARY KEY, count INT, last_time DATETIME);"
        db.execute(sql)
        db.commit()
    # mdict setting
    sql = 'SELECT name FROM sqlite_master WHERE type="table" AND name="setting";'
    row = c.execute(sql).fetchone()
    if not row:
        sql = "CREATE TABLE setting(name TEXT PRIMARY KEY, value TEXT);"
        db.execute(sql)
        db.commit()
    db.close()


dict_file_order = [
    "Etymology",
    "Merriam-Webster",
]


def custom_sort_key(name):
    for i, n in enumerate(dict_file_order):
        if n in name:
            return i
    return len(dict_file_order)


def init_mdict(mdict_dir, index_dir=None):
    mdicts = OrderedDict()
    db_names = {}
    mdict_setting = {}
    with sqlite3.connect(Config.DB_NAMES["app_db"]) as conn:
        rows = conn.execute("SELECT name, value FROM setting;")
        for row in rows:
            mdict_setting[row[0]] = row[1] == "1"
    for root, dirs, files in os.walk(mdict_dir, followlinks=True):
        files.sort(key=custom_sort_key)
        for fname in files:
            if (
                fname.endswith(".db")
                and not fname.endswith(".mdx.db")
                and not fname.endswith(".mdd.db")
            ):
                db_file = os.path.join(root, fname)
                d = DBDict(db_file)
                if not d.is_ok():
                    continue
                # mdict db
                dict_uuid = str(
                    uuid.uuid3(uuid.NAMESPACE_URL, db_file.replace("\\", "/"))
                ).upper()
                name = os.path.splitext(fname)[0]
                enable = mdict_setting.get(dict_uuid, True)
                logger.info(
                    'Initialize DICT DB "%s" {%s} [%s]...'
                    % (name, dict_uuid, "Enable" if enable else "Disable")
                )
                logger.info("\tfind %s:mdx" % fname)
                if d.is_mdd():
                    logger.info("\tfind %s:mdd" % fname)
                logo = "logo.ico"
                for ext in ["ico", ".jpg", ".png"]:
                    if os.path.exists(os.path.join(root, name + ext)):
                        logo = name + ext
                        break
                db_names[dict_uuid] = db_file
                mdicts[dict_uuid] = {
                    "title": d.title(),
                    "uuid": dict_uuid,
                    "logo": logo,
                    "about": d.about(),
                    "root_path": root,
                    "query": d,
                    "cache": {},
                    "type": "mdict_db",
                    "error": "",
                    "enable": enable,
                }
            elif fname.endswith(".mdx"):
                name = os.path.splitext(fname)[0]
                logo = "logo.ico"
                for ext in ["ico", ".jpg", ".png"]:
                    if os.path.exists(os.path.join(root, name + ext)):
                        logo = name + ext
                        break
                mdx_file = os.path.join(root, fname)
                dict_uuid = str(
                    uuid.uuid3(uuid.NAMESPACE_URL, mdx_file.replace("\\", "/"))
                ).upper()
                enable = mdict_setting.get(dict_uuid, True)
                logger.info(
                    'Initialize MDICT "%s" {%s} [%s]...'
                    % (name, dict_uuid, "Enable" if enable else "Disable")
                )

                if index_dir:
                    mdict_index_dir = os.path.join(index_dir, dict_uuid)
                    if not os.path.exists(mdict_index_dir):
                        os.makedirs(mdict_index_dir)
                else:
                    mdict_index_dir = None
                idx = IndexBuilder2(mdx_file, index_dir=mdict_index_dir)
                if not idx._title or idx._title == "Title (No HTML code allowed)":
                    title = name
                else:
                    title = idx._title
                    title = regex_tag.sub(" ", title)

                abouts = []
                abouts.append("<ul>")
                abouts.append("<li>%s</li>" % os.path.basename(idx._mdx_file))
                logger.info("\t+ %s" % os.path.basename(idx._mdx_file))
                for mdd in idx._mdd_files:
                    abouts.append("<li>%s</li>" % os.path.basename(mdd))
                    logger.info("\t+ %s" % os.path.basename(mdd))
                abouts.append("</ul><hr />")
                if (
                    idx._description
                    == "<font size=5 color=red>Paste the description of this product in HTML source code format here</font>"
                ):
                    text = ""
                else:
                    text = fix_html(idx._description)
                about_html = os.path.join(root, "about_%s.html" % name)
                if not os.path.exists(about_html):
                    with open(about_html, "wt", encoding="utf-8") as f:
                        f.write(text)
                if False:
                    text = regex_style.sub("", text)
                    text = regex_ln.sub("\n", text)
                    text = regex_tag.sub(" ", text)
                    text = [t for t in [t.strip() for t in text.split("\n")] if t]
                    abouts.append("<p>" + "<br />\n".join(text) + "</p>")
                else:
                    abouts.append(text)
                about = "\n".join(abouts)
                mdicts[dict_uuid] = {
                    "title": title,
                    "uuid": dict_uuid,
                    "logo": logo,
                    "about": about,
                    "root_path": root,
                    "query": idx,
                    "cache": {},
                    "type": "mdict",
                    "error": "",
                    "enable": enable,
                }

    logger.info("--- MDict is Ready ---")
    return mdicts, db_names


regex_css_comment = re.compile(r"(/\*.*?\*/)", re.DOTALL)
regex_css_tags = re.compile(r"([^}/;]+?){")


def fix_css(prefix_id, css_data):
    def replace(mo):
        tags = mo.group(1).strip()
        if not tags or tags.startswith("@"):
            return mo.group(0)
        else:
            fix_tags = []
            for tag in tags.split(","):
                tag = tag.strip()
                fix_tags.append(f"{prefix_id} .mdict {tag}")
            return "\n%s {" % ",".join(fix_tags)

    data = regex_css_comment.sub("", css_data)
    data = regex_css_tags.sub(replace, data)
    return data


regex_opened_tag = re.compile(r"<([a-z]+)(?: .*?)?>", re.DOTALL | re.IGNORECASE)
regex_closed_tag = re.compile(r"</([a-z]+)>", re.IGNORECASE)


def fix_html(html_data):
    opened_tags = regex_opened_tag.findall(html_data)
    closed_tags = regex_closed_tag.findall(html_data)
    opened_tags = [tag.lower() for tag in opened_tags]
    closed_tags = [tag.lower() for tag in closed_tags]
    # remove single tag
    for tag in ["img", "link", "input", "br", "hr", "p", "meta"]:
        while tag in opened_tags:
            opened_tags.remove(tag)
        while tag in closed_tags:
            closed_tags.remove(tag)
    if len(opened_tags) == len(closed_tags):
        return html_data
    for tag in opened_tags[::-1]:
        if tag in closed_tags:
            closed_tags.remove(tag)
        else:
            html_data += "</%s>" % tag
    for tag in closed_tags:
        html_data = "<%s>" % tag + html_data
    return html_data
