# -*- coding: utf-8 -*-
from content_plugin import ContentPlugin
from gluon import URL, CAT, I, XML

import os


class ContentPackage(ContentPlugin):
    """docstring for ContentPackage."""

    def get_item_url(self, item):
        return URL('plugin_package', 'index.html', args=[item.unique_id])

    def preview(self, item):
        super(ContentPackage, self).preview(item)
        content = self.db.plugin_package_content(item_id=item.unique_id)
        return XML(
            self.response.render(
                'plugin_package/preview.html',
                dict(item=item, p_content=content))
        )


    def get_icon(self):
        return I(_class='fa fa-file-archive-o')


    def get_name(self):
        return self.T('Package')


    def export(self, item, export_dir):
        """
        Export the package and all of his items.
        """
        content = self.db.plugin_package_content(item_id=item.unique_id)
        with open(os.path.join(export_dir, 'package.json'), 'w') as f:
            f.write(content.as_json())

        for item_id in content.item_list:
            item_dir = os.path.join(export_dir, item_id)
            os.mkdir(item_dir)
            self.app.exportItem(item_id, item_dir)

        # done
        return


    def check_create_conditions(self):
        if ((not self.app.session.marked_items) or
            (len(self.app.session.marked_items) == 0)):
            # the are not items marked for package creation
            return (False, dict(
                message=self.T("You need to mark some items first")))

        # build up the suggested values
        keywords = []
        headline = ''
        for item_id in self.app.session.marked_items:
            _item = self.app.getItemByUUID(item_id)
            keywords.extend(_item.keywords)
            if _item.item_type == 'text':
                headline = _item.headline
        keywords = list(set(keywords))  # remove dups
        if headline == '':
            # if there is not a text item in the list, take the headline
            # from the first item
            _item = self.app.getItemByUUID(self.app.session.marked_items[0])
            headline = _item.headline

        return (True, dict(headline=headline, keywords=keywords))


    def create_content(self, item):
        self.db.plugin_package_content.insert(
            item_list=self.app.session.marked_items,
            item_id=item.unique_id
        )
        self.app.session.marked_items = []

    def get_full_text(self, item):
        """Return full text document, mean for plugins"""
        content = self.db.plugin_package_content(item_id=item.unique_id)
        output = self.response.render(
            'plugin_package/full_text.txt',
            dict(item=item, content=content))
        return unicode(output.decode('utf-8'))

    def get_changelog_url(self, item):
        return URL('plugin_package', 'changelog', args=[item.unique_id])

    def shareItem(self, item_id, src_desk, dst_desk):
        """Share package to user"""
        super(ContentPackage, self).shareItem(item_id, src_desk, dst_desk)
        # on packages, we share each item on the package, and then
        # the package it self
        pkg_item = self.app.getItemByUUID(item_id)
        pkg_content = self.db.plugin_package_content(
            item_id=pkg_item.unique_id)
        for c_item in pkg_content.item_list:
            p_c_item = self.app.getItemByUUID(c_item)
            src = self.db.desk(src_desk)
            if p_c_item.id in src.item_list:
                ct = self.app.getContentType(p_c_item.item_type)
                ct.shareItem(c_item, src_desk, dst_desk)
