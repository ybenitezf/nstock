# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from gluon import URL, XML, CAT, I
import os.path

class ContentText(ContentPlugin):

    def get_icon(self):
        return I(_class="fa fa-file-text-o")


    def get_name(self):
        return self.T('Text')


    def create_content(self, item):
        self.db.plugin_text_text.insert(
            byline="{} {}".format(
                self.auth.user.first_name,
                self.auth.user.last_name
            ),
            item_id=item.unique_id
        )

    def export(self, item, export_dir):
        content = self.db.plugin_text_text(item_id=item.unique_id)
        with open(os.path.join(export_dir, 'text.json'), 'w') as f:
            f.write(content.as_json())

        return


    def get_item_url(self, item):
        return URL('plugin_text', 'index.html', args=[item.unique_id])

    def get_changelog_url(self, item):
        return URL('plugin_text', 'changelog', args=[item.unique_id])

    def get_full_text(self, item):
        """Return full text document, mean for plugins"""
        text_content = self.db.plugin_text_text(item_id=item.unique_id)
        output = self.response.render(
            'plugin_text/full_text.txt',
            dict(text_content=text_content, item=item))
        return unicode(output.decode('utf-8'))

    def preview(self, item):
        super(ContentText, self).preview(item)
        content = self.db.plugin_text_text(item_id=item.unique_id)
        return XML(self.response.render(
            'plugin_text/preview.html',
            dict(item=item, p_content=content)))
