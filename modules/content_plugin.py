# -*- coding: utf-8 -*-
import csv
import os.path
from gluon import IS_IN_SET
from mail import item_notify_users

class ContentPlugin(object):

    def __init__(self, db, T, response, request, auth, mail=None):
        self.T = T
        self.db = db
        self.response = response
        self.request = request
        self.auth = auth
        if not mail:
            from gluon import current
            self.mail = current.mail
        self.define_tables()

    def define_tables(self):
        raise NotImplementedError

    def get_item_url(self, item):
        raise NotImplementedError

    def prepare_language_field(self):
        """
        Add the languages list into db.item.language
        """
        db = self.db
        request = self.request

        f_name = os.path.join(request.folder,
            os.path.join('private', 'language-codes.csv'))
        with open(f_name) as lang_codes:
            reader = csv.DictReader(lang_codes)
            required_names = [(row['alpha2'], row['English']) for row in reader]
            required_names.sort(cmp=lambda x,y: cmp(x[1], y[1]))
            db.item.language_tag.requires = IS_IN_SET(required_names, zero=None)

    def preview(self, item):
        """
        Show the item preview on list's or in packages.
        """
        raise NotImplementedError

    def create_item_url(self):
        """
        Return a tuple in with the first element is the link to create a new
        item of this Content-Type and the second is the text to use as title.
        """
        raise NotImplementedError

    def get_changelog_url(self, item):
        return None

    def is_translation(self, item):
        """
        Check if the current item is a translation of another item
        """

        return self.db.translations(trans_id=item.id)

    def create_translation(self, item, lt):
        db = self.db
        auth = self.auth

        # duplicate item
        flds = db.item._filter_fields(item)
        # assign new language tag
        flds['language_tag'] = lt
        # remove administrative metadata
        hidde = ['created_by', 'created_on', 'modified_on', 'modified_by',
            'is_active']
        for name in hidde:
            del flds[name]
        target_id = db.item.insert(**db.item._filter_fields(flds))
        # assign owner permission to the user creating the translation
        auth.add_permission(0, 'owner', db.item, target_id)
        # if the original work is from a different user assign collaborator
        # perms to the original author
        if auth.user.id != item.created_by:
            g_id = auth.user_group(item.created_by)
            owner  = db.auth_user(item.created_by)
            auth.add_permission(g_id, 'collaborator', db.item, target_id)
            # send an email to the creator of the original item
            subject = self.T("Translation of %s") % (item.headline,)
            context = dict(
                t_item=item,
                t_target=db.item(target_id),
                t_user=auth.user,
            )
            message=self.response.render(
                'translation_email.txt',
                context
            )
            item_notify_users(item.id, subject=subject, message=message)
        # make content translation
        self.create_content_translation(item, db.item(target_id))
        # indicate that the original item has a new translation
        db.translations.insert(
            item_id=item.id,
            trans_id=target_id,
            language_tag=lt
        )

        return target_id

    def create_content_translation(self, original_item, target_item):
        """
        Make a copy of the content from original_item to target_item
        """
        raise NotImplementedError

    def get_item_icon(self, item):
        return 'fa-file-o'

    def create_item(self, values):
        """
        Insert a new item into the db and return the item ID
        """
        db = self.db
        auth = self.auth
        item_id = db.item.insert(**db.item._filter_fields(values))
        # give owner perm to the item
        auth.add_permission(0, 'owner', db.item, item_id)
        return item_id

    def share_item(self, item, user):
        """Share ITEM with USER"""
        db = self.db
        auth = self.auth

        gid = auth.user_group(user.id)
        if not auth.has_permission('owner', db.item, record_id=item.id, user_id=user.id):
            auth.add_permission(gid, 'collaborator', db.item, item.id)
            self.on_share(item, user)

    def prepare_item_for_search(self, item, CT_REG):
        """
        Prepare a text document so the item can be indexed with Woosh
        """
        output = self.response.render(
            "item/full_text.txt",
            dict(item=item, CT_REG=CT_REG)
        )
        return unicode(output.decode('utf-8'))

    def get_full_text(self, item, CT_REG):
        """Return full text document, mean for plugins"""
        raise NotImplementedError

    def on_share(self, item, user):
        """do something when conent is shared with user"""
        pass
