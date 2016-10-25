# -*- coding: utf-8 -*-

@auth.requires( auth.has_permission('owner', db.item, record_id=request.args(0)) or
                auth.has_permission('collaborator', db.item, record_id=request.args(0)))
def index():
    """
    Default view for all items, the item/index view requires a var
    named item, all content types templates must exteds the layout of this view.
    """

    item = db.item(request.args(0))
    # We never will have a pure item, so we redirect to the apropiate C/T
    # plugin
    redirect(CT_REG[item.item_type].get_item_url(item))

    return None

@auth.requires( auth.has_permission('owner', db.item, record_id=request.args(0)) or
                auth.has_permission('collaborator', db.item, record_id=request.args(0)))
def meta():
    """
    Edit/Show item metadata info
    """
    item = db.item(request.args(0))

    if CT_REG[item.item_type].is_translation(item):
        db.item.language_tag.writable = False
        db.item.language_tag.readable = False
    else:
        CT_REG[item.item_type].prepare_language_field()

    form = SQLFORM(db.item, record=item)

    if form.process().accepted:
        session.flash = "Done !"
        # send an email to all the users who has access to this item
        # i need all user who have some permission over current item
        query  = (db.auth_permission.record_id == item.id)
        query &= (db.auth_permission.table_name == db.item)
        query &= (db.auth_permission.group_id == db.auth_membership.group_id)
        query &= (db.auth_user.id == db.auth_membership.user_id)
        query &= (db.auth_user.id != item.created_by)

        collaborators = db(query).select(db.auth_user.ALL, distinct=True)
        for u in collaborators:
            if u != auth.user:
                mail.send(to=[u.email],
                    sender=auth.user.email,
                    subject=T("Changes on %s") % (item.headline,),
                    message=response.render(
                        'changes_email.txt',
                        dict(item=item, user=auth.user, t_user=u)
                    )
                )
        # --
        # with an alert about the new changes
        Whoosh().add_to_index(item.id, CT_REG[item.item_type].get_full_text(db.item(item.id),CT_REG))
        redirect(CT_REG[item.item_type].get_item_url(item))

    return locals()

@auth.requires( auth.has_permission('owner', db.item, record_id=request.args(0)) or
                auth.has_permission('collaborator', db.item, record_id=request.args(0)))
def changelog():
    """
    Show item change log over the time
    """
    item = db.item(request.args(0))

    query = (db.item_archive.current_record == item.id)
    db.item_archive.modified_on.label = T('Date & Time')
    db.item_archive.modified_on.readable = True
    db.item_archive.modified_by.label = T('User')
    db.item_archive.modified_by.readable = True
    fields = [db.item_archive.modified_on,
        db.item_archive.modified_by
    ]

    def gen_links(row):
        diff = A(SPAN(_class="glyphicon glyphicon-random"),
            _href=URL('diff',
                args=[item.id, row.id]),
            _class="btn btn-default",
            _title=T("Differences"),
        )

        return CAT(diff)

    links = [dict(header='', body=gen_links)]

    changes = SQLFORM.grid(query,
        orderby=[~db.item_archive.modified_on],
        fields=fields,
        args=request.args[:1],
        create=False, editable=False, details=False, deletable=False,
        searchable=False,
        csv=False,
        links=links,
    )

    return locals()

@auth.requires( auth.has_permission('owner', db.item, record_id=request.args(0)) or
                auth.has_permission('collaborator', db.item, record_id=request.args(0)))
def diff():
    """
    Show the diff betwen the actual item and the archive one
    """
    item = db.item(request.args(0))
    item_archive = db.item_archive(request.args(1))

    fields = []
    fields_archived = []

    for f in db.item:
        # if values diff
        if item[f.name] != item_archive[f.name]:
            f.comment = None
            fields.append(f)
            db.item_archive[f.name].comment = None
            fields_archived.append(db.item_archive[f.name])

    # build two readonly forms
    form_actual = SQLFORM.factory(*fields,
        record=item,
        readonly=True,
        showid=False,
        formstyle='divs'
        )
    form_archive = SQLFORM.factory(*fields,
        record=item_archive,
        readonly=True,
        showid=False,
        formstyle='divs')

    return locals()

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

@auth.requires( auth.has_permission('owner', db.item, record_id=request.args(0)) or
    auth.has_permission('collaborator', db.item, record_id=request.args(0)))
def translate():
    item = db.item(request.args(0))

    # if CT_REG[item.item_type].is_translation(item):
    #     session.flash = T('This item is a translation of another !')
    #     redirect(URL('index', args=[item.id]))

    # 1.- need a list of all the translations that this item has
    query = (db.translations.item_id == item.id)
    trans = db(query).select(
        db.translations.trans_id,
        db.translations.language_tag
    )
    # 2.- a form with allows creating a new translation
    fld_target = Field('target', 'string', length=2)
    fld_target.label = T('Target language')
    fld_target.comment = T('''
        To create a new translation of the current item select the target
        language.
    ''')
    import os
    import csv
    f_name = os.path.join(request.folder,
        os.path.join('private', 'language-codes.csv'))
    lang_reg = dict()
    with open(f_name) as lang_codes:
        reader = csv.DictReader(lang_codes)
        required_names = list()
        for row in reader:
            query  = (db.translations.item_id == item.id)
            query &= (db.translations.language_tag == row['alpha2'])
            is_translated = db(query).select()
            if item.language_tag != row['alpha2'] and not is_translated:
                required_names.append((row['alpha2'], row['English']))
            lang_reg[row['alpha2']] = row['English']
        required_names.sort(cmp=lambda x,y: cmp(x[1], y[1]))
        fld_target.requires = IS_IN_SET(required_names, zero=None)
    form = SQLFORM.factory(fld_target,
        submit_button=T('Translate this item')
        )

    if form.process().accepted:
        # create a new item/content pair for the language_tag selected
        item_id = CT_REG[item.item_type].create_translation(item, form.vars.target)
        Whoosh().add_to_index(item_id, CT_REG[item.item_type].get_full_text(db.item(item_id),CT_REG))
        redirect(URL('index', args=[item_id]))

    return locals()

@auth.requires( auth.has_permission('owner', db.item, record_id=request.args(0)) or
    auth.has_permission('collaborator', db.item, record_id=request.args(0)))
def share():
    """
    Show the user's who has access to this item
    """
    item = db.item(request.args(0))

    # i need all user who have some permission over current item
    query  = (db.auth_permission.record_id == item.id)
    query &= (db.auth_permission.table_name == db.item)
    query &= (db.auth_permission.group_id == db.auth_membership.group_id)
    query &= (db.auth_user.id == db.auth_membership.user_id)
    query &= (db.auth_user.id != item.created_by)

    rows = db(query).select(db.auth_user.ALL, distinct=True)

    fld_email = Field('email', 'string', default='')
    fld_email.requires = IS_EMAIL()
    form = SQLFORM.factory(fld_email,
        formstyle='bootstrap3_inline',
        submit_button=T("Share this item"),
        table_name='share')
    if form.process().accepted:
        # search a user by his email addr
        u = db.auth_user(email=form.vars.email)
        if u is not None:
            # create new share
            CT_REG[item.item_type].share_item(item, u)
            # send an email to all the users who has access to this item
            for ou in rows:
                if ou != auth.user:
                    mail.send(to=[ou.email],
                        sender=auth.user.email,
                        subject=T("Share of %s") % (item.headline,),
                        message=response.render(
                            'share_email.txt',
                            dict(item=item, user=auth.user, t_user=db.auth_user(email=form.vars.email))
                        )
                    )
        # --
        else:
            # no user with that email
            response.flash = T("The user don't exists on this system")

        response.js = '$( "#{}" ).get(0).reload();'.format(request.cid)

    return locals()

@auth.requires_login()
def all_items():
    """
    Show user items list
    """
    request.vars.q = None if request.vars.q == '' else request.vars.q
    if request.vars.q is not None:
        ids = Whoosh().search(request.vars.q)
        query = db.item.id.belongs(ids)
    else:
        query = (db.item.id > 0)

    query &= (auth.accessible_query('collaborator', db.item) |
        auth.accessible_query('owner', db.item))
    grid = SQLFORM.grid(query,
        orderby=[~db.item.created_on],
        create=False,
        csv=False,
        paginate=6,
    )

    return dict(grid=grid)
