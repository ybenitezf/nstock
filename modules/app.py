# coding: utf-8
from content_plugin import ContentPlugin
from gluon import current, URL
from gluon.storage import Storage
import perms


class Application(object):

    def __init__(self):
        super(Application, self).__init__()

        # copy current context
        self.db = current.db
        self.T = current.T
        self.auth = current.auth
        self.request = current.request
        self.response = current.response
        self.mail = current.mail
        self.conf = current.conf
        self.registry = Storage()

    def registerContentType(self, item_type, plug):
        """
        Register a ContentPlugin for an Item Type
        """
        assert isinstance(plug, ContentPlugin)

        self.registry[item_type] = plug
        plug.setController(self)

    def getContentType(self, item_type):
        return self.registry[item_type]

    def getItemByUUID(self, unique_id):
        db = self.db
        query = (db.item.unique_id == unique_id)
        item = db(query).select().first()
        return item

    def isOwner(self, unique_id, user=None):
        """
        Returns True if user is the owner of the item
        """
        item = self.getItemByUUID(unique_id)

        if item is None:
            return False

        if user is None:
            return perms.isOwner(item.id)

        return self.auth.has_permission(
            'owner', self.db.item, record_id=item.id, user_id=user.id)

    def isCollaborator(self, unique_id, user=None):
        """
        Returns True if user is a collaborator of the item
        """
        item = self.getItemByUUID(unique_id)

        if item is None:
            return False

        if user is None:
            return perms.isCollaborator(item.id)

        return self.auth.has_permission(
            'collaborator', self.db.item, record_id=item.id, user_id=user.id)

    def isOwnerOrCollaborator(self, unique_id, user=None):
        if unique_id is None:
            return False

        return (
            self.isOwner(unique_id, user=user) or
            self.isCollaborator(unique_id, user=user))

    def createItem(self, content_type, values):
        db = self.db
        auth = self.auth
        values['item_type'] = content_type

        item_id = db.item.insert(**db.item._filter_fields(values))
        # give owner perm to the item
        auth.add_permission(0, 'owner', db.item, item_id)
        return db.item(item_id).unique_id

    def getItemURL(self, unique_id):
        item = self.getItemByUUID(unique_id)
        c = "plugin_{}".format(item.item_type)
        f = "index.html"
        return URL(c=c, f=f, args=[item.unique_id])

    def getContentChangesURL(self, unique_id):
        item = self.getItemByUUID(unique_id)
        c = "plugin_{}".format(item.item_type)
        f = "changelog.html"
        return URL(c=c, f=f, args=[item.unique_id])

    def notifyCollaborators(self, item_id, subject, message):
        pass

    def shareItem(self, item_id, user):
        """
        Share item_id with user
        """
        # 4. - update the item to the Woosh of the user (TODO)
        item = self.getItemByUUID(item_id)
        target_id = self.db.item.insert(**self.db.item._filter_fields(item))
        # give owner to the target user
        g_id = self.auth.user_group(user.id)
        self.auth.add_permission(g_id, 'owner', self.db.item, target_id)
        # give collaborator perms to the current user
        g_id = self.auth.user_group(self.auth.user.id)
        self.auth.add_permission(
            g_id, 'collaborator', self.db.item, target_id
        )
        # disable the old item
        item.update_record(is_active=False)
        # update the archive tables
        self.db(self.db.item_archive.current_record == item.id).update(
            current_record=target_id
        )

        return
