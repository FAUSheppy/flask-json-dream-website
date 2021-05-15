function submitContactForm(){

    /* check input fields */
    mailField = document.getElementById("email")
    messageField = document.getElementById("message")

    if(mailField.value == ""){
        alert("Bitte geben Sie einen Kontakt an unter dem wir Sie erreichen können!")
        return
    }

    if(messageField.value == ""){
        alert("Nachricht ist leer!")
        return
    }

    /* show the waiting dialog */
    dialog = document.getElementById("waiting-dialog")
    dialog.style.disply = "block"
    setMainBackgroundOpacity(0.5)

    /* submit the form */
    xhr = new XMLHttpRequest();
    xhr.open("POST", "/kontakt.php"); 
    xhr.onload = formSubmitFinished

    formData = new FormData(document.getElementById("contact-form")); 

    formData.append("sinfo", "dsenda");
    formData.append("in", "");
    formData.append("anrede", "Herr/Frau");
    formData.append("vorname", "");
    formData.append("fname", formData.get("name"));
    formData.append("mail",  formData.get("telefon"));
    formData.append("ma", 0);

    xhr.send(formData);

}

function formSubmitFinished(event){ 
    if(event.target.status < 200 || event.target.status >= 300){
        showErrorMessage(event.target); // blocking
        setMainBackgroundOpacity(1)
    }else{
        window.location.href = "/thanks"
    }
}

function setMainBackgroundOpacity(opacity){
    mainContainer = document.getElementById("main-container")
    mainContainer.style.opacity = opacity
}

function showErrorMessage(target){
    console.log(target)
    alert("Error: " + target.statusText)
}
