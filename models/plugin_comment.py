# -*- coding: utf-8 -*-

"""
Define the tables for the editorials commentary system
"""

def _():
    tbl = db.define_table('plugin_comment_comment',
        Field('body', 'text', label=T('Your comment')),
        Field('item_id', 'reference item'),
        auth.signature,
    )
    tbl.item_id.readable = False
    tbl.item_id.writable = False
    tbl.body.requires = IS_NOT_EMPTY()

    return lambda item_id: LOAD('plugin_comment', 'index.load', args=[item_id], ajax=True)

plugin_comment = _()
