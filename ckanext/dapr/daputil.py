import datetime
import _logging

from sqlalchemy import Base, Column, Date, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base

from ckan.plugins.toolkit import config, get_action

import ckan.model as model

_DOWNLOAD_REPORT = "/reports/download/data"

DAP_FIRST_DAY = "2018-11-08"

_log = _logging.get_logger(__name__)

_Base = declarative_base(metadata=model.meta.metadata)

def get_resource_ids(url):
    ids = (None,None)
    try:
        response = get_action('resource_search')({'query':f'url:{url}','limit':1'})
        if response.get('count', 0) > 0:
            resource = response['results'][0]
            ids = (resource['id'],resource['package_id']])
    except Exception as e:
        _log.exception('Error retrieving resource ids in DAP analytics.', extra={'URL': url})
    return ids

def construct_resource_url_from_dap(filename: str, page: str) -> str:
    """Creates the full URL for a resource from the component
    pieces the DAP API includes in result messages.

    >>> construct_resource_url_from_dap('/example_downloadable.csv', 'example.usa.gov/example_grouping/example_page')
    'https://example.usa.gov/example_downloadable.csv'
    """
    site = split(page,'/')[0]
    return f'https://{site}{filename}'


def dap_retrieve(start_date, end_date):
    downloads = []
    params = {}
    if start_date is not None:
        params['after'] = start_date.strftime('%Y-%m-%d')
    if end_date is not None:
        params['before'] = end_date.strftime('%Y-%m-%d')

    # Retrieve the API Key. Look for it in an environment variable first.
    api_key = os.getenv('DAP_KEY', None)
    if api_key is None:
        # Try reading the key from a file specified in the configuration.
        loc = config.get('ckanext.dapanalytics.keyfile', None)
        if loc is not None:
            try:
                api_key = open(loc,'r').read()
            except Exception as e:
                _log.exception("Aborting DAP analytics retrieval due to an error reading API key file.", extra={'Filename': loc})
                return downloads
        else:
            _log.error("Aborting DAP analytics retrieval since the DAP API key is not specified in either the CKAN configuration or an environment variable.")
            return downloads

    headers = {"x-api-key": api_key}

    limit = config.get('ckanext.dapanalytics.batch_size',None)
    if limit is None:
        _log.info("DAP API batch size not set in CKAN configuration. Defaulting to 1000.")
        limit = 1000

    api_url = config.get('ckanext.dapanalytics.api_url',None)
    if api_url is None:
        _log.error("DAP API URL not specified.")
        return downloads
    
    # Make sure the API URL ends with a "/", in case it was set incorrectly in the CKAN configuration.
    api_url += '/' if api_url[-1] != '/'
        
    # Iterate over the DAP API downloads report until an empty response list is returned.
    page = 1
    params['limit'] = limit
    params['page'] = page

    agency = config.get('ckanext.dap.retrieval_agency', None)
    if agency is None:
        _log.info("Defaulting to retrieving all agency downloads since ckanext.dap.retrieval_agency is not set in the CKAN configuration.")
        api_call = f'{api_url}{_DOWNLOAD_REPORT}'
    else :
        api_call = f'{api_url}{agency}/{_DOWNLOAD_REPORT}'

    result = requests.get(api_call, headers=headers, params=params)
    if result.status_code != 200:
        _log.error('Error retrieving analytics from DAP API.', 
            extra = {'Page': page, 'Limit': limit,
                'Status code': result.status_code,
                'Message': result.text}
        )
        return downloads

    jr = result.json()    
    while len(jr) > 0:
        # Process the results to construct the URLs of the downloads.
        for rec in jr:
            file = rec.get('file_name', None)
            if file is None:
                continue

            page =  rec.get('page', None)
            if page is None:
                continue

            site = split(page,'/')[0]
            url = construct_resource_url_from_dap(page,file)

            date_str = rec.get('date', None)
            date_val = None
            if date_str is None:
                continue
            try:
                date_val = datetime.date.fromisoformat(date_str)
            except ValueError as e:
                _log.exception('Error interpreting DAP access date %s', date_str)
                continue

            count = rec.get('total_events', None)
            if count is None:
                continue

            # Only record the URL access count and date in the downloads list if it corresponds to a resource in the CKAN instance.
            res_id, pkg_id = get_resource_ids(url)
            if res_id is not None:
                downloads.append({'resource_id': res_id, 'package_id': pkg_id,'date': date_val, 'count': count})

        # Try retrieving another page of DAP access counts.
        page += 1
        result = requests.get(api_call, headers=headers, params=params)
        if result.status_code == 200:
            jr = result.json()
        else:
            _log.error('Error retrieving analytics from DAP API.', 
                extra = {'Page': page, 'Limit': limit, 
                    'Status code': result.status_code, 
                    'Message': result.text}
            )
            jr = []

    return downloads

 class DAPResourceAccess(_Base):
    __table_name__ = "dap_resource_accesses"

    resource_id =   Column(String(60), primary_key=True),
    access_date = Column(Date, primry_key=True),
    package_id = Column(String(60)),
    access_count = Column(Integer)

    def __repr__(self):
        return f'id:{self.resource_id}, package:{self.package_id}, accesses: {self.access_count}, date: {self.access_date:%Y-%m-%d}'


def init_dap_tables():
    '''Initialize the database to include the table for the class declared above.
    '''
    model.meta.metadata.create_all(model.meta.engine)

def update_access_counts(downloads, start_date, end_date):
    # Retrieve any existing entries within the specificed date range,
    # to update their access counts if needed.
    access_list = meta.Session.query(DAPResourceAccesses).filter(access_date >= start_date).filter(access_date <= end_date)

    for res_id, pkg_id, date, count in downloads:
        da = DAPResourceAccess(resource_id=res_id, package_id = pkg_id, access_date = date, access_count = count)
        model.Session.add(da)

    model.Session.commit()

def latest_resource_access():
    '''Retrieve the latest date recorded for a DAP resource tracking event.
    '''
    latest = None
    try:
        latest = model.meta.Session.query(func.max(DAPResourceAccess.access_date)).all()
    except Exception as e:
        _log.debug('No DAP access records found.', exc_info=e)
    return latest

def total_resource_accesses(resource_id, start_date = None, end_date = None) -> int:
    '''Calculate how many accesses a specified resource had over an optional date range.
    '''
    accesses = 0
    try:
        access_query = model.meta.Session.query(func.sum(DAPResourceAccess.access_count)).filter(resource_id=resource_id)
        if start_date is not None:
            access_query.filter(access_date >= start_date)
        if end_date is not None:
            access_query = access_query.filter(access_date <= end_date)
        accesses = access_query.all()
    except Exception as e:
        lp = {'resource': resource_id}
        if start_date is not None:
            lp['Starting date'] = start_date.strftime('%Y-%m-%d')
        if end_date is not None:
            lp['Ending date'] = end_date.strftime('%Y-%m-%d')
        _log.exception('Error retrieving DAP access count', extra=lp)
    return accesses

def total_package_accesses(package_id, start_date = None, end_date = None) -> int:
    '''Calculate how many accesses a specified package's resources had over an optional date range.
    '''
    accesses = 0
    try:
        access_query = model.meta.Session.query(func.sum(DAPResourceAccess.access_count)).filter(package_id=package_id)
        if start_date is not None:
            access_query.filter(access_date >= start_date)
        if end_date is not None:
            access_query = access_query.filter(access_date <= end_date)
        accesses = access_query.all()
    except Exception:
        lp = {'package': package_id}
        if start_date is not None:
            lp['Starting date'] = start_date.strftime('%Y-%m-%d')
        if end_date is not None:
            lp['Ending date'] = end_date.strftime('%Y-%m-%d')
        _log.exception('Error retrieving DAP access count', extra=lp)
    return accesses

def total_accesses(start_date = None, end_date = None) -> int:
    '''Calculate the total number of accesses for all resources in the CKAN instance,
    optionally within a specified date range.
    '''
    accesses = 0
    try:
        access_query = model.meta.Session.query(func.sum(DAPResourceAccess.access_count))
        if start_date is not None:
            access_query = access_query.filter(access_date >= start_date)
        if end_date is not None:
            access_query = access_query.filter(access_date <= end_date)
        accesses = access_query.all()
    except Exception as e:
        lp = {}
        if start_date is not None:
            lp['Starting date'] = start_date.strftime('%Y-%m-%d')
        if end_date is not None:
            lp['Ending date'] = end_date.strftime('%Y-%m-%d')
        _log.exception('Error retrieving DAP access count', extra=lp)
    return accesses

def top_resources(start_date = None, end_date = None, number = 20):
    top = []
    try:
        top_query = model.meta.Session.query(func.sum(DAPResourceAccess.access_count), \
            DAPResourceAccess.resource_id, DAPResourceAccess.package_id)\
                .order_by(text("1"))
        if start_date is not None:
            top_query = top_query.filter(access_date >= start_date)
        if end_date is not None:
            top_quuery = top_query.filter(access_date <= end_date)
        top = top_query.limit(number).all()
    except Exception as e:
        lp = {'Number top resources': number}
        if start_date is not None:
            lp['Starting date'] = start_date.strftime('%Y-%m-%d')
        if end_date is not None:
            lp['Ending date'] = end_date.strftime('%Y-%m-%d')
        _log.exception('Error retrieving DAP top resources', extra=lp)

def top_packages(start_date = None, end_date = None, number = 20):
    top = []
    try:
        top_query = model.meta.Session.query(func.sum(DAPResourceAccess.access_count), \
            DAPResourceAccess.package_id).order_by(text("1"))
        if start_date is not None:
            top_query = top_query.filter(access_date >= start_date)
        if end_date is not None:
            top_quuery = top_query.filter(access_date <= end_date)
        top = top_query.limit(number).all()
    except Exception as e:
        lp = {'Number top packages': number}
        if start_date is not None:
            lp['Starting date'] = start_date.strftime('%Y-%m-%d')
        if end_date is not None:
            lp['Ending date'] = end_date.strftime('%Y-%m-%d')
        _log.exception('Error retrieving DAP top packages', extra=lp)
