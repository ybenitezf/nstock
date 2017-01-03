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
