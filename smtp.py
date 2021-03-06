import sys
import smtplib

def checkSMTPConnection(app):
    '''Check connection and login on SMTP server configured in app config'''

    try:
        if not all([ x in app.config and app.config[x] for x in ["TARGET_SMTP", "TARGET_EMAIL"]]):
            raise smtplib.SMTPException("Missing Configuration.")
        smtpTarget = smtplib.SMTP(app.config["TARGET_SMTP"])
        if app.config["TARGET_SMTP_USER"] and app.config["TARGET_SMTP_PASSWORD"]:
            smtp.login(app.config["TARGET_SMTP_USER"], app.config["TARGET_SMTP_PASSWORD"])
        smtpTarget.quit()
    except (smtplib.SMTPException, ConnectionRefusedError) as e:
        if app.config["SMTP_MUST_BE_CONNECTED"]:
            print(e, file=sys.stderr)
            sys.exit(1)
        else:
            print("Warning: SMTP unusable: {}".format(e), file=sys.stderr)

def sendMailFromHtmlForm(app, htmlForm):
    '''Take the app config and the contact HTML-form and send a mail accordingly'''

    email   = htmlForm["email"]
    name    = htmlForm["name"]
    message = htmlForm["message"]
    subject = htmlForm["subject"]

    subject = "Subject: {} ({})\n\n".format(subject, name)

    smtpTarget = smtplib.SMTP(app.config["TARGET_SMTP"])
    smtpTarget.sendmail(email, app.config["TARGET_EMAIL"] , message)
    smtpTarget.quit()
