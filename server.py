#!/usr/bin/python3
import json
import os
import flask
import argparse
import jinja2
import sys

import caldav
import datetime as dt
import markdown2
import PIL.Image

# sitemap utilities
from werkzeug.routing import BuildError
from werkzeug.utils   import ImportStringError
import xml.etree.ElementTree as et

# import project files
import smtp

# paths
SECTIONS_DIR   = "sections/"
NEWS_DIR       = "news/"
PICTURES_DIR   = "pictures/"
MAIN_LINKS_DIR = "mainLinks/"
PEOPLE_DIR     = "people/"
CACHE_FILE     = "cache.json"

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
HTTP_NO_CONTENT = 204
EMPTY_STRING   = ""
READ           = "r"
WRITE          = "w"

# subpages
IDENTIFIER_PREFIX   = "PAGE_"
CONFIG_POSTFIX      = "_EXTRA_CONFIG"
SUBPAGE_CONFIG_FILE = "subpages.json"
SUBPAGE_CONTENT_DIR = "subpages/"

app = flask.Flask("FLASK_JSON_DREAM_WEBSITE", static_folder=None)

try:
    app.config.from_object("config_prod")
except ImportStringError:
    print("Rename example_config.py to config_prod.py!", file=sys.stderr)
    sys.exit(1)

def updateEventsFromCalDav():
    '''Load event from a remote calendar'''

    if app.config["SHOW_CALENDAR"]:
        client = caldav.DAVClient(url=app.config["CALENDAR_URL"],
                                    username=app.config["CALENDAR_USERNAME"],
                                    password=app.config["CALENDAR_PASSWORD"])
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

    if not os.path.isfile(CACHE_FILE):
        return []

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

    if not jsonDictList:
        print("Warning: {} is an empty directory".format(basedir), file=sys.stderr)

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

    impressumPath = os.path.join(app.config["CONTENT_DIR"], "impressum.html")
    impressumTextPath = os.path.join(app.config["CONTENT_DIR"], "impressum_text.html")

    impressumText = None
    impressumFull = None
    
    with open(impressumTextPath) as f:
        impressumText = flask.Markup(f.read())

    with open(impressumPath) as f:
        impressumFull = flask.render_template_string(f.read(), conf=app.config, text=impressumText)
        return flask.render_template("stub.html", content=impressumFull)

@app.route("/thanks")
def thanks():
    '''Page to be displayed after successfully submitting a contact form'''

    thanksTemplatePath = os.path.join(app.config["CONTENT_DIR"], "thanks.html")
    thanksTemplate = None

    with open(thanksTemplatePath) as f:
        thanksTemplate = flask.Markup(flask.render_template_string(f.read(), conf=app.config,
                                                                    footerFixBottom=True))

    return flask.render_template("stub.html", content=thanksTemplate)

@app.route("/people")
def people():
    peopleDict = readJsonDir(os.path.join(app.config["CONTENT_DIR"], PEOPLE_DIR))
    return flask.render_template("people.html", conf=app.config, people=peopleDict)

@app.route("/content/")
def content():
    identifier = IDENTIFIER_PREFIX + flask.request.args.get("id")
    container=False
    if identifier in app.config:

        # check for extra config # 
        extraConfigDir = app.config[identifier + CONFIG_POSTFIX]
        commonName  = app.config.get(identifier + CONFIG_POSTFIX + "cn")
        extraConfig = None
        markupText  = None
        if extraConfigDir:
            fullpath = os.path.join(app.config["CONTENT_DIR"], extraConfigDir)
            if os.path.isdir(fullpath):
                extraConfig = readJsonDir(fullpath)

                # picture slider! #
                for section in extraConfig:
                    if section["picture"]:
                        section.update({"picture-overlay" : section["picture"][:-4] + "_g.jpg"})

                markupText = flask.Markup(flask.render_template(app.config[identifier],
                        extraConfig=extraConfig, commonName=commonName))
            else:
                with open(fullpath) as f:
                    markupText = markdown2.markdown(f.read())
                    container = True

        return flask.render_template("default_content.html", container=container,
                                        conf=app.config, markupText=markupText,
                                        commonName=commonName)
    else:
        return (EMPTY_STRING, HTTP_NOT_FOUND)

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
        with open(os.path.join(app.config["CONTENT_DIR"], article[MARKDOWN_FILE_KEY])) as f:
            article.update( { MARKDOWN_CONTENT_KEY : markdown2.markdown(f.read()) } )
    except FileNotFoundError as e:
        return ("File not found Error ({})".format(e), HTTP_NOT_FOUND)

    return flask.render_template("news.html", conf=app.config, article=article, title=article["title"])

@app.route("/static/<path:path>")
def sendStatic(path):
    cache_timeout = 2592000
    return flask.send_from_directory('static', path, cache_timeout=cache_timeout)

def generatePicture(pathToOrig, scaleX, scaleY, encoding):
    '''Generate an pictures with the requested scales and encoding if it doesn't already exist'''

    CACHE_DIR = os.path.join(app.config["PICTURES_DIR"], "cache/")

    if os.path.isfile(CACHE_DIR):
        raise OSError("Picture cache dir is occupied by a file!")
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    filename, extension = os.path.splitext(os.path.basename(pathToOrig))
    if not encoding:
        encoding = extension.strip(".")

    # just python things... #
    if encoding.lower() == "jpg":
        encoding = "jpeg"

    # open image #
    image = PIL.Image.open(os.path.join(app.config["PICTURES_DIR"], pathToOrig))

    # ensure sizes are valid #
    x, y = image.size
    if not scaleY:
        scaleY = y
    scaleX = min(x, scaleX)
    scaleY = min(y, scaleY)

    # generate new paths #
    newFile = "x-{x}-y-{y}-{fname}.{ext}".format(x=scaleX, y=scaleY, fname=filename, ext=encoding)
    newPath = os.path.join(CACHE_DIR, newFile)

    # save image with new size and encoding #
    image.thumbnail((scaleX, scaleY), PIL.Image.ANTIALIAS)
    image.save(newPath, encoding)

    # strip the STATIC_DIR because we will use send_from_directory for safety #
    REPLACE_ONCE = 1
    return newPath.replace(app.config["PICTURES_DIR"], "", REPLACE_ONCE)

@app.route("/picture/<path:path>")
def sendPicture(path):
    cache_timeout = 2592000

    scaleY = flask.request.args.get("scaley")
    scaleX = flask.request.args.get("scalex")
    if scaleY:
        scaleY = round(float(scaleY))
    if scaleX:
        scaleX = round(float(scaleX))
        path = generatePicture(path, scaleX, scaleY, flask.request.args.get("encoding"))

    raw = flask.send_from_directory(app.config["PICTURES_DIR"], path, cache_timeout=cache_timeout)
    response = flask.make_response(raw)
    response.headers['X-ATHQ-INTERNAL-FID'] = path

    return response

@app.route('/defaultFavicon.ico')
def icon():
    return flask.send_from_directory(app.config["CONTENT_DIR"], 'defaultFavicon.ico')

@app.route('/robots.txt')
def robots():
    return flask.send_from_directory(app.config["CONTENT_DIR"], 'robots.txt')

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

    # add /content/ to sitemap #
    content = filter(lambda x: x.startswith(IDENTIFIER_PREFIX), app.config.keys())
    uniqueContent = filter(lambda x: not x.endswith(CONFIG_POSTFIX), content)
    for c in uniqueContent:
        idWithoutPrefix = c.lstrip(IDENTIFIER_PREFIX)
        urls += [("/content?id={}".format(idWithoutPrefix), app.config["START_TIME"],
                                                                        PRIORITY_PRIMARY)]

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
    '''Before first request configuration'''

    app.config["SECTIONS_DIR"]   = os.path.join(app.config["CONTENT_DIR"], SECTIONS_DIR)
    app.config["NEWS_DIR"]       = os.path.join(app.config["CONTENT_DIR"], NEWS_DIR)
    app.config["MAIN_LINKS_DIR"] = os.path.join(app.config["CONTENT_DIR"], MAIN_LINKS_DIR)
    app.config["PICTURES_DIR"]   = os.path.join(app.config["CONTENT_DIR"], PICTURES_DIR)

    if app.config["RELOAD_CALENDAR_ON_START"]:
        updateEventsFromCalDav()
    
    app.config["START_TIME"] = dt.datetime.now()

    # add additional pages if they exist #
    subpageConfigFileTmp = os.path.join(app.config["CONTENT_DIR"], SUBPAGE_CONFIG_FILE)
    if os.path.isfile(subpageConfigFileTmp):
        
        # parse subpage config file #
        subpages = dict()
        with open(subpageConfigFileTmp) as f:
            subpages = json.load(f)

        # set template paths for identifier in app config #
        for identifier in subpages.keys():
            if type(subpages[identifier]) == dict:
                app.config[IDENTIFIER_PREFIX + identifier] = subpages[identifier]["template"]
                configKey = IDENTIFIER_PREFIX + identifier + CONFIG_POSTFIX
                if "config-dir" in subpages[identifier]:
                    app.config[configKey] = subpages[identifier]["config-dir"]
                else:
                    app.config[configKey] = subpages[identifier]["markdown"]
                if "cn" in subpages[identifier]:
                    app.config[configKey + "cn"] = subpages[identifier]["cn"]
            else:
                app.config[IDENTIFIER_PREFIX + identifier] = subpages[identifier]
                app.config[IDENTIFIER_PREFIX + identifier + CONFIG_POSTFIX] = None

        # set custom loader to support second template dir #
        subpageContentDirTmp = os.path.join(app.config["CONTENT_DIR"], SUBPAGE_CONTENT_DIR)
        fsLoader = jinja2.FileSystemLoader([subpageContentDirTmp])

        choiceLoader = jinja2.ChoiceLoader([ app.jinja_loader, fsLoader])
        app.jinja_loader = choiceLoader
    else:
        print("Warning: Subpage Config File not found", file=sys.stderr)

    ## check if SMTP server is availiable ##
    smtp.checkSMTPConnection(app)


@app.route("/contact")
def contact():
    key=None
    if app.config['PGP_PUB_KEY_FILE']:
        with open(os.path.join(app.config["CONTENT_DIR"], app.config['PGP_PUB_KEY_FILE'])) as f:
            key = f.read().strip()
    return flask.render_template("contact.html", conf=app.config, PGP_KEY=key)

@app.route("/contact-api", methods=['POST'])
def contactAPI():
    '''Form Location for Contact Form to be submitted to target email'''

    smtp.sendMailFromHtmlForm(app, flask.request.form)
    return (EMPTY_STRING, HTTP_NO_CONTENT)

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
