#!/usr/bin/python3
import json
import os
import flask
import argparse

import caldav
import datetime as dt
import markdown2

# sitemap utilities #
from werkzeug.routing import BuildError
import xml.etree.ElementTree as et

VEREIN_SECTIONS_DIR = "sections/"
MAIN_LINKS_DIR = "main-links/"
NEWS_DIR = "news/"

app = flask.Flask("athq-landing-page", static_folder=None)
mainConfig = dict()
with open("config.json") as f:
    mainConfig = json.load(f)

caldavUrl = None
caldavPassword = None
caldavUsername = None

def updateEventsFromCalDav():


    if app.config["USE_CALENDAR"]:
        client = caldav.DAVClient(url=caldavUrl, username=caldavUsername, password=caldavPassword)
        authenticatedClient = client.principal()
        defaultCal = authenticatedClient.calendars()[0]

        start = dt.datetime.now()
        start = start - dt.timedelta(seconds=start.timestamp() % dt.timedelta(days=1).total_seconds())
        end   = start + dt.timedelta(days=90)

        # TODO remove this
        # start = start - dt.timedelta(days=90)

        events = sorted(defaultCal.date_search(start, end), 
                            key=lambda e: e.vobject_instance.vevent.dtstart.value)
        eventsDictList = []
        for e in events:
            date = e.vobject_instance.vevent.dtstart.value
            date += dt.timedelta(hours=2)
            newEventDict = { "description" : e.vobject_instance.vevent.summary.value,
                             "time" : date.strftime("%H:%M"),
                             "day" :   date.strftime("%d"),
                             "month" : date.strftime("%b"),
                             "year" :  date.strftime("%Y")                       }
            try:
                newEventDict.update({ "location" : e.vobject_instance.vevent.location.value })
            except AttributeError:
                pass
            eventsDictList += [newEventDict]
    else:
        eventsDictList = []

    with open("cache.json", "w") as f:
        json.dump(eventsDictList, f)


def getEventsCache():
    with open("cache.json", "r") as f:
        return json.load(f)

def readJsonDir(basedir):

    # load json files from projects/ dir #
    jsonDictList =[]
    for root, dirs, files in os.walk(basedir):
        for filename in sorted(files):
            if filename.endswith(".json"):
                with open(os.path.join(basedir, filename)) as f:
                    jsonDictList += [json.load(f)]

    return jsonDictList

def parseNewsDirWithTimeout():

    TIMEOUT_RELATIVE = "timeout-relative-weeks"
    TIMEOUT_FIXED = "timeout-fixed"
    PARSED_TIME = "parsed-time"
    ACTIVE = "active"
    DATE = "date"

    news = readJsonDir(NEWS_DIR)
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
    updateEventsFromCalDav();
    return ("", 204)

@app.route("/")
def root():
    announcements = parseNewsDirWithTimeout()
    return flask.render_template("index.html",  mainLinks=readJsonDir(MAIN_LINKS_DIR),
                                                siteTitle=mainConfig["siteTitle"],
                                                conf=mainConfig,
                                                events=getEventsCache(),
                                                moreEvents=len(getEventsCache())>3,
                                                vereinSections=readJsonDir(VEREIN_SECTIONS_DIR),
                                                announcements=announcements)

@app.route("/impressum")
def impressum():
    return flask.render_template("impressum.html", conf=mainConfig)

@app.route("/verein")
def verein():
    return flask.render_template("verein.html", conf=mainConfig)

@app.route("/stammtisch")
def stammtisch():
    return flask.render_template("stammtisch.html", conf=mainConfig)

@app.route("/people")
def people():
    return flask.render_template("people.html", conf=mainConfig,
                                                people=readJsonDir("people/"))

@app.route("/news")
def news():

    uid = flask.request.args.get("uid")

    news = parseNewsDirWithTimeout()
    newsDict = dict()
    for n in news:
        newsDict.update( { n["uid"] : n } )

    if not uid:
        article = sorted(news, key=lambda n: n["parsed-time"])[-1]
    elif not newsDict[int(uid)]:
        return ("", 404)
    else:
        article = newsDict[int(uid)]
    try:
        with open(article["markdown-file"]) as f:
            article.update( { "markdown-content" : markdown2.markdown(f.read()) } )
    except FileNotFoundError as e:
        return ("File not found Error ({})".format(e), 404)

    return flask.render_template("news.html", conf=mainConfig, article=article)

@app.route("/static/<path:path>")
def sendStatic(path):
    if "pictures" in path:
        cache_timeout = 2592000
    else:
        cache_timeout = None
    return flask.send_from_directory('static', path, cache_timeout=cache_timeout)

@app.route('/defaultFavicon.ico')
def icon():
    return app.send_static_file('defaultFavicon.ico')

@app.route("/sitemap.xml")
def siteMap():
    urls = []
    for rule in app.url_map.iter_rules():
        skips = ["icon", "siteMap", "invalidate", "news"]
        if any([s in rule.endpoint for s in skips]):
            continue
        if "GET" in rule.methods:
            try:
                url = flask.url_for(rule.endpoint, **(rule.defaults or {}))
                priority = 0.8
                if rule.endpoint == "root":
                    priority = 1.0
                urls += [(url, app.config["START_TIME"], priority)]
            except BuildError:
                pass

    news = parseNewsDirWithTimeout()
    for n in filter(lambda x: x["active"], news):
        urls += [("/news?uid={}".format(n["uid"]), n["parsed-time"], 0.8)]

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

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Projects Showcase',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # general parameters #
    parser.add_argument("-i", "--interface", default="0.0.0.0", help="Interface to listen on")
    parser.add_argument("-p", "--port", default="5000", help="Port to listen on")
    parser.add_argument("--cal-info", help="File Containing a public calendar link")
    parser.add_argument("--no-update-on-start", action="store_const", const=True, default=False,
                                help="Don't update the calendar on start")

    # startup #
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    args = parser.parse_args()
   
    if args.cal_info:
        app.config["USE_CALENDAR"] = True
        with open(args.cal_info) as f:
            caldavUrl, caldavUsername, caldavPassword = f.read().strip().split(",")
    else:
        app.config["USE_CALENDAR"] = False

    if not args.no_update_on_start:
        updateEventsFromCalDav()

    app.config["START_TIME"] = dt.datetime.now()

    app.run(host=args.interface, port=args.port)
