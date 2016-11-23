# -*- coding: utf-8 -*-

from plugin_package.content_package import ContentPackage

if False:
    from gluon import current
    response = current.response
    request = current.request
    T = current.T
    from db import db, auth
    from dc import CT_REG

CT_REG.package = ContentPackage(db, T, response, request, auth)
