# -*- coding: utf-8 -*-
if False:
    from gluon import current
    response = current.response
    request = current.request
    T = current.T
    from dc import application
    from db import auth


def _():
    # add items menu
    create_items = []
    registry = application.registry
    for content_type in registry:
        icon = registry[content_type].get_icon()
        name = registry[content_type].get_name()
        url = URL('item', 'create.html', args=[content_type])
        create_items.append(
            (CAT(icon, ' ', name), False, url, [])
        )
    response.menu += [(T('Add Items'), False, "#", create_items)]

if auth.user:
    _()
