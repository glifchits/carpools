
from flask import request, url_for, redirect, session
from flask import Blueprint, current_app as app
from schema import *
from app.config import CONFIG

import smtplib

email = Blueprint('email', __name__, url_prefix = '/email')


@email.route('/<ride_id>', methods=['POST'])
def send_email(ride_id):
    app.logger.debug(ride_id)
    app.logger.debug(request.values)

    sender = request.values.get('from')
    recipient = request.values.get('to')
    subject = request.values.get('subject')
    message = request.values.get('message')

    sender = session['user']['email']
    ride = Ride.objects(id = ride_id).first()
    recipient = ride.driver.email

    app.logger.debug(sender)
    app.logger.debug(recipient)

    smtpserver = 'smtp.gmail.com:587'
    header  = "From: %s\n" % sender
    header += "To: %s\n" % recipient
    header += "Cc: \n"
    header += "Subject: %s\n\n" % subject
    message = header + message

    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(CONFIG['email-login'], CONFIG['email-pass'])
    problems = server.sendmail(sender, list(recipient), message)
    server.quit()

    app.logger.debug('problems: ' + str(problems))
    return '404'



