# -*- coding: utf-8 -*-
if False:
    from gluon import current
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T
    from db import db, auth, service


@auth.requires_login()
def index():
    """
    Show user items list
    """
    # accessible_query(name, table, user_id=None)
    # query =  (db.item.id > 0)
    # query &= (auth.accessible_query('collaborator', db.item) |
    #     auth.accessible_query('owner', db.item))
    # grid = SQLFORM.grid(query,
    #     orderby=[~db.item.modified_on],
    #     create=False,
    #     csv=False,
    #     paginate=1,
    # )

    response.title = T('eNews - CAST')

    # return dict(grid=grid)
    return locals()


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth
    to allow administrator to manage users
    """
    form = auth()
    return dict(form=form)


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()
