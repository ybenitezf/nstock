# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from gluon import Field, URL, IS_NOT_EMPTY, XML, CAT, I, IS_IMAGE
from plugin_ckeditor import CKEditor


class ContentPicture(ContentPlugin):

    def define_tables(self):
        db = self.db
        T = self.T
        editor = CKEditor(db=db)

        if not hasattr(db, 'plugin_picture_rendition'):
            tbl = db.define_table(
                'plugin_picture_rendition',
                Field(
                    'picture', 'upload', uploadseparate=True, autodelete=True
                ),
                Field('purpose', 'string', length=50, default='raw'),
                Field(
                    'height', 'integer', default=0, readable=False,
                    writable=False
                ),
                Field(
                    'width', 'integer', default=0, readable=False,
                    writable=False
                ),
                Field(
                    'color', 'string', length=20, readable=False,
                    writable=False
                ),
                Field(
                    'format', 'string', length=10, readable=False,
                    writable=False
                )
            )
            tbl.purpose.comment = T('''
            It may contain any value but it is recommended to use one of the
            values: raw, web, thumbnail, print
            ''')
            tbl.purpose.label = T('Purpose')
            tbl.height.label = T('Height')
            tbl.width.label = T('Width')
            tbl.color.label = T('Color space')
            tbl.format.label = T('Format')
            tbl.format.comment = T('Automatic form PIL')
            tbl.picture.label = T('Picture')
            tbl.picture.requires = [IS_IMAGE(), IS_NOT_EMPTY()]

        if not hasattr(db, 'plugin_picture_info'):
            # definimos la BD
            tbl = db.define_table(
                'plugin_picture_info',
                Field('credit_line', 'string', length=250, default=''),
                Field(
                    'description', 'text',
                    label=T('Description'),
                    default=''
                ),
                Field(
                    'caption', 'string',
                    length=250,
                    default=''
                ),
                Field(
                    'thumbnail', 'upload',
                    uploadseparate=True,
                    autodelete=True,
                    default=None
                ),
                Field('renditions', 'list:reference plugin_picture_rendition'),
                Field('item_id', 'reference item'),
                self.auth.signature,
            )
            tbl.credit_line.label = T("Credit line")
            tbl.description.label = T('Description')
            tbl.description.widget = editor.widget
            tbl.caption.label = T("Caption")
            tbl.renditions.label = T("Renditions")
            tbl.item_id.readable = False
            tbl.item_id.writable = False

            # enable record  versioning
            tbl._enable_record_versioning()

    def create_item_url(self):
        return (
            URL('plugin_picture', 'create.html'),
            CAT(I(_class='fa fa-picture-o'), ' ', self.T('Picture'))
        )

    def get_item_url(self, item):
        return URL('plugin_picture', 'index.html', args=[item.id])

    def get_item_icon(self, item):
        return 'fa-picture-o'

    def create_content_translation(self, original_item, target_item):
        """
        Create a duplicate of the content for translation
        """
        db = self.db

        content = db.plugin_picture_info(item_id=original_item.id)
        # duplicate the picture info
        flds = db.plugin_picture_info._filter_fields(content)
        flds['item_id'] = target_item.id
        # remove administrative metadata
        hidde = [
            'created_by', 'created_on', 'modified_on', 'modified_by',
            'is_active']
        for name in hidde:
            del flds[name]

        new_content_id = db.plugin_picture_info.insert(
            **db.plugin_picture_info._filter_fields(flds)
        )

        return new_content_id

    def get_full_text(self, item, CT_REG):
        """Return full text document, mean for plugins"""
        pic_info = self.db.plugin_picture_info(item_id=item.id)
        output = self.response.render(
            'plugin_picture/full_text.txt',
            dict(pic_info=pic_info, item=item, CT_REG=CT_REG))
        return unicode(output.decode('utf-8'))

    def get_changelog_url(self, item):
        return URL('plugin_picture', 'changelog', args=[item.id])

    def preview(self, item):
        info = self.db.plugin_picture_info(item_id=item.id)
        return XML(
            self.response.render(
                'plugin_picture/preview.html',
                dict(item=item, info=info)))
