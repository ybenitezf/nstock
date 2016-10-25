# -*- coding: utf-8 -*-
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
