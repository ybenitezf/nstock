# -*- coding: utf-8 -*-
from gluon import I

class ContentPlugin(object):

    def __init__(self):
        super(ContentPlugin, self).__init__()
        self.configured = False

    def setController(self, app):
        self.app = app
        self.T = app.T
        self.db = app.db
        self.response = app.response
        self.request = app.request
        self.auth = app.auth
        self.mail = app.mail
        self.configured = True


    def get_item_url(self, item):
        raise NotImplementedError


    def create_content(self, item):
        raise NotImplementedError


    def get_icon(self):
        return I(_class="fa fa-file")

    def get_name(self):
        return self.T("Some Content-Type")


    def preview(self, item):
        """
        Show the item preview on list's or in packages.
        """
        return ''


    def get_changelog_url(self, item):
        return None

    def get_full_text(self, item):
        """Return full text document, mean for plugins"""
        raise NotImplementedError

    def shareItem(self, item_id, src_desk, dst_desk):
        """Share item with user, given the perms"""
        self.app.shareItem(item_id, src_desk, dst_desk)
        # some content plugins may whant to do some stuff before or after
        # sharing an item. For example package-type items. Remember call
        # super.
