CKAN Google Analytics Extension
===============================

**Status:** Production

**CKAN Version:** >= 2.9.*

A CKAN extension that retrieves statistics from the Digital Analytics Program (DAP) 
for insertion into CKAN pages.

Features
--------

* Retrieves download events tracked by DAP and records them for later retrieval.

* Enables listing the datasets accessed most frequently.

* Enables displaying an access count for datasets and resources.

* Tracks all accesses to resources indexed in a CKAN instance, whether the access
originated from the CKAN instance or some other DAP-enabled website.

Installation
------------

1. Install the extension as usual, (e.g. from an activated virtualenv):

    ::

    $ pip install -e  git+https://github.com/katucker/ckanext-dapr.git
    $ pip install -r ckanext-dapr/requirements.txt

2. Edit your ckan.ini (or similar) to provide the parameters below for 
retrieving and displaying tracking data.

    ::
        ckanex.dapr.retrieval_agency = <Agency name to use in the API for
            retrieving tracking event totals. If set, must match an agency
            name defined in the GSA DAP API at https://open.gsa.gov/api/dap/.
            If not set, tracking event totals for all agencies will be 
            retrieved, which could be a lengthy list.>
        ckanext.dapr.keyfile = <Full path to a file containing the API key to
            use for retrieving tracking events. 
            See https://open.gsa.gov/api/dap/ to register for an API key.
            If not set, the API key must be provided in environment variable
            DAP_KEY or the statistics retrieval command will fail.>
        ckanext.dapr.show_downloads = <True to display on a resource's page
            how many times it has been downloaded.>
        ckanext.dapr.api_url = <The web location to use for the DAP API. 
            Defaults to https://api.gsa.gov/analytics/dap/v2.0.0/>
        ckanext.dapr.batch_size = <The number of tracking events to retrieve in
            each call to the DAP API. Defaults to 1,000. The DAP API sets an upper
            limit of 10,000 on this parameter. >

3. Add the extension to the list of plugins in the ini file,
   such as the following:

   ::

      ckan.plugins = dap dapr

   (The dap extension is a separate CKAN extension, shown here
   to illustrate specifying multiple CKAN extensions.)


Setting Up Statistics Retrieval from the Digital Analytics Program
-----------------------------------------------------

1. Run the following command from your activated CKAN environment to
   set up the required database tables (of course, altering the
   ``--config`` option to point to your site config file)::

       ckan dapr initdb --config=/etc/ckan/default/ckan.ini

4. Restart CKAN (e.g. by restarting Apache)

6. Import DAP tracking event counts by running the following command from
   your activated CKAN environment::

       ckan dapr load --config=/etc/ckan/default/ckan.ini [--start_date YYYY-mm-dd] [--end_date YYYY-mm-dd]

   (Of course, pointing config at your specific site config)

   If the optional start date argument is not specified, the load command will retrieve DAP
   tracking events from the earliest recorded date for the DAP program.

   If the optional end date argument is not specified, the load command will retrieve all DAP
   tracking events up to the current date.

   Running the dapr load command without start and end date arguments is useful for initializing
   the database when the extension is first installed.

7. Configure a cron, supervisord, or equivalent job to regularly run the dapr load command
 in order to update the statistics. Use a start date argument for the recurring command runs to
 operate efficiently.

Testing
------------

Install this repo at the same level as the CKAN repo. For example:

~/code/ckan
~/code/ckanext-dapr

Then pytest can be run from the ckanext-dapr directory, using the pytest
fixtures the CKAN repo provides using the following commands:

cd ~/code/ckanext-dapr
pytest --ckan-ini=test.ini
