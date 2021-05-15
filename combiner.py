#!/usr/bin/python3

import requests
import os

TARGET_DIV = "mobile-display"
TARGET_DIR = "/home/ik15ydit/reps/ths-website-full"

# "php-file" : "flask-url"
MAP = {
            "impressum.php"       : "/impressum",
            "datenschutz.php"     : "/impressum",
            "schimmel.php"        : "/content/?id=gebaeude-schimmel",
            "gebaeudecheck.php"   : "/content/?id=gebaeude-gebaeudecheck",
            "luftdichtheit.php"   : "/content/?id=gebaeude-luftdichtheit",
            "index.php"           : "/",
            "kontakt.php"         : "/contact",
            "leckageortung.php"   : "/content/?id=wasserschaeden-leckageortung",
            "leitunsgsortung.php" : "/content/?id=wasserschaeden-leitungsortung",
            "schaltanlagen.php"   : "/content/?id=anlagen-elektronik-schaltanlagen",
            "elektronik.php"      : "/content/?id=anlagen-elektronik-elektronik",
            "technologie.php"     : "/content/?id=technologie",
            "trocknung.php"       : None
        }

REVERSE_MAP = { "/contact" : "/kontakt.php" }
for k,v in MAP.items():
    if not v or not "content" in v:
        continue
    REVERSE_MAP.update({ v : k })

for key, value in MAP.items():
    
    if value:
        # create new mobile section # 
        phpFile = os.path.join(TARGET_DIR, key)
        response = requests.get("http://localhost:5000" + value)
        mobileFile = os.path.join(TARGET_DIR, key[:-4]) + "-mobile.php" 

        with open(mobileFile, "w") as f:
            foundStart = False
            for l in response.content.decode("utf-8").split("\n"):

                # look for start #
                if not foundStart:
                    if "mobile-display" in l:
                        foundStart = True
                    else:
                        continue

                # skip end
                if "</body>" in l or "</html>" in l:
                    continue

                for k in REVERSE_MAP.keys():
                    if k and "href=\"" + k in l:
                        l = l.replace("href=\"" + k, "href=\"" + REVERSE_MAP[k])
                f.write(l)
                f.write("\n")

        # read old toplevel file #
        contentNew = []
        with open(os.path.join(TARGET_DIR, key), "r") as f:

            for l in f:

                contentNew += [l]
                if "footerbereich" in l:
                    contentNew += [ "require('{}');\n".format(key[:-4] + "-mobile.php") ]
                    contentNew += [ "require('module/endhtml.php');\n" ]

        # write updated toplevel file
        with open(os.path.join(TARGET_DIR, key), "w") as f:
            f.write("".join(contentNew))    

    if not value:
        content = []
        with open(os.path.join(TARGET_DIR, key), "r") as f:
            content = f.read().split("\n")

        with open(os.path.join(TARGET_DIR, key), "w") as f:
            content = content[:-1]
            content += ["require('module/endhtml.php')"]
            content += ["?>"]
            f.write("\n".join(content));
