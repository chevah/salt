# -*- coding: utf-8 -*-
'''
Module for Sending Messages via SMTP

.. versionadded:: Helium

:depends:   - smtplib python module
:configuration: This module can be used by either passing a jid and password
    directly to send_message, or by specifying the name of a configuration
    profile in the minion config, minion pillar, or master config.

    For example:

    .. code-block:: yaml

        my-smtp-login:
            smtp.server: smtp.domain.com
            smtp.sender: admin@domain.com
            smtp.username: myuser
            smtp.password: verybadpass

    The resourcename refers to the resource that is using this account. It is
    user-definable, and optional. The following configurations are both valid:

    .. code-block:: yaml

        my-smtp-login:
            smtp.server: smtp.domain.com
            smtp.sender: admin@domain.com
            smtp.username: myuser
            smtp.password: verybadpass

        my-smtp-login:
            smtp.server: smtp.domain.com
            smtp.sender: admin@domain.com
            smtp.username: myuser
            smtp.password: verybadpass

'''
import logging
import socket

log = logging.getLogger(__name__)

HAS_LIBS = False
try:
    import smtplib
    import email.mime.text
    HAS_LIBS = True
except ImportError:
    pass


__virtualname__ = 'smtp'


def __virtual__():
    '''
    Only load this module if smtplib is available on this minion.
    '''
    if HAS_LIBS:
        return __virtualname__
    return False


def send_msg(recipient,
        message,
        subject='Message from Salt',
        sender=None,
        server=None,
        use_ssl='True',
        username=None,
        password=None,
        profile=None):
    '''
    Send a message to an SMTP recipient. Designed for use in states.

    CLI Examples::

        smtp.send_msg 'admin@example.com' 'This is a salt module test' \
            profile='my-smtp-account'
        smtp.send_msg 'admin@example.com' 'This is a salt module test' \
            username='myuser' password='verybadpass' sender="admin@example.com' \
            server='smtp.domain.com'
    '''
    if profile:
        creds = __salt__['config.option'](profile)
        server = creds.get('smtp.server')
        sender = creds.get('smtp.sender')
        username = creds.get('smtp.username')
        password = creds.get('smtp.password')

    msg = email.mime.text.MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    try:
        if use_ssl in ['True', 'true']:
            smtpconn = smtplib.SMTP_SSL(server)
        else:
            smtpconn = smtplib.SMTP(server)

    except socket.gaierror, _error:
        log.debug("Exception: {0}" . format(_error))
        return False

    if not use_ssl in ['True', 'true']:
        smtpconn.ehlo()
        if smtpconn.has_extn('STARTTLS'):
            try:
                smtpconn.starttls()
            except smtplib.SMTPHeloError:
                log.debug("The server didn’t reply properly \
                        to the HELO greeting.")
                return False
            except smtplib.SMTPException:
                log.debug("The server does not support the STARTTLS extension.")
                return False
            except RuntimeError:
                log.debug("SSL/TLS support is not available \
                        to your Python interpreter.")
                return False
            smtpconn.ehlo()

    if username and password:
        try:
            smtpconn.login(username, password)
        except smtplib.SMTPAuthenticationError, _error:
            log.debug("SMTP Authentication Failure")
            return False

    try:
        smtpconn.sendmail(sender, [recipient], msg.as_string())
    except smtplib.SMTPRecipientsRefused:
        log.debug("All recipients were refused.")
        return False
    except smtplib.SMTPHeloError:
        log.debug("The server didn’t reply properly to the HELO greeting.")
        return False
    except smtplib.SMTPSenderRefused:
        log.debug("The server didn’t accept the {0}.".format(sender))
        return False
    except smtplib.SMTPDataError:
        log.debug("The server replied with an unexpected error code.")
        return False

    smtpconn.quit()
    return True
