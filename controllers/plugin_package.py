# -*- coding: utf-8 -*-
from perms import isOwnerOrCollaborator

if False:
    from gluon import CAT, SQLFORM, A, SPAN, URL
    from gluon import current, redirect
    request = current.request
    response = current.response
    session = current.session
    T = current.T
    from db import db, auth
    from dc import CT_REG
    from z_whoosh import Whoosh


@auth.requires(isOwnerOrCollaborator())
def index():
    """
    Edit/Show package content
    """
    pkg_item = db.item(request.args(0))
    # content = db.plugin_package_content(item_id=item)

    return locals()


@auth.requires(isOwnerOrCollaborator())
def view_group():
    """
    Show a concrete package group
    """
    pkg_item = db.item(request.args(0))
    pkg_content = db.plugin_package_content(item_id=pkg_item)
    group = db.plugin_package_groups(request.args(1))
    return locals()


@auth.requires(isOwnerOrCollaborator())
def delete_group():
    """Delete a group from the package"""
    item = db.item(request.args(0))
    content = db.plugin_package_content(item_id=item)
    group = db.plugin_package_groups(request.args(1))

    if group.group_items:
        # the group is not empty
        response.flash = T('The group is not empty. Can not be deleted')
    else:
        # the group can be deleted
        # remove the group from package
        content.groups.remove(group.id)
        content.update_record()
        # remove group form database
        del db.plugin_package_groups[group.id]
        response.js = "jQuery('#groups').get(0).reload();"

    return CAT('')


@auth.requires(isOwnerOrCollaborator())
def move_item():
    """Move item between groups"""
    item = db.item(request.args(0))
    pkg_content = db.plugin_package_content(item_id=item.id)
    src = db.plugin_package_groups(request.args(1))
    dst = db.plugin_package_groups(request.args(2))
    g_item = db.item(request.args(3))

    src.group_items.remove(g_item.id)
    dst.group_items.append(g_item.id)
    src.update_record()
    dst.update_record()
    response.js = "jQuery('#groups').get(0).reload();"
    # touch package_content to grap the changes
    pkg_content.dummy_record = (not pkg_content.dummy_record)
    pkg_content.update_record()

    return CAT('')


@auth.requires(isOwnerOrCollaborator())
def create_group_form():
    item = db.item(request.args(0))
    content = db.plugin_package_content(item_id=item)

    db.plugin_package_groups.group_items.default = []
    db.plugin_package_groups.group_items.writable = False
    db.plugin_package_groups.group_items.readable = False
    form = SQLFORM(
        db.plugin_package_groups,
        submit_button=T('Create new group'),
        _class="form-inline"
        )

    if form.process().accepted:
        content.groups.append(form.vars.id)
        content.update_record()
        response.flash = ''
        response.js = '$( "#groups" ).get(0).reload();'

    return locals()


@auth.requires(isOwnerOrCollaborator())
def diff():
    item = db.item(request.args(0))
    content = db.plugin_package_content(item_id=item.id)
    archive = db.plugin_package_content_archive(request.args(1))
    return locals()


@auth.requires(isOwnerOrCollaborator())
def changelog():
    item = db.item(request.args(0))
    pkg_content = db.plugin_package_content(item_id=item.id)
    query = (
        db.plugin_package_content_archive.current_record == pkg_content.id)
    db.plugin_package_content_archive.modified_on.label = T('Date & Time')
    db.plugin_package_content_archive.modified_on.readable = True
    db.plugin_package_content_archive.modified_by.label = T('User')
    db.plugin_package_content_archive.modified_by.readable = True
    fields = [
        db.plugin_package_content_archive.modified_on,
        db.plugin_package_content_archive.modified_by
    ]

    def gen_links(row):
        diff = A(SPAN(
            _class="glyphicon glyphicon-random"),
            _href=URL(
                'diff',
                args=[item.id, row.id]),
            _class="btn btn-default",
            _title=T("Differences"),
        )

        return CAT(diff)

    links = [dict(header='', body=gen_links)]

    changes = SQLFORM.grid(
        query,
        orderby=[~db.plugin_package_content_archive.modified_on],
        fields=fields,
        args=request.args[:1],
        create=False, editable=False, details=False, deletable=False,
        searchable=False,
        csv=False,
        links=links,
    )

    return locals()


@auth.requires(isOwnerOrCollaborator())
def view_package_groups():
    pkg_item = db.item(request.args(0))
    pkg_content = db.plugin_package_content(item_id=pkg_item)
    return locals()


@auth.requires_login()
def create():
    if session.dashboard is None:
        session.flash = T('You must activate some dashboard first')
        redirect(URL('default', 'index'))

    dash = db.dashboard(session.dashboard)
    if not dash.item_list:
        session.flash = T('The current dashboard is empty')
        redirect(URL('default', 'index'))

    # get the headline form the first item in the list
    first_item = db.item(dash.item_list[0])

    fields = []
    # i need the input of the based item fields
    fdl_headline = db.item.headline
    fdl_headline.default = first_item.headline
    fields.append(fdl_headline)
    # fdl_keywords = db.item.keywords
    # keywords_list = []
    # for item_id in dash.item_list:
    #     _item = db.item(item_id)
    #     keywords_list.extend(_item.keywords)
    # keywords_list = list(set(keywords_list))
    # fdl_keywords.default = keywords_list
    # fields.append(fdl_keywords)
    # fields.append(db.item.genre)
    # fields.append(db.item.located)
    fdl_item_type = db.item.item_type
    fdl_item_type.writable = False
    fdl_item_type.readable = False
    fdl_item_type.default = 'package'

    form = SQLFORM.factory(
        *fields,
        table_name='plugin_package_item'  # to allow the correct file name
    )

    if form.process(dbio=False).accepted:
        item_id = CT_REG.package.create_item(form.vars)
        # create the default group
        form.vars.group_role = 'main'
        form.vars.group_items = dash.item_list
        main_g_id = db.plugin_package_groups.insert(
            **db.plugin_package_groups._filter_fields(form.vars)
        )
        # create the package item
        db.plugin_package_content.insert(
            item_id=item_id,
            groups=[main_g_id]
        )
        Whoosh().add_to_index(
            item_id, CT_REG.package.get_full_text(db.item(item_id), CT_REG))
        redirect(URL('default', 'index'))

    return locals()
