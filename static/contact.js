function submitForm(){

    /* show the waiting dialog */
    dialog = document.getElementById("waiting-dialog")
    dialog.style.disply = "block"
    setMainBackgroundOpacity(0.5)

    /* submit the form */
    xhr = new XMLHttpRequest();
    xhr.open("POST", "/your/url/name.php"); 
    xhr.onload = 
    formData = new FormData(document.getElementById("contact-form")); 
    xhr.send(formData);

    mainContainer = document.getElementById("main-container")
    mainContainer.style.opacity = 0.5

    window.location.href = "/thanks"
    // after x seconds forward to thx

}

function formSubmitFinished(event){ 
    if(event.target.status != 200){
        showErrorMessage(); // blocking
        setMainBackgroundOpacity(0.5)
    }else{
        window.location.href = "/thanks"
    }
}

function setMainBackgroundOpacity(opacity){
    mainContainer = document.getElementById("main-container")
    mainContainer.style.opacity = opacity
}
