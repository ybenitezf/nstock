# coding: utf-8
from content_plugin import ContentPlugin
from z_whoosh import Whoosh
from gluon import current, URL
from gluon.storage import Storage
from gluon.cache import Cache
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
        self.cache = Cache(self.request)

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

    def indexItem(self, item_id, user=None):
        """
        Add/update item to the user search index
        """
        if user is None:
            user = self.auth.user
        item = self.getItemByUUID(item_id)
        ct = self.getContentType(item.item_type)
        text = ct.get_full_text(item)
        w = Whoosh(str(user.id))
        w.add_to_index(unicode(item_id), text)

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

    def notifyChanges(self, item_id):
        response = self.response
        auth = self.auth
        T = self.T
        item = self.getItemByUUID(item_id)

        message = response.render(
            'changes_email.txt',
            dict(item=item, user=auth.user)
        )
        subject = T("Changes on %s") % (item.headline,)

        self.notifyCollaborators(
            item.unique_id,
            subject,
            message
        )

    def getCollaborators(self, item_id, exclude_current=True):
        """
        Given a item returns the list of user who have access to item.
        """
        db = self.db
        auth = self.auth
        item = self.getItemByUUID(item_id)

        query = (db.auth_permission.record_id == item.id)
        query &= (db.auth_permission.table_name == db.item)
        query &= (db.auth_permission.group_id == db.auth_membership.group_id)
        query &= (db.auth_user.id == db.auth_membership.user_id)
        if exclude_current:
            query &= (db.auth_user.id != auth.user.id)
        return db(query).select(
            db.auth_user.ALL,
            distinct=True,
            cache=(self.cache.ram, 30),
            cacheable=True)

    def notifyCollaborators(self, item_id, subject, message):
        db = self.db
        auth = self.auth
        item = self.getItemByUUID(item_id)

        myusers = self.getCollaborators(item.unique_id)
        for u in myusers:
            db.notification.insert(
                subject=subject,
                message_content=message,
                from_user=auth.user.id,
                to_user=u.id
            )

    def shareItem(self, item_id, user, perms='collaborator'):
        """
        Share item_id with user
        """
        if user.id != self.auth.user.id:
            item = self.getItemByUUID(item_id)
            if perms == 'collaborator':
                g_id = self.auth.user_group(user.id)
                self.auth.add_permission(
                    g_id, 'collaborator', self.db.item, item.id)
                self.indexItem(item.unique_id, user)
            else:
                # give owner to the target user
                g_id = self.auth.user_group(user.id)
                self.auth.add_permission(g_id, 'owner', self.db.item, item.id)
                # give collaborator perms to the current user
                g_id = self.auth.user_group(self.auth.user.id)
                self.auth.add_permission(
                    g_id, 'collaborator', self.db.item, item.id)
                # remove the owner perm from original user.
                self.auth.del_permission(
                    g_id, 'owner', self.db.item, item.id)
                # add to the index of the user
                self.indexItem(item.unique_id, user)

        return
