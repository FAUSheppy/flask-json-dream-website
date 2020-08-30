# Requirements
This Softwares runs python3-flask with markdown, json and caldav.

    python3 -m pip install flask, caldav, markdown2

This Software requires bootstrap > 4.13 which can be downloaded [here](https://getbootstrap.com/docs/4.3/getting-started/download/). It must be unpacked into the *static/*-directory into *js* and *css* respectively.

Additionally bootstrap depends on [jquery](https://code.jquery.com) which you have to download into a file called *jquery.min.js* in *static/js/*.

# Configuration
The page and most of it's content is configured via json, basic configuration is done in *config.py*.

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
All following sections are read and created from the *sections* directory. Json configuration for these sections must contain the following information. The pictures for all the sections should have a similar aspect ratios.

    {
        "picture" : "path to a picture for this section",
        "title" : "A title for this card",
        "text" : "A potentially long text with multiple lines that will be displayed next to the picture...",
    }

The configuration may contain the following information, which add a button-like link to the section.

    "moreInfoButtonText" : "less than 25 charaters",
    "moreInfoButtonHref" : "/href/to/go/to"

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
You can add new subpages in the *content*-location via a *subpages.json* file denoting an identifier as key and a HTML-template as value, like this:

    {
        "identifier-1" : "html-template-1.html",
        "identifier-2" : "html-template-2.html"
    }

You can also give identifier complex objects pointing to another config dir which will be parsed by *readJsonDir* and passed to *render_template* as a list of dictionary objects called *"extraConfig"*:

    {
        "identifier-1" : {
            "template" : "html-template-1.html",
            "config-dir" : "config_dir_in_content_dir"
    }

# Contact Page
Templates for the contact information and legal page can be found in the example content directory. It can be edited freely and is just a suggestion.

The templates referenced here must be located in a *subpages/* directory and will be made availiable at */content?id=identifier*.
