import jira
import getpass
import argparse
from datetime import datetime


MSW_JIRA = "https://jira.datcon.co.uk"
READ_ONLY_USER = "read.only"
READ_ONLY_PW = "@Whewell1833!"

def get_jira_client(username=READ_ONLY_USER, password=READ_ONLY_PW):
    """
    Prompt user for relevant inputs, then create and return a JIRA python
    client.
    """
    return jira.JIRA(MSW_JIRA, auth=(username, password))


def jira_seconds_to_days(seconds):
	return (seconds/3600.0)/8.0