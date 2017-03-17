# -*- coding: utf-8 -*-

from plugin_package.content_package import ContentPackage
from gluon.tools import PluginManager
from plugin_ckeditor import CKEditor

if False:
    from gluon import current
    from gluon import Field
    response = current.response
    request = current.request
    T = current.T
    from db import db, auth


def _():
    plugins = PluginManager('package', app=None)
    if plugins.package.app is not None:
        # this will register the the application on content/type
        plugins.package.app.registerContentType('package', ContentPackage())

        if not hasattr(db, 'plugin_package_content'):
            editor = CKEditor(db=db)
            tbl = db.define_table(
                'plugin_package_content',
                Field('item_list', 'list:string'),
                Field('description', 'text'),
                Field('item_id', 'string', length=64),
                auth.signature,
            )
            tbl.item_id.writable = False
            tbl.item_id.readable = False
            tbl.item_list.writable = False
            tbl.item_list.readable = False
            tbl.description.label = T('Description')
            tbl.description.widget = editor.widget
            tbl._enable_record_versioning()

            # add a callback to the item table for updating the item list of
            # the package on item deletion.
            def plugin_package_callback(s):
                item = s.select().first()
                # this are the packages with contains the item to delete
                pkgs = db(
                    db.plugin_package_content.item_list.contains(
                        item.unique_id)
                ).select()
                for pkg in pkgs:
                    # remove the item from the package
                    pkg.item_list.remove(item.unique_id)
                    pkg.update_record()

                return False
            db.item._before_delete.insert(0, plugin_package_callback)

_()
