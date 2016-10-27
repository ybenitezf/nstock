# -*- coding: utf-8 -*-

def index():
    if not auth.user:
        return A(T('Login to comment'), _href=URL('default', 'user/login'))

    item_id = request.args(0)

    tbl = db.plugin_comment_comment
    tbl.item_id.default = item_id
    form = SQLFORM(tbl,
        submit_button=T('Comment'),
        formstyle='bootstrap3_stacked')

    rows = db(
        (tbl.id > 0) & (tbl.item_id == request.args(0))
    ).select(orderby=~tbl.created_on)

    if form.process().accepted:
        response.flash = T('Comment posted')
        response.js = "jQuery('#%s').get(0).reload();" % request.cid
        # send notifications to the users, except the current one
        
    return dict(form=form, comments=rows)
