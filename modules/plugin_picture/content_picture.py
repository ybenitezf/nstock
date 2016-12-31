# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from gluon import URL, XML, CAT, I


class ContentPicture(ContentPlugin):

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
        info = self.db.plugin_picture_info(item_id=item.unique_id)
        return XML(
            self.response.render(
                'plugin_picture/preview.html',
                dict(item=item, info=info)))
