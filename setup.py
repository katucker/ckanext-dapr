from setuptools import setup, find_packages

version = "0.1"

setup(
    name="ckanext-dapr",
    version=version,
    description="Retrieve Digital Analytics Program (DAP) tracking information for reporting within a CKAN instance",
    long_description="""The United States Federal Government tracks use of its websites through
    the Digital Analytics Program, with file downloads separately tracked from web pages. This CKAN extension
    implements commands for retrieving the tracking statistics for Resources
    referenced in a CKAN instance, regardless of whether the Resource is stored in the CKAN
    instance or not. The retrieved tracking statistics are available for reporting usage for
    Resources and their containing Datasets.
	""",
    classifiers=['Development Status :: 2 - Pre-Alpha','Environment :: Plugins',
    'Programming Language :: Python :: 3'],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords="",
    author="Keith Tucker",
    author_email="keith.tucker@ed.gov",
    url="",
    license="GNU Affero General Public License version 3",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    namespace_packages=["ckanext", "ckanext.dapr"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points="""
        [ckan.plugins]
	# Add plugins here, eg
	dap=ckanext.dapr.plugin:DAPRPlugin

        [paste.paster_command]
        load = ckanext.dapr.commands:load
        initdb = ckanext.dapr.commands:initdb
	""",
)
