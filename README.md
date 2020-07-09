# Requirements
This Softwares runs python3-flask with markdown, json and caldav.

    python3 -m pip install flask, json, caldav, markdown2

This Software requires bootstrap > 4.13 which can be downloaded [here](https://getbootstrap.com/docs/4.3/getting-started/download/). It must be unpacked into the *static/*-directory into *js* and *css* respectively.

Additionally bootstrap depends on [jquery](https://code.jquery.com) which you have to download into a file called *jquery.min.js* in *static/js/*.

# Usage

    ./server.py -h
    usage: server.py [-h] [-i INTERFACE] [-p PORT] --cal-info CAL_INFO
                 [--no-update-on-start]

    optional arguments:
        -h, --help            show this help message and exit
        -i INTERFACE          Interface to listen on (default: 0.0.0.0)
        -p PORT, --port PORT  Port to listen on (default: 5000)
        --cal-info CAL_INFO   File Containing a public calendar link (default: None)
        --no-update-on-start  Don't update the calendar on start (default: False)


# Configuration
The page and most of it's content is configured via json. To use the CalDav-events section, you need to add a comma seperated file with the following format format/information:

    URL,USER,PASSWORD

## Main Config
The main Config ``config.json`` which must be placed in the project-root must contain the following values:

    {
        "siteTitle" : "the default site title",
	"siteDescription" : "a description for this site",
	"siteLogo" : "url to logo",
	"siteURL": "the url of this site"
    }

Additionally it may contain the following information:

    "teamspeak-server" : "TS_SERVER",
    "discord-server" : "DISCORD_LINK",
    "facebook" : "FACEBOOK_LINK",
    "instagram" : "INSTAGRAM_LINK",
    "twitter" : "TWITTER_LINK",
    "twitch-channel" : "TWITCH_CHANNEL_NAME",
    "twitch-placeholder-img" : "PLACEHOLDER_IMG"

## Startpage Sections
### Events
The events section from the start-page is imported from the calendar and will show events a given time in the future or past. It will by default show three events. If there are more than three events, a *'More'*-button will be displayed. If there are no events the section will not be shown at all.

### News/Announcements
This Section will read and display JSON configuration from the *news/*-direcotry. A news-configuration must contain these information:

    {
	    "title" : "title of the announcement",
	    "uid" : a_unique_integer_number,
	    "markdown-file" : "path to markdown file containing the actual announcement",
	    "active" : boolean_if_it_should_be_displayed,
	    "description" : "a short description",
	    "date" : date_posted_as_unix_timestamp,
    }

Additionally it must contain either a 'fixed-timeout' or 'relative-timeout-weeks' after which it will no longer be displayed. If both a specified the fixed timeout takes precedence.

    	"timeout-relative-weeks" : 12,
    	"timeout-fixed" : a_date_as_unix_timestamp

Finally it MAY contain a text to display on the button leading to the article (otherwise it will use a default).

        "link-text" : "maximum 25 characters"

Obviously the markdown file referenced in the configuration must also be created.

### Other Sections
All following sections are read and created from the *vereinSection* directory. Json configuration for these sections much contain these information. The pictures for all the sections should have a similar aspect ratio.

    {
        "picture" : "path to a picture for this section",
        "title" : "A title for this card",
        "text" : "A potentially very long text of multiple lines that will be displayed next to the picture...",
    }

The configuration may contain the following information, which add a button-like link to the section.

    "moreInfoButtonText" : "less than 25 charaters",
    "moreInfoButtonHref" : "href to go to"

The alpha-numeric order of the filenames specifies the order in which the sections will be displayed on the website, so the files should be prefixed with a number, for example *10_section_hello.json* and *90_section_ending.json*.

## People
To display a person on the people-subpage create a JSON-file in the *people/*-directory containing the following information:

    {
        "title" : "Name of the Person",
        "subtitle" : "Function of the Person",
        "image" : "path to image",
        "text" : "Potentially long text describing the person and their functions."
    }

The order is again specified by the alpha-numeric order of the files.

# Adding new Subpages
New subpages must be added as a new location in the *server.py* like this:

    @app.route("/subpage")
    def subpage():
        return flask.render_template("subpage.html", conf=mainConfig)

See the example subpage-templates in *templates/*.
