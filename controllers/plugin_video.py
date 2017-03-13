# -*- coding: utf-8 -*-


@auth.requires(lambda: application.canUpdateItem(request.args(0)))
def index():
    item = application.getItemByUUID(request.args(0))
    content = db.plugin_video_content(item_id=item.id)

    return locals()


@auth.requires(lambda: application.canUpdateItem(request.args(0)))
def renditions():
    item = application.getItemByUUID(request.args(0))
    content = db.plugin_video_content(item_id=item.unique_id)

    return locals()


@auth.requires(lambda: application.canUpdateItem(request.args(0)))
def del_redition():
    item = application.getItemByUUID(request.args(0))
    content = db.plugin_video_content(item_id=item.unique_id)

    rendition = db.plugin_video_rendition(request.args(1))
    if rendition:
        content.renditions.remove(rendition.id)
        content.update_record()
        del db.plugin_video_rendition[rendition.id]

    return locals()


@auth.requires(lambda: application.canReadItem(request.args(0)))
def changelog():
    """
    Show item change log over the time
    """
    item = application.getItemByUUID(request.args(0))
    if item is None:
        raise HTTP(404)
    content = db.plugin_video_content(item_id=item.unique_id)

    query = (db.plugin_video_content_archive.current_record == content.id)
    db.plugin_video_content_archive.modified_on.label = T('Date & Time')
    db.plugin_video_content_archive.modified_on.readable = True
    db.plugin_video_content_archive.modified_by.label = T('User')
    db.plugin_video_content_archive.modified_by.readable = True
    fields = [
        db.plugin_video_content_archive.modified_on,
        db.plugin_video_content_archive.modified_by
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
        orderby=[~db.plugin_video_content_archive.modified_on],
        fields=fields,
        args=request.args[:1],
        create=False, editable=False, details=False, deletable=False,
        searchable=False,
        csv=False,
        links=links,
    )

    return locals()


@auth.requires(lambda: application.canReadItem(request.args(0)))
def diff():
    item = application.getItemByUUID(request.args(0))
    if item is None:
        raise HTTP(404)
    content = db.plugin_video_content(item_id=item.unique_id)
    archive = db.plugin_video_content_archive(request.args(1))

    fields = []
    fields_archived = []
    fields_names = []

    for f in db.plugin_video_content:
        # if values diff
        if content[f.name] != archive[f.name]:
            fields_names.append(f.name)
            f.comment = None
            fields.append(f)
            db.plugin_video_content_archive[f.name].comment = None
            fields_archived.append(db.plugin_video_content_archive[f.name])

    # build two readonly forms
    form_actual = SQLFORM.factory(
        *fields,
        record=content,
        readonly=True,
        showid=False,
        formstyle='divs'
        )
    form_archive = SQLFORM.factory(
        *fields,
        record=archive,
        readonly=True,
        showid=False,
        formstyle='divs')

    return locals()


@auth.requires(lambda: application.canUpdateItem(request.args(0)))
def add_rendition():
    item = application.getItemByUUID(request.args(0))
    content = db.plugin_video_content(item_id=item.unique_id)

    form = SQLFORM(
        db.plugin_video_rendition,
        submit_button=T("Upload"))

    if form.process().accepted:
        content.renditions.append(form.vars.id)
        content.update_record()
        redirect(URL('index', args=[item.unique_id]))

    return locals()


@auth.requires(lambda: application.canUpdateItem(request.args(0)))
def edit_content():
    item = application.getItemByUUID(request.args(0))
    content = db.plugin_video_content(item_id=item.unique_id)

    form = SQLFORM(
        db.plugin_video_content,
        record=content,
        showid=False,
        submit_button=T('Save')
    )

    if form.process().accepted:
        application.notifyChanges(item.unique_id)
        application.indexItem(item.unique_id)
        response.flash = T('Saved')

    return form
