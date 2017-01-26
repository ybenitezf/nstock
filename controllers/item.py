# -*- coding: utf-8 -*-
from z_whoosh import Whoosh
if False:
    from gluon import redirect, current, Field, HTTP
    from gluon import A, CAT, SPAN, SQLFORM, URL, IS_IN_SET
    from gluon import IS_EMAIL
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T
    # from db import auth, db, mail
    from db import auth, db
    from dc import application
    # from menu import *


@auth.requires(application.isOwnerOrCollaborator(request.args(0)))
def index():
    """
    Default view for all items, the item/index view requires a var
    named item, all content types templates must exteds the layout of this view
    """

    # We never will have a pure item, so we redirect to the apropiate C/T
    # plugin
    redirect(application.getItemURL(request.args(0)))

    return None


@auth.requires(application.isOwner(request.args(0)))
def meta():
    """
    Edit/Show item metadata info
    """
    item = application.getItemByUUID(request.args(0))

    if item is None:
        raise HTTP(404)

    contentType = application.getContentType(item.item_type)
    l_names = [
        (r.language_tag, r.english_name) for r in db(
            db.languages.id > 0
        ).select(orderby=db.languages.english_name)
    ]
    db.item.language_tag.requires = IS_IN_SET(
        l_names,
        zero=None
    )

    # issue #5 hidde some fields from metadata
    db.item.provider.readable = False
    db.item.provider.writable = False
    db.item.provider_service.readable = False
    db.item.provider_service.writable = False
    db.item.copyright_holder.readable = False
    db.item.copyright_holder.writable = False
    db.item.copyright_url.readable = False
    db.item.copyright_url.writable = False
    db.item.copyright_notice.readable = False
    db.item.copyright_notice.writable = False
    db.item.pubstatus.readable = False
    db.item.pubstatus.writable = False

    form = SQLFORM(db.item, record=item)

    if form.process().accepted:
        # session.flash = "Done !"
        # send an email to all the users who has access to this item
        application.notifyChanges(item.unique_id)
        application.indexItem(item.unique_id)
        if request.ajax:
            response.js = "$('#metaModal').modal('hide');"
        else:
            redirect(application.getItemURL(item.unique_id))

    return locals()


@auth.requires(application.isOwnerOrCollaborator(request.args(0)))
def changelog():
    """
    Show item change log over the time
    """
    item = application.getItemByUUID(request.args(0))
    if item is None:
        raise HTTP(404)

    query = (db.item_archive.current_record == item.id)
    db.item_archive.modified_on.label = T('Date & Time')
    db.item_archive.modified_on.readable = True
    db.item_archive.modified_by.label = T('User')
    db.item_archive.modified_by.readable = True
    fields = [
        db.item_archive.modified_on,
        db.item_archive.modified_by
    ]

    def gen_links(row):
        diff = A(
            SPAN(_class="glyphicon glyphicon-random"),
            _href=URL(
                'diff',
                args=[item.unique_id, row.id]),
            _class="btn btn-default",
            _title=T("Differences"),
        )

        return CAT(diff)

    links = [dict(header='', body=gen_links)]

    changes = SQLFORM.grid(
        query,
        orderby=[~db.item_archive.modified_on],
        fields=fields,
        args=request.args[:1],
        create=False, editable=False, details=False, deletable=False,
        searchable=False,
        csv=False,
        links=links,
    )

    return dict(item=item, changes=changes)


@auth.requires(application.isOwnerOrCollaborator(request.args(0)))
def diff():
    """
    Show the diff betwen the actual item and the archive one
    """
    item = application.getItemByUUID(request.args(0))
    if item is None:
        raise HTTP(404)
    item_archive = db.item_archive(request.args(1))
    if item_archive is None:
        raise HTTP(503)

    fields = []
    fields_archived = []

    # allow view of administrative metadata
    db.item.modified_by.readable = True
    db.item.modified_on.readable = True
    db.item_archive.modified_by.readable = True
    db.item_archive.modified_on.readable = True

    for f in db.item:
        if item[f.name] != item_archive[f.name]:
            f.comment = None
            fields.append(f)
            db.item_archive[f.name].comment = None
            fields_archived.append(db.item_archive[f.name])

    # build two readonly forms
    form_actual = SQLFORM.factory(
        *fields,
        record=item,
        readonly=True,
        showid=False,
        formstyle='divs'
        )
    form_archive = SQLFORM.factory(
        *fields_archived,
        record=item_archive,
        readonly=True,
        showid=False,
        formstyle='divs')

    return dict(item=item, form_actual=form_actual, form_archive=form_archive)


@auth.requires_login()
def add_items():
    return dict()


@auth.requires_permission('owner', db.item, record_id=request.args(0))
def unshare():
    item = db.item(request.args(0))
    gid = int(request.args(1))

    auth.del_permission(gid, 'collaborator', db.item, item.id)

    response.js = '$( "#{}" ).get(0).reload();'.format(request.cid)
    return CAT('')


@auth.requires(application.isOwner(request.args(0)))
def share():
    """
    Show the user's who has access to this item
    """
    item = application.getItemByUUID(request.args(0))
    if item is None:
        raise HTTP(404)

    fld_email = Field('email', 'string', default='')
    fld_email.requires = IS_EMAIL()
    form = SQLFORM.factory(
        fld_email,
        formstyle='bootstrap3_inline',
        submit_button=T("Share this item"),
        table_name='share')
    if form.process().accepted:
        # search a user by his email addr
        u = db.auth_user(email=form.vars.email)
        if u is not None:
            # create new share
            subject = T("Share of %s", (item.headline,))
            message = response.render(
                'share_email.txt',
                dict(
                    item=item,
                    user=auth.user,
                    t_user=db.auth_user(email=form.vars.email)
                )
            )
            application.notifyCollaborators(
                item.unique_id,
                subject,
                message
            )
            application.shareItem(item.unique_id, u)
            # --
            # close the dialog
            response.js = "$('#metaModal').modal('hide');"
        else:
            # no user with that email
            response.flash = T("The user don't exists on this system")
            form.errors.email = T("The user don't exists on this system")

    return locals()


@auth.requires_login()
def all_items():
    """
    Show user items list
    """
    if type(request.vars.q) is list:
        # in the case of being loaded from a query string
        # use only the last valor from q
        request.vars.q = request.vars.q[-1]
    request.vars.q = None if request.vars.q == '' else request.vars.q
    if request.vars.q is not None:
        ids = Whoosh().search(request.vars.q)
        query = db.item.unique_id.belongs(ids)
    else:
        query = (db.item.id > 0)

    query &= (
        auth.accessible_query('collaborator', db.item) |
        auth.accessible_query('owner', db.item))

    grid = SQLFORM.grid(
        query,
        orderby=[~db.item.created_on],
        create=False,
        csv=False,
        paginate=6,
    )

    return dict(grid=grid)
