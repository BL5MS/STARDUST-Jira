import jira
import getpass
import argparse
from datetime import datetime

try:
    input_func = raw_input
except Exception as e:
    input_func = input

##############################################################################
# A quick and dirty script which does the following:
# Asks the User for their login for "jira.datcon.co.uk"
# Asks what Project and dates they want to query time tracking for.
# Spits out all the users that have tracked time in that sprint, the total
# time spent, and a breakdown between issues.
##############################################################################
MSW_JIRA = "https://jira.datcon.co.uk"


parser = argparse.ArgumentParser(description="Check STARDUST Timetracking")
parser.add_argument("-S", dest="sprints", type=str, help="The comma sepearted list of Sprint IDs to check.")
parser.add_argument("-ed", dest="end_date", default=None, type=str, help="the end date of your " 
                    "time tracking query in the format YYYY/MM/DD")

required_arguments = parser.add_argument_group("Required Arguments")
required_arguments.add_argument("-u", dest="username", type=str, help="Your Jira username", required=True)
required_arguments.add_argument("-pw", dest="password", type=str, help="Your Jira password", required=True)
required_arguments.add_argument("-sd", dest="start_date", type=str, help="the starting date of your " 
                    "time tracking query in the format YYYY/MM/DD.", required=True)
required_arguments.add_argument("-k", dest="jira_key", type=str, help="Your Jira Project Key", required=True)


# A Day of time currently converts to 28800 Jira "Time units"
# I don't bother trying to break down more finely than 1/8th of a day - 
# 3600 Jira time units.
# There is a "timespent" which reports e.g. 1d, 6h. But it's less of a faff
# to just pull everything in seconds, then convert it all in the end.

class JiraUserWrapper():
    """
    Wrapper class to hold information about certain Jira users.
    """
    def __init__(self, key):
        """
        :param key: The Jira "key" representing this user. For us it should
            be our DCL initals.
        """
        self.key = key
        self.total_time_worked = 0

        # Issues worked is a string: int dictionary. Where the string is
        # the Jira story ID and the int is the time worked on that story.
        self.issues_worked = {}

def get_issues(jira_client, max_results=9999):
    """
    Uses a JQL query to return all the relvant issues as jira.Issues, 
    in a list.
    We only ask for the summary fields in the interests of saving time 
    waiting for query to finish.
    """
    project_base_key = None
    worklog_start_date = None
    worklog_end_date = None

    jql_string = "project={0} and timespent > 0 and worklogDate >= \"{1}\""
    issue_fields="summary"

    while not project_base_key:
        project_base_key = input_func("Enter the JIRA Key for your JIRA project: ")

    while not worklog_start_date:
        worklog_start_date = input_func("Please enter the starting date of your " 
                                        "time tracking query in the format" 
                                        " YYYY/MM/DD: ")
        try:
            datetime.strptime(worklog_start_date, "%Y/%m/%d")
        except ValueError:
            print("Date format not recognised.")
            worklog_start_date = None

    while not worklog_end_date:
        worklog_end_date = input_func("Please enter the end date of your " 
                                      "time tracking query in the format" 
                                      " YYYY/MM/DD. Leave blank for a default of now: ")
        if worklog_end_date == "":
            worklog_end_date = datetime.now().strftime("%Y/%m/%d")
            jql_string = jql_string + " and workLogDate <= now()"

        else:
            try:
                datetime.strptime(worklog_end_date, "%Y/%m/%d")
            except ValueError:
                print("Date format not recognised.")
                worklog_end_date = None
            else:
                jql_string = jql_string + " and workLogDate <= \"{0}\"".format(
                                  worklog_end_date)



    return jira_client.search_issues(jql_string.format(project_base_key, worklog_start_date),
                                 fields=issue_fields, maxResults=max_results)

def get_worklogs(jira_client, issue_list):
    """
    For a list of Jira issues. Get the associated worklogs for them.
    """
    worklogs = []
    for issue in issue_list:
        worklogs.extend(jira_client.worklogs(issue=issue.key))

    return worklogs

def get_corresponding_issue(worklog, issue_list):
    """
    For a worklog, return the corresponding issue in the issue list.
    """
    for issue in issue_list:
        if worklog.issueId == issue.id:
            return issue

def create_user_data(issue_list, worklogs):
    """
    Go through all of the worklogs and create/append the timespent into a list
    of jira users, then return the list of jira users.
    """
    jira_users = {}

    for worklog in worklogs:

        # If we can't find a user key, create it.
        if worklog.author.key not in jira_users.keys():
            new_user = JiraUserWrapper(worklog.author.key)
            jira_users[worklog.author.key] = new_user

        jira_user = jira_users.get(worklog.author.key)
        corresponding_issue = get_corresponding_issue(worklog, issue_list)

        user_issue_timespent = jira_user.issues_worked.get(
            corresponding_issue.key, 0)

        jira_user.total_time_worked += worklog.timeSpentSeconds
        user_issue_timespent += worklog.timeSpentSeconds
        jira_user.issues_worked[corresponding_issue.key] = user_issue_timespent

    return jira_users

def print_output(jira_users):
    """
    Prints the output in some kind of pretty format.
    """
    for user_key in jira_users:

        # Convert the "jira time units" into days:
        user = jira_users.get(user_key)
        days_worked = (user.total_time_worked/3600)/8

        useroutput = "\nUser {0} has logged {1} days in total. \n" \
            "A breakdown of this timetracking is as follows: \n".format(
                user_key, days_worked)

        for story, jira_time in user.issues_worked.items():
            days_worked = (jira_time/3600)/8
            useroutput = useroutput + "Story: {0}, time_spent: {1} days.\n".format(
                story, days_worked)
            
        print(useroutput)


def get_jira_client(username, password):
    """
    Prompt user for relevant inputs, then create and return a JIRA python
    client.
    """
    username = None
    password = None
    project_base_key = None
    worklog_start_date = None

    while not username:
        username = input_func("Enter your Atlassian username: ")

    while not password:
        password = getpass.getpass("Enter your Password: ")

    return jira.JIRA(MSW_JIRA, auth=(username, password))


def main():
	args = parser.parse_args()
    mswJira = get_jira_client()
    issues = get_issues(mswJira)
    worklogs = get_worklogs(mswJira, issues)
    users = create_user_data(issues, worklogs)
    print_output(users)


if __name__ == '__main__':
    main()
