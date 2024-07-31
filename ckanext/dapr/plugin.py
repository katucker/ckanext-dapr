# -*- coding: utf-8 -*-
import logging

from builtins import str, range

import ckan.lib.helpers as h
import ckan.plugins as p
from ckan.plugins.toolkit import asbool, config, get_validator, url_for, redirect_to, render, get_action

from ckan.exceptions import CkanVersionException

from flask import Blueprint

DEFAULT_API_URL = "https://api.gsa.gov/analytics/dap/v2.0.0/"
DEFAULT_BATCH_SIZE = 2000
MAX_BATCH_SIZE = 10000

log = logging.getLogger(__name__)

def show_top_packages():
    redirect_to(url_for('.top'))

def get_package_url_title(id):
    res = (None, None)
    pf = get_action('package_search')
    response = pf({'q':f'id:{id}', 'rows':1, 'fl':['url','title']})
    if response.get('count', 0) > 0:
        r = response['results'][0]
        res = r.get('url', None), r.get('title', None)
    else:
        log.error('Could not retrieve URL and title for package %s', id)

    return res

def show_top_datasets():
    '''Retrieve a list of datasets that have the highest number of accesses.
    Display the retrieved list in a returned page.
    '''
    render_data = []
    datasets = daputil.top_packages()
    for dataset in datasets:
        url,title = get_package_url_title(dataset.package_id)
        render_data.append({'url': url, 'title': title})
    render("top.html", data=render_data)

class daprPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IBlueprint, inherit=True)
    p.implements(p.ITemplateHelpers)

    def configure(self, config):
        """Load config settings for this extension from config file.

        See IConfigurable.

        """
        self.retrieval_agency = config.get("ckanext.dapr.retrieval_agency", None)

        self.keyfile = config.get("ckanext.dapr.keyfile", None)
        self.show_downloads = asbool(config.get("ckanext.dapr.show_downloads", True))
        self.api_url = config.get("ckanext.dapr.api_url", DEFAULT_API_URL)
        self.batch_size - config.get("ckanext.dapr.batch_size", DEFAULT_BATCH_SIZE)

        p.toolkit.add_resource("../assets", "ckanext-dap")

    def update_config(self, config):
        """Change the CKAN environment configuration.

        See IConfigurer.

        """
        p.toolkit.add_template_directory(config, "../templates")

    def update_config_schema(self, schema):
        """Add runtime-editable configuration parameters.

        See IConfigurer.

        """
        im = get_validator('ignore_missing')
        pi = get_validator('positive_integer')

        schema.update({
            "ckanext.dapr.retrieval_agency": [im],
            "ckanext.dapr.show_downloads": [im],
            "ckanext.dapr.api_url": [im],
            "ckanext.dapr.batch_size": [im, pi, get_validator('limit_to_configured_maximum')(MAX_BATCH_SIZE)]
        })

        return schema

    def get_blueprint(self):
        """Add new routes that this extension's controllers handle.

        See IBlueprint.

        """
        blueprint = Blueprint("dap_analytics", self.__module__)
        blueprint.template_folder = "templates"
        blueprint.add_url_rule("/analytics/package/top", "packages_top", view_func=show_top_packages)
        blueprint.add_url_rule("analytics/dataset/top", "top", view_func=show_top_datasets)
        return blueprint
