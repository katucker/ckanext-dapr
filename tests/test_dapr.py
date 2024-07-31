import pytest

import ckan.logic as logic
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers

from ../dapr import daputil

DAP_TEST_RESPONSE = 
[
    {  'file_name': '/fruit-and-vegetable-prices.aspx',
        'page' : 'www.ers.usda.gov/data-products'
        'date' : '2020-05-20',
        'total_events' : 50
    },
    {  'file_name': '/default/files/fsawg/datacenter/library/PortfolioSummary.xls',
        'page' : 'studentaid.gov/sites'
        'date' : '2020-05-20',
        'total_events' : 250
    },
    {  'file_name': '/ccdb/complaints.json.zip',
        'page' : 'files.consumerfinance.gov'
        'date' : '2020-05-20',
        'total_events' : 155
    },
    {
        'file_name': '/dataset/fc85541b-d729-4722-8622-e814dae86b5b/resource/80bc1b6e-f748-4b2e-81a6-746d8fcbd975/download/bpersonnel2021-22.csv',
        'page': 'data.ed.gov/dataset/idea-section-618-state-part-b-personnel/resources'
        'date' : '2020-05-20',
        'total_events' : 25
    },
    {  'file_name': '/fruit-and-vegetable-prices.aspx',
        'page' : 'www.ers.usda.gov/data-products'
        'date' : '2020-05-21',
        'total_events' : 51
    },
    {  'file_name': '/default/files/fsawg/datacenter/library/PortfolioSummary.xls',
        'page' : 'studentaid.gov/sites'
        'date' : '2020-05-21',
        'total_events' : 251
    },
    {  'file_name': '/ccdb/complaints.json.zip',
        'page' : 'files.consumerfinance.gov'
        'date' : '2020-05-21',
        'total_events' : 156
    },
    {
        'file_name': '/dataset/fc85541b-d729-4722-8622-e814dae86b5b/resource/80bc1b6e-f748-4b2e-81a6-746d8fcbd975/download/bpersonnel2021-22.csv',
        'page': 'data.ed.gov/dataset/idea-section-618-state-part-b-personnel/resources'
        'date' : '2020-05-21',
        'total_events' : 15
    },
    {  'file_name': '/fruit-and-vegetable-prices.aspx',
        'page' : 'www.ers.usda.gov/data-products'
        'date' : '2020-05-22',
        'total_events' : 52
    },
    {  'file_name': '/default/files/fsawg/datacenter/library/PortfolioSummary.xls',
        'page' : 'studentaid.gov/sites'
        'date' : '2020-05-22',
        'total_events' : 252
    },
    {  'file_name': '/ccdb/complaints.json.zip',
        'page' : 'files.consumerfinance.gov'
        'date' : '2020-05-22',
        'total_events' : 157
    },
    {
        'file_name': '/dataset/fc85541b-d729-4722-8622-e814dae86b5b/resource/80bc1b6e-f748-4b2e-81a6-746d8fcbd975/download/bpersonnel2021-22.csv',
        'page': 'data.ed.gov/dataset/idea-section-618-state-part-b-personnel/resources'
        'date' : '2020-05-22',
        'total_events' : 25
    }
]

class MockDAPAPI:
    def init(self, *args, **kwargs):
        self.start = daputil.DAP_FIRST_DAY 
        self.end = '2024-08-23' # A date significant to the extension author.
        # If there is more than one positional argument, the second one
        # is the dictionary of parameters for the GET request.
        if len(args) > 1:
            if 'after' in args[1]:
                self.start = args[1]['after']
            if 'before' in args[1]:
                self.end = args[1]['before']
        # If there is a 'params' keywork argument, it contains the
        # dictionary of GET request parameters.
        if 'params' kwargs.keys():
            params = kwargs['params']
            if 'after' in params:
                self.start = params['after']
            if 'before' in params:
                self.end = params['before']

    def json(self):
        # Return the entries in the DAP_TEST_RESPONSE list that fall within
        # the start and end dates provided when the mock API object was created.
        return [x in DAP_TEST_RESPONSE if x['date'] >= self.start and x['date'] <= self.end]

_TEST_FSA_DATA = daputil.construct_resource_url_from_dap(file=DAP_TEST_RESPONSE[1]['file_name'],
                page=DAP_TEST_RESPONSE[1]['page'])
_TEST_IDEA_DATA = daputil.construct_resource_url_from_dap(file=DAP_TEST_RESPONSE[3]['file_name'],
                page=DAP_TEST_RESPONSE[31]['page'])

@pytest.fixture
def load_test_resources():
    """ Create some test CKAN content, matching a subset of the test DAP data.
    """
    test_org = {
        'name': 'test_org',
        'title': 'Test Org'
    }
    test_org_id = helpers.call_action('organization_create', data_dict=test_org)
    res_list = [
        {
            'name': 'Test FSA data',
            'url': _TEST_FSA_DATA 
        },
        {
            'name': 'Test IDEA data',
            'url': _TEST_IDEA_DATA
        }
    ]
    
    test_pkg = {
        'name': 'test_data_asset',
        'title': 'Test data asset',
        'resources': res_list,
        'owner_org': test_org_id
    }
    _ = helpers.call_action('package_create', data_dict=prices_pkg)

# Set the CKAN configuration to use this extension.
@pytest.mark.ckan_config('ckan_plugins', 'dapanalytics')

# Set pytest fixtures (defined in ckan/ckan/tests/pytest_ckan/fixtures.py
# in the CKAN repo) to use for all tests.
@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')

@helpers.change_config('ckanext.dapanalytics.batch_size', 40000)
def test_config_batch_size_cap(self, app):
    """ Requesting the "app" fixture triggers loading the CKAN configuration,
     so this test verifies the configuration loading code caps the
     batch size parameter to the maximum the DAP API allows.
    """
    assert app.config['ckanext.dapanalytics.batch_size'] == 10000
    
def test_targeted_load(monkeypatch, cli, load_test_data):
    def mock_dap_api(*args, **kwargs):
        return MockDAPAPI(args, kwargs)

    monkeypatch.setattr(requests, 'get', mock_dap_api)

    from ../dapr/cli import load

    cli.invoke(load,['-s','2020-05-20','-e', '2020-05-20'])

    prices_res_id, _ = daputil.get_resource_ids(prices_res_url)

    # The access count for just 2020-05-20 should be recorded.
    assert(daputil.total_resource_accesses(prices_res_id) == 250) 

def test_update_load(monkeypatch, cli, load_test_data):
    def mock_dap_api(*args, **kwargs):
        return MockDAPAPI(args, kwargs)

    monkeypatch.setattr(requests, 'get', mock_dap_api)

    from ../dapr/cli import load

    cli.invoke(load,['--update'])

    res_id, _ = daputil.get_resource_ids(_TEST_FSA_URL)

    # The sum of all records for the FSA test data should be returned.
    assert(daputil.total_resource_accesses(res_id) == 753) 