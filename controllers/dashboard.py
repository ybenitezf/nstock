# -*- coding: utf-8 -*-

if False:
    from gluon import SQLFORM, URL, CAT, IS_NOT_EMPTY
    from gluon import current, redirect, Field
    from db import db, auth
    from dc import application
    from z_whoosh import Whoosh
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T


def activeDashboard(dash_id):
    dash = db.dashboard(dash_id)

    if dash:
        session.dashboard = dash.id


def isOwner(dash_id=None):
    dash_id = dash_id or request.args(0)
    return auth.has_permission(
        'owner', db.dashboard, record_id=dash_id)


@auth.requires_login()
def toogle_on():
    dash = db.dashboard(request.args(0))
    activeDashboard(dash.id)
    response.js = "jQuery('#dashboard_cmp').get(0).reload();"
    response.js += "jQuery('#main').get(0).reload();"
    return CAT('')


@auth.requires(isOwner())
def index():
    """Show the item list of this dashboard"""
    dash = db.dashboard(request.args(0))
    activeDashboard(request.args(0))

    query = (db.item.id > 0)
    query &= (
        auth.accessible_query('collaborator', db.item) |
        auth.accessible_query('owner', db.item))
    query &= db.dashboard.item_list.contains(db.item.unique_id)
    query &= (db.dashboard.id == dash.id)

    grid = SQLFORM.grid(
        query, args=request.args[:1],
        orderby=[~db.item.created_on],
        create=False,
        csv=False,
        paginate=6,
    )

    response.title = dash.name

    return dict(grid=grid, current_dash=dash)


@auth.requires(isOwner())
def load_items():
    """Show the item list of this dashboard"""
    dash = db.dashboard(request.args(0))
    # session.dashboard = dash.id

    request.vars.q = None if request.vars.q == '' else request.vars.q
    if request.vars.q is not None:
        ids = Whoosh().search(request.vars.q)
        query = db.item.id.belongs(ids)
    else:
        query = (db.item.id > 0)

    query &= (
        auth.accessible_query('collaborator', db.item) |
        auth.accessible_query('owner', db.item))
    query &= db.dashboard.item_list.contains(db.item.unique_id)
    query &= (db.dashboard.id == dash.id)

    grid = SQLFORM.grid(
        query, args=request.args[:1],
        orderby=[~db.item.created_on],
        create=False,
        csv=False,
        paginate=6,
    )

    response.title = dash.name
    response.js = "jQuery('#dashboard_cmp').get(0).reload();"

    return dict(grid=grid, current_dash=dash)


@auth.requires(isOwner())
def delete():
    dash = db.dashboard(request.args(0))

    db(db.dashboard.id == dash.id).delete()
    session.dashboard = None

    redirect(URL('default', 'index'))
    return CAT()


@auth.requires_login()
def create():
    fld_name = db.dashboard.name
    fld_name.requires = IS_NOT_EMPTY()
    fld_activate = Field(
        'activate',
        'boolean',
        default=True,
        label=T('Activate?'))

    form = SQLFORM.factory(fld_name, fld_activate)

    if form.process().accepted:
        d_id = db.dashboard.insert(
            name=form.vars.name,
            item_list=[]
        )
        auth.add_permission(0, 'owner', db.dashboard, d_id)
        if form.vars.activate:
            redirect(URL('index', args=[d_id]))
        redirect(URL('index', args=[session.dashboard]))
    return dict(form=form)


@auth.requires(isOwner())
def edit():
    dash = db.dashboard(request.args(0))
    db.dashboard.item_list.readable = False
    db.dashboard.item_list.writable = False

    form = SQLFORM(db.dashboard, record=dash, showid=False)

    if form.process().accepted:
        redirect(URL('index', args=[dash.id]))

    return locals()


@auth.requires(isOwner())
def toogle_pin():
    dash = db.dashboard(request.args(0))
    item = application.getItemByUUID(request.args(1))

    response.js = ""

    if item.unique_id in dash.item_list:
        new_list = dash.item_list
        new_list.remove(item.unique_id)
        if request.vars.remove_item == "True":
            response.js += "$('#item-{}').hide();".format(item.id)

    else:
        new_list = dash.item_list
        new_list.append(item.unique_id)
    dash.update_record(item_list=new_list)

    response.js += "jQuery('#dashboard_cmp').get(0).reload();"

    return CAT('')


@auth.requires_login()
def side_menu():
    query = (db.dashboard.id > 0)
    query &= (db.dashboard.created_by == auth.user.id)
    dash_list = db(query).select(db.dashboard.ALL)

    alinks = request.vars.alinks
    return dict(dash_list=dash_list, alinks=alinks)
