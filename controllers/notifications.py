# coding: utf-8
if False:
    from gluon import current
    response = current.response
    from db import db, auth


@auth.requires_login()
def has_notifications():
    query = (db.notification.id > 0)
    query &= (db.notification.seen == False)
    query &= (db.notification.to_user == auth.user.id)

    nots = db(query).select(db.notification.ALL)

    if nots:
        return response.json(True)

    return response.json(False)
