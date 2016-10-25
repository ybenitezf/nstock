# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from gluon import Field, URL, IS_NOT_EMPTY, XML, CAT, I

class ContentPhotoset(ContentPlugin):
    """
    Photo set item
    """

    def define_tables(self):
        db = self.db
        T = self.T

        if not hasattr(db, 'plugin_photoset_photo'):
            db.define_table('plugin_photoset_photo',
                Field('thumbnail', 'upload',
                    uploadseparate=True,
                    autodelete=True,
                    default=None),
                Field('picture', 'upload',
                    uploadseparate=True,
                    autodelete=True),
            )

        if not hasattr(db, 'plugin_photoset_content'):
            tbl = db.define_table('plugin_photoset_content',
                Field('credit_line', 'string', length=250, default=''),
                Field('description', 'text',
                    label=T('Description'),
                    default=''),
                Field('photoset', 'list:reference plugin_photoset_photo'),
                Field('item_id', 'reference item'),
                self.auth.signature,
            )
            tbl.credit_line.label = T("Credit line")
            tbl.description.label = T('Description')
            tbl._enable_record_versioning()

    def create_item_url(self):
        return (URL('plugin_photoset', 'create.html'),
            CAT(I(_class="fa fa-object-group"), ' ', self.T('Photo Set'))
            )

    def get_item_url(self, item):
        return URL('plugin_photoset', 'index.html', args=[item.id])

    def get_item_icon(self, item):
        return 'fa-object-group'

    def create_content_translation(self, original_item, target_item):
        """
        Create a duplicate of the content for translation
        """
        db = self.db

        content = db.plugin_photoset_content(item_id=original_item.id)

        flds = db.plugin_photoset_content._filter_fields(content)
        flds['item_id'] = target_item.id
        # remove administrative metadata
        hidde = ['created_by', 'created_on', 'modified_on', 'modified_by',
            'is_active']
        for name in hidde:
            del flds[name]

        new_content_id = db.plugin_photoset_content.insert(
            **db.plugin_photoset_content._filter_fields(flds)
        )

        return new_content_id

    def get_changelog_url(self, item):
        return URL('plugin_photoset', 'changelog', args=[item.id])

    def get_full_text(self, item, CT_REG):
        """Return full text document, mean for plugins"""
        photoset_content = self.db.plugin_photoset_content(item_id=item.id)
        output = self.response.render('plugin_photoset/full_text.txt',
            dict(photoset_content=photoset_content, item=item, CT_REG=CT_REG))
        return unicode( output.decode( 'utf-8' ) )

    def preview(self, item):
        photoset_content = self.db.plugin_photoset_content(item_id=item.id)
        return XML(self.response.render('plugin_photoset/preview.html',
            dict(item=item, photoset_content=photoset_content)))
