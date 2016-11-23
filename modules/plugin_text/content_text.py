# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from gluon import Field, URL, IS_NOT_EMPTY, XML, CAT, I
from plugin_ckeditor import CKEditor


class ContentText(ContentPlugin):

    def define_tables(self):
        db = self.db

        if not hasattr(db, 'plugin_text_text'):
            # configure ckeditor
            editor = CKEditor(db=db)
            # definimos la BD
            tbl = db.define_table(
                'plugin_text_text',
                Field('byline', 'string', length=250, default=''),
                Field('body', 'text', label=self.T('Content')),
                Field('item_id', 'reference item'),
                self.auth.signature,
            )
            tbl.item_id.readable = False
            tbl.item_id.writable = False
            tbl.body.requires = IS_NOT_EMPTY()
            tbl.body.widget = editor.widget

            # enable record  versioning
            tbl._enable_record_versioning()

    def create_item_url(self):
        return (
            URL('plugin_text', 'create.html'),
            CAT(I(_class="fa fa-file-text-o"), ' ', self.T('Text')))

    def get_item_url(self, item):
        return URL('plugin_text', 'index.html', args=[item.id])

    def get_item_icon(self, item):
        return 'fa-file-text-o'

    def create_content_translation(self, original_item, target_item):
        """
        Create a duplicate of the content for translation
        """
        db = self.db
        content = db.plugin_text_text(item_id=original_item.id)

        # duplicate item
        flds = db.plugin_text_text._filter_fields(content)
        flds['item_id'] = target_item.id
        # remove administrative metadata
        hidde = [
            'created_by', 'created_on', 'modified_on', 'modified_by',
            'is_active']
        for name in hidde:
            del flds[name]

        content_id = db.plugin_text_text.insert(
            **db.plugin_text_text._filter_fields(flds)
        )

        return content_id

    def get_changelog_url(self, item):
        return URL('plugin_text', 'changelog', args=[item.id])

    def get_full_text(self, item, CT_REG):
        """Return full text document, mean for plugins"""
        text_content = self.db.plugin_text_text(item_id=item.id)
        output = self.response.render(
            'plugin_text/full_text.txt',
            dict(text_content=text_content, item=item, CT_REG=CT_REG))
        return unicode(output.decode('utf-8'))

    def preview(self, item):
        content = self.db.plugin_text_text(item_id=item.id)
        return XML(self.response.render(
            'plugin_text/preview.html',
            dict(item=item, p_content=content)))
