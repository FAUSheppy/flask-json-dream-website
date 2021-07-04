/* determine which size of image to load */
function getSize(src){
    var trueRes = screen.width/Math.min(window.devicePixelRatio, 4)

    if(src.indexOf("scale_fullscreen") > -1 || src.indexOf("wallpaper") > -1 ){
        trueRes = Math.max(trueRes, 800)
        return '?scalex=' + trueRes
    }

    if(trueRes > 1920)
        return '?scalex=1280&scaley=960'
    else if(trueRes <= 1920 && trueRes >= 1200)
        return '?scalex=1280&scaley=960'
    else
        return '?scalex=640&scaley=480'
}

/* check if browser is capable of webp */
function supportsWebp() {
    return true;

    /* alternative to check for webP support */
    //if (!self.createImageBitmap) return false;
    //const webpData = 'data:image/webp;base64,UklGRh4AAABXRUJQVlA4TBEAAAAvAAAAAAfQ//73v/+BiOh/AAA=';
    //return createImageBitmap(webpData).then(() => true, () => false);
}

/* cache */
var webP = supportsWebp()
var elements = null
var counter = 0

/* garantuee initall call evaluates to true */
var viewbox_y = -Infinity

IDENT = "realsrc"
WIDTH_LOCK = "LAZYLOAD_WIDTH"
HEIGHT_LOCK = "LAZYLOAD_HEIGHT"

/* function to load images */
function changeSrc(offset){

    /* check if there was a relevant change */
    var cur_viewbox = -document.getElementById("navbar-ph").getBoundingClientRect().y
    if(cur_viewbox - viewbox_y < 100){
        return;
    }

    /* cache viewbox */
    viewbox_y = cur_viewbox

    /* cache */
    if(elements == null){
        elements = document.querySelectorAll("*[" + IDENT + "]");
    }

    for (var i = counter; i < elements.length; i++) {
            var boundingClientRect = elements[i].getBoundingClientRect();
            if (elements[i].hasAttribute(IDENT)
                    && boundingClientRect.top < window.innerHeight + offset) {

                var newSrc = elements[i].getAttribute(IDENT)
                var xWidth  = elements[i].getAttribute(WIDTH_LOCK)
                var yHeight = elements[i].getAttribute(HEIGHT_LOCK)
                if(!newSrc){
                    console.log(elements[i])
                }
                /* remove url( ... ) */
                //newSrc = newSrc.substring(4,newSrc.length-1)

                if(newSrc.indexOf(".jpg") > -1 
                        || newSrc.indexOf(".png") > -1
                        || newSrc.indexOf(".jpeg") > -1){
                    /* get correct size */
		    if(xWidth || yHeight){
			if(xWidth !=null && yHeight != null){
                    		newSrc += "?scalex=" + xWidth + "&scaley=" + yHeight
			}else if(xWidth != null){
                    		newSrc += "?x=" + xWidth
			}else{
                    		newSrc += "?y=" + yHeight
			}
		    }else{
                    	newSrc += getSize(newSrc)
		    }

                    /* load webP if supported */
                    if(webP){
                        newSrc += '&encoding=webp'
                    }
                }else{
                    /* continue for other formats like svg */
                    elements[i].removeAttribute(IDENT);
                    elements[i].setAttribute("src", newSrc);
                    /* do not set bgImg for these formats */
                    continue;
                }
                elements[i].setAttribute("src", newSrc);
                if(newSrc.indexOf("wallpaper") > -1){
                    elements[i].style.backgroundImage = 'url(' + newSrc +')';
                }
                elements[i].removeAttribute(IDENT);
            }else{
                /* DOM is parsed top down and images are inserted in that order too */
                /* meaing that once we reach pic that insnt in viewbox none following will be*/
                counter = i;
                return;
            }
        }

    /* if we got here we are done */
    window.removeEventListener("scroll",refresh_handler);
    console.log("Listener finished & removed")

}
var refresh_handler = function(e) {
    /* images directly in view first (offset 0)*/
    //changeSrc(0)
    /* then load images almost in view */
    changeSrc(500)
};

/* add listeners */
ms = document.getElementById("main_scrollable")
window.addEventListener('scroll', refresh_handler);
window.addEventListener('resize', refresh_handler);
window.addEventListener('load', refresh_handler);
