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
    return /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);

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
                if(!newSrc){
                    console.log(elements[i])
                }
                /* remove url( ... ) */
                //newSrc = newSrc.substring(4,newSrc.length-1)

                if(newSrc.indexOf(".jpg") > -1 
                        || newSrc.indexOf(".png") > -1
                        || newSrc.indexOf(".jpeg") > -1){
                    /* get correct size */
                    newSrc += getSize(newSrc)

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

function initComparisons() {
  var x, i;
  /* Find all elements with an "overlay" class: */
  var containers = document.getElementsByClassName("slider-container");
  x = document.getElementsByClassName("img-comp-overlay");
  console.log(x)
  for (i = 0; i < containers.length; i++) {
    /* Once for each "overlay" element:
    pass the "overlay" element as a parameter when executing the compareImages function: */

    var refImage = containers[i].children[2]
    var testw = refImage.width
    var testh = refImage.height

    containers[i].children[0].children[0].width = testw
    containers[i].children[1].children[0].width = testw
    containers[i].children[0].children[0].height = testh
    containers[i].children[1].children[0].height = testh

    containers[i].children[0].style.opacity = 1
    containers[i].children[1].style.opacity = 1

    compareImages(x[i], refImage);
  }
  function compareImages(img, refImage) {
    var slider = null;
    var clicked = 0;
    /* Get the width and height of the img element */
    var w = img.offsetWidth;
    var h = img.offsetHeight;
    /* Set the width of the img element to 50%: */
    img.style.width = (w / 2) + "px";
    /* Create slider: */
    slider = document.createElement("DIV");
    slider.setAttribute("class", "img-comp-slider");
    /* Insert slider */
    img.parentElement.insertBefore(slider, img);
    /* Position the slider in the middle: */
    slider.style.top = (h / 2) - (slider.offsetHeight / 2) + "px";
    slider.style.left = (w / 2) - (slider.offsetWidth / 2) + "px";
    /* Execute a function when the mouse button is pressed: */
    slider.addEventListener("mousedown", slideReady);
    /* And another function when the mouse button is released: */
    window.addEventListener("mouseup", slideFinish);
    /* Or touched (for touch screens: */
    slider.addEventListener("touchstart", slideReady);
     /* And released (for touch screens: */
    window.addEventListener("touchend", slideFinish);
    function slideReady(e) {
      /* Prevent any other actions that may occur when moving over the image: */
      e.preventDefault();
      /* The slider is now clicked and ready to move: */
      clicked = 1;
      /* Execute a function when the slider is moved: */
      window.addEventListener("mousemove", slideMove);
      window.addEventListener("touchmove", slideMove);
    }
    function slideFinish() {
      /* The slider is no longer clicked: */
      clicked = 0;
    }
    function slideMove(e) {
      var pos;
      /* If the slider is no longer clicked, exit this function: */
      if (clicked == 0) return false;
      /* Get the cursor's x position: */
      pos = getCursorPos(e)
      /* Prevent the slider from being positioned outside the image: */
      if (pos < 0) pos = 0;
      if (pos > w) pos = w;
      /* Execute a function that will resize the overlay image according to the cursor: */
      slide(pos);
    }
    function getCursorPos(e) {
      var a, x = 0;
      e = e || window.event;
      /* Get the x positions of the image: */
      a = img.getBoundingClientRect();
      /* Calculate the cursor's x coordinate, relative to the image: */
      x = e.pageX - a.left;
      /* Consider any page scrolling: */
      x = x - window.pageXOffset;
      return x;
    }
    function slide(x) {
      /* Resize the image: */
      img.style.width = x + "px";
      /* Position the slider: */
      slider.style.left = img.offsetWidth - (slider.offsetWidth / 2) + "px";
    }
  }
}
