# -*- coding: utf-8 -*-
if False:
    from gluon import current
    response = current.response
    request = current.request
    T = current.T
    from dc import CT_REG
    from db import auth


def _():
    # add items menu
    create_items = []
    for ct in CT_REG:
        url, title = CT_REG[ct].create_item_url()
        create_items.append(
            (title, False, url, [])
        )
    response.menu += [(T('Create Items'), False, "#", create_items)]

if auth.user:
    _()
