# encoding: utf-8
import datetime
import logging
import click

from . import daputil

log = logging.getLogger(__name__)

def get_commands():
    return [
        dap
    ]


@click.group()
def dap():
    pass

@dap.command(short_help=u"Initialize the database for storing Digital Analytics Program analytics.")
def init():
    """Initialise the local DAP analytics database tables
    """
    model.Session.remove()
    model.Session.configure(bind=model.meta.engine)
    daputil.init_dap_tables()
    log.info("Set up DAP access tables in main database")


@dap.command(short_help=u"Load resource access data from Digital Analytics Program API.")
@click.option("-s", "--start-date", required=False, help="Load events from this date forward (YYYY-mm-dd).")
@click.option("-e", "--end-date", required=False, help="Load events up to this date (YYYY-mm-dd)")
@click.option("-u", "--update", is_Flag=True, help="Load new events since last run.")
def load(start_date: str = None, end_date: str = None, update: bool):
    start_day = None
    end_day = None
    if update:
        # Retrieve the latest date recorded in the database event tracking table, and set
        # that as the starting date for retrieval.
        start_day = dap_util.latest_resource_access()
        if start_day is None:
            # No resource accesses recorded yet. Default to the date DAP was first mandated. 
            try:
                start_day = datetime.datetime.strptime(DAP_FIRST_DAY, '%Y-%m-%d')
            except Exception:
                log.exception('Error defaulting to start date %s. Load failed.', DAP_FIRST_DAY)
                return
    else:
        if start_date is None:
            # Not updating, but no start date specified. Default to the date DAP was first mandated.
            try: 
                start_day = datetime.datetime.strptime(DAP_FIRST_DAY, '%Y-%m-%d')
            except Exception:
                log.exception('Error defaulting to start date %s. Load failed', DAP_FIRST_DAY)
                return
        else:
            try:
                start_day = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            except Exception:
                log.exception('Error interpreting start date %s. Load failed.', start_date)
                return
        if end_date is not None:
            try:
                end_day = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            except Exception:
                log.exception('Ignoring error interpreting end date %s', end_date)

    """Parse data from Digital Analytics Program API, cross-reference it
    to package resources and get a list of resource access counts by date.
    """
    downloads = daputil.dap_retrieve(start_day, end_day)

    if len(downloads) > 0:
        daputil.update_access_counts(downloads, start_day, end_day)


