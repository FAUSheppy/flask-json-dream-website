#!/usr/bin/python3
import json
import os
import flask
import argparse

import caldav
import datetime as dt
import markdown2

# sitemap utilities
from werkzeug.routing import BuildError
import xml.etree.ElementTree as et

# paths
SECTIONS_DIR   = "sections/"
NEWS_DIR       = "news/"
PICTURES_DIR   = "pictures/"
MAIN_LINKS_DIR = "mainLinks/"

# json config keys
TIMEOUT_RELATIVE = "timeout-relative-weeks"
TIMEOUT_FIXED    = "timeout-fixed"
PARSED_TIME      = "parsed-time"
ACTIVE           = "active"
DATE             = "date"
UID              = "uid"

MARKDOWN_FILE_KEY    = "markdown-file"
MARKDOWN_CONTENT_KEY = "markdown-content"

# sitemap
PRIORITY_PRIMARY   = 1.0
PRIORITY_SECONDARY = 0.8

# other
HTTP_NOT_FOUND = 404
EMPTY_STRING   = ""
CACHE_FILE     = "cache.json"
READ           = "r"
WRITE          = "w"

app = flask.Flask("FLASK_JSON_DREAM_WEBSITE", static_folder=None)
app.config.from_object("config")

def updateEventsFromCalDav():
    '''Load event from a remote calendar'''

    if app.config["SHOW_CALENDAR"]:
        client = caldav.DAVClient(url=caldavUrl, username=caldavUsername, password=caldavPassword)
        authenticatedClient = client.principal()
        defaultCal = authenticatedClient.calendars()[0]

        start = dt.datetime.now()
        start -= dt.timedelta(seconds=start.timestamp() % dt.timedelta(days=1).total_seconds())
        end   = start + dt.timedelta(days=app.config["NEWS_MAX_AGE"])

        events = sorted(defaultCal.date_search(start, end), 
                            key=lambda e: e.vobject_instance.vevent.dtstart.value)

        eventsDictList = []
        for e in events:
            date = e.vobject_instance.vevent.dtstart.value
            date += dt.timedelta(hours=2)
            newEventDict = { "description" : e.vobject_instance.vevent.summary.value,
                             "time"        : date.strftime("%H:%M"),
                             "day"         : date.strftime("%d"),
                             "month"       : date.strftime("%b"),
                             "year"        : date.strftime("%Y")}
            try:
                newEventDict.update({ "location" : e.vobject_instance.vevent.location.value })
            except AttributeError:
                pass
            eventsDictList += [newEventDict]
    else:
        eventsDictList = []
    
    # dump to cache file #
    with open(CACHE_FILE, WRITE) as f:
        json.dump(eventsDictList, f)


def getEventsCache():
    '''Return the cached events'''

    with open(CACHE_FILE, READ) as f:
        return json.load(f)

def readJsonDir(basedir):
    '''Read a directory containing json information'''

    jsonDictList =[]
    for root, dirs, files in os.walk(basedir):
        for filename in sorted(files):
            if filename.endswith(".json"):
                with open(os.path.join(basedir, filename)) as f:
                    jsonDictList += [json.load(f)]

    return jsonDictList

def parseNewsDirWithTimeout():
    '''Parse a directory containing news-json structs and filter out
        entries that have exceeded the max age'''

    news = readJsonDir(app.config["NEWS_DIR"])
    now = dt.datetime.now()
    for n in news:
        n.update( { PARSED_TIME : dt.datetime.fromtimestamp(n[DATE]) } )
        if n.get(ACTIVE):
            continue
        if n.get(TIMEOUT_FIXED):
            if dt.datetime.fromtimestamp(n[TIMEOUT_FIXED]) < now:
                n[ACTIVE] = False
        elif n.get(TIMEOUT_RELATIVE):
            if n[PARSED_TIME] + dt.timedelta(weeks=n[TIMEOUT_RELATIVE]) < now:
                n[ACTIVE] = False
        else:
            raise ValueError("No timeout for news {} specified!", n)

    return sorted(news, key=lambda n: n[PARSED_TIME], reverse=True)

@app.route("/invalidate")
def invalidateEventCache():
    '''Reload the calendar events'''

    updateEventsFromCalDav();
    return (EMPTY_STRING, 204)

@app.route("/")
def root():
    return flask.render_template("index.html", conf=app.config,
                                            mainLinks=readJsonDir(app.config["MAIN_LINKS_DIR"]),
                                            events=getEventsCache(),
                                            moreEvents=len(getEventsCache())>3,
                                            sections=readJsonDir(app.config["SECTIONS_DIR"]),
                                            announcements=parseNewsDirWithTimeout())

@app.route("/impressum")
def impressum():
    return flask.render_template("impressum.html", conf=app.config)

@app.route("/people")
def people():
    return flask.render_template("people.html", conf=app.config,
                                                people=readJsonDir("people/"))

@app.route("/news")
def news():
    '''Display news-articles based on a UID-parameter'''

    requestedId = flask.request.args.get(UID)

    # load news and map UIDs #
    news = parseNewsDirWithTimeout()
    newsDict = dict()
    for n in news:
        newsDict.update( { n[UID] : n } )

    # set newest article config if there is not UID     #
    # return 404 if the UID doesnt exist                #
    # set article config of matching article otherwiese #
    if not requestedId:
        article = sorted(news, key=lambda n: n[PARSED_TIME])[-1]
    elif not newsDict[int(requestedId)]:
        return (EMPTY_STRING, HTTP_NOT_FOUND)
    else:
        article = newsDict[int(requestedId)]

    # load article based on config #
    try:
        with open(article[MARKDOWN_FILE_KEY]) as f:
            article.update( { MARKDOWN_CONTENT_KEY : markdown2.markdown(f.read()) } )
    except FileNotFoundError as e:
        return ("File not found Error ({})".format(e), HTTP_NOT_FOUND)

    return flask.render_template("news.html", conf=app.config, article=article)

@app.route("/static/<path:path>")
def sendStatic(path):
    cache_timeout = None
    return flask.send_from_directory('static', path, cache_timeout=cache_timeout)

@app.route("/picture/<path:path>")
def sendPicture(path):
    cache_timeout = 2592000
    return flask.send_from_directory(PICTURES_DIR, path, cache_timeout=cache_timeout)

@app.route('/defaultFavicon.ico')
def icon():
    return flask.send_from_directory('static', 'defaultFavicon.ico')

@app.route("/sitemap.xml")
def siteMap():
    '''Return an XML-sitemap for SEO'''

    # search for urls to add to sitemap #
    urls = []

    # iterate through all endpoints #
    for rule in app.url_map.iter_rules():

        # skip all endpoints #
        if any([s in rule.endpoint for s in app.config["SITEMAP_IGNORE"]]):
            continue
        
        # skip all non-GET endpoints #
        if not "GET" in rule.methods:
            continue

        # get url for endpoint, get start time and set priority #
        try:
            url = flask.url_for(rule.endpoint, **(rule.defaults or {}))
            priority = PRIORITY_SECONDARY
            if rule.endpoint == "root":
                priority = PRIORITY_PRIMARY
            urls += [(url, app.config["START_TIME"], priority)]
        except BuildError:
            pass

    # add news articles to sitemap #
    news = parseNewsDirWithTimeout()
    for n in filter(lambda x: x["active"], news):
        urls += [("/news?uid={}".format(n[UID]), n[PARSED_TIME], PRIORITY_SECONDARY)]

    hostname = flask.request.headers.get("X-REAL-HOSTNAME")
    if not hostname:
        hostname = "localhost"

    top = et.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url, lastmod, priority in urls:
        child = et.SubElement(top, 'url')

        chilLoc      = et.SubElement(child, 'loc')
        childLastmod = et.SubElement(child, 'lastmod')
        childPrio    = et.SubElement(child, 'priority')

        childPrio.text    = str(priority)
        childLastmod.text = lastmod.strftime("%Y-%m-%d")
        chilLoc.text      = "https://" + hostname + url

    xmlDump = "<?xml version='1.0' encoding='UTF-8'?>"
    xmlDump += et.tostring(top, encoding='UTF-8', method='xml').decode()
    return flask.Response(xmlDump, mimetype='application/xml')

@app.before_first_request
def init():
    app.config["SECTIONS_DIR"]   = os.path.join(app.config["CONTENT_DIR"], SECTIONS_DIR)
    app.config["NEWS_DIR"]       = os.path.join(app.config["CONTENT_DIR"], NEWS_DIR)
    app.config["MAIN_LINKS_DIR"] = os.path.join(app.config["CONTENT_DIR"], MAIN_LINKS_DIR)

    if app.config["RELOAD_CALENDAR_ON_START"]:
        updateEventsFromCalDav()
    
    app.config["START_TIME"] = dt.datetime.now()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Projects Showcase',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # general parameters #
    parser.add_argument("-i", "--interface", default="127.0.0.1", help="Interface to listen on")
    parser.add_argument("-p", "--port",      default="5000",      help="Port to listen on")
    parser.add_argument("--auto-reload", action="store_const", default=False, const=True,
                                help="Automaticly reload HTTP templates (impacts performance)")
    parser.add_argument("--no-update-on-start", action="store_const", const=True, default=False,
                                help="Don't update the calendar on start")

    # startup #
    args = parser.parse_args()
    app.config['TEMPLATES_AUTO_RELOAD'] = args.auto_reload
    app.run(host=args.interface, port=args.port)
