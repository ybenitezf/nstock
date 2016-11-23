# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from gluon import Field, URL, CAT, I, SPAN, XML

class ContentPackage(ContentPlugin):
    """docstring for ContentPackage."""

    def define_tables(self):
        db = self.db
        T = self.T

        if not hasattr(db, 'plugin_package_groups'):
            tbl = db.define_table('plugin_package_groups',
                Field('group_role', 'string', length=30, default='main'),
                Field('group_items', 'list:reference item')
            )
            tbl.group_role.label = T('Role')
            tbl.group_role.comment = T("""
            Declare the group role within the package structure.
            Contain values representing “main”, “sidebar” or other editorial
            terms that express how the content in the package is intended to be
            used.
            """)

        if not hasattr(db, 'plugin_package_content'):
            tbl = db.define_table('plugin_package_content',
                Field('groups', 'list:reference plugin_package_groups'),
                Field('dummy_record', 'boolean', default=True),
                Field('item_id', 'reference item'),
                self.auth.signature,
            )
            tbl.item_id.writable = False
            tbl.item_id.readable = False
            tbl.groups.writable = False
            tbl.groups.readable = False
            tbl.dummy_record.writable = False
            tbl.dummy_record.readable = False
            tbl._enable_record_versioning()

    def get_item_url(self, item):
        return URL('plugin_package', 'index.html', args=[item.id])

    def preview(self, item):
        content = self.db.plugin_package_content(item_id=item.id)
        return XML(self.response.render('plugin_package/preview.html',
            dict(item=item,p_content=content)))

    def create_item_url(self):
        title = CAT(self.T('Package'), ' ',
            SPAN(self.T('from current dashboard'), _class="small")
            )
        return (URL('plugin_package', 'create.html'),
            CAT(I(_class='fa fa-file-archive-o'), ' ', self.T('Package'))
            )

    def get_full_text(self, item, CT_REG):
        """Return full text document, mean for plugins"""
        output = self.response.render('plugin_package/full_text.txt',
            dict(item=item, CT_REG=CT_REG))
        return unicode( output.decode( 'utf-8' ) )


    def get_changelog_url(self, item):
        return URL('plugin_package', 'changelog', args=[item.id])

    def create_content_translation(self, original_item, target_item):
        db = self.db
        original_content = db.plugin_package_content(item_id=original_item.id)

        # create a new groups container for the target_item
        new_content_id = db.plugin_package_content.insert(
            groups=[],
            item_id=target_item.id
        )
        new_content = db.plugin_package_content(new_content_id)
        new_groups = []
        # duplicate the groups from original_item
        for grp in original_content.groups:
            src_group = db.plugin_package_groups(grp)
            dst_group_id = db.plugin_package_groups.insert(
                group_role=src_group.group_role,
                group_items=src_group.group_items
            )
            new_groups.append(dst_group_id)
        new_content.update_record(groups=new_groups)

    def on_share(self, item, user):
        """Share all the item in the package with the target user"""
        db = self.db

        if item.item_type == 'package':
            pkg_content = db.plugin_package_content(item_id=item.id)
            for g_id in pkg_content.groups:
                group = db.plugin_package_groups(g_id)
                for item_id in group.group_items:
                    self.share_item(db.item(item_id), user)

    def get_item_icon(self, item):
        return 'fa-file-archive-o'
