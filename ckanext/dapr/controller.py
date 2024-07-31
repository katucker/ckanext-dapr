from __future__ import absolute_import
from builtins import str
import logging
from ckan.lib.base import BaseController, c, render, request
from . import daputil

import ckan.logic as logic
import hashlib
from . import plugin
from ckan.plugins.toolkit import config

from paste.util.multidict import MultiDict

from ckan.controllers.api import ApiController

log = logging.getLogger("ckanext.dap")


class DAPAnalyticsController(BaseController):
    def view(self):
        # get package objects corresponding to popular content
        c.top_resources = dbutil.top_resources(limit=10)
        return render("summary.html")


