# -*- coding: utf-8 -*-
from mail import item_notify_users

if False:
    from gluon import T, URL, SQLFORM
    from gluon import current, redirect
    from db import db, auth
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache


@auth.requires_login()
def index():
    item_id = request.args(0) or redirect(URL('default', 'index.html'))
    item = db.item(item_id)

    tbl = db.plugin_comment_comment
    tbl.item_id.default = item.id
    form = SQLFORM(
        tbl,
        submit_button=T('Comment'),
        formstyle='bootstrap3_stacked')

    rows = db(
        (tbl.id > 0) & (tbl.item_id == item.id)
    ).select(orderby=~tbl.created_on)

    if form.process().accepted:
        response.flash = T('Comment posted')
        response.js = "jQuery('#%s').get(0).reload();" % request.cid
        # send notifications to the users, except the current one
        subject = T("Comments on %s", (item.headline,))
        # get the comment body
        comment = tbl(form.vars.id)
        message = response.render(
            'plugin_comment/someone_commented.txt',
            dict(item=item, comment=comment, user=auth.user)
        )
        item_notify_users(item.id, subject=subject, message=message)

    return dict(form=form, comments=rows)
