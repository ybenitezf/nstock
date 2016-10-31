# -*- coding: utf-8 -*-

from plugin_text.content_text import ContentText

if False:
    from gluon import current
    response = current.response
    request = current.request
    T = current.T
    from db import db, auth
    from dc import CT_REG


CT_REG.text = ContentText(db, T, response, request, auth)
