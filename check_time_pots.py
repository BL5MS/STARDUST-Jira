import jira
import getpass
import argparse
from datetime import datetime
from utils.common import get_jira_client, jira_seconds_to_days
from utils.common import MSW_JIRA
import csv

##############################################################################
# A quick and dirty script which does the following:
# Asks the User for their login for "jira.datcon.co.uk"
# Asks what Project and dates they want to query time tracking for.
# Spits out all the users that have tracked time in that sprint, the total
# time spent, and a breakdown between issues.
##############################################################################

parser = argparse.ArgumentParser(description="Check Epic Time Pots")
parser.add_argument("-f", dest="csv_file", type=str, 
                    help="Path to csv file containing existing epic data")

required_arguments = parser.add_argument_group("Required Arguments")
required_arguments.add_argument("-e", dest="epic_key", type=str, 
                                help="Your Jira Epic Key", required=True)


def get_issues(jira_client, epic_key, max_results=9999):
    """
    Uses a JQL query to return all the relvant issues as jira.Issues, 
    in a list.
    We only ask for the summary fields in the interests of saving time 
    waiting for query to finish.
    """

    jql_string = "\"Epic Link\"={0}"
    # To get issue fields. Export an issue to XML & comb through it.
    issue_fields = ["summary, timeoriginalestimate", "timeestimate", 
                    "timespent"]

    return jira_client.search_issues(jql_string.format(epic_key),
                                     fields=issue_fields, 
                                     maxResults=max_results)


def read_csv_into_issues(csvfile):
    # Fields can be None, in this case write down 0
    # CSV order is ID, Summary, Original est, Remaining Est, TimeSpent

    issues = {}
    try:
        with open(csvfile, 'r') as csv_file:

            # BUG HERE
            issue_reader = csv.reader(csv_file, delimiter=',')
            for row in issue_reader:
                # Pop 2 do stuff
                key = row.pop(0)
                summary = row.pop(0)
                issues[key] = [summary] + [float(i) for i in row]
    except IOError:
        print("File doesn't exist, creating.")

    return issues


def write_issues_into_csv(issues, file_name="default.csv"):
    """
    """
    # Must open with type 'wb' and not just 'w' because
    # of https://stackoverflow.com/questions/3191528/csv-in-python-adding-an-extra-carriage-return-on-windows
    with open(file_name, 'wb') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for issue_id, info in issues.items():
            writer.writerow([issue_id] + info)


def convert_issues_to_dict(issues):
    """
    For the Jira issues, convert to a dict where the ID is
    the Key and the items are a list of the time information
    """
    output = {}

    for issue in issues:

        time_info = []

        # Yes, having the summary as the first one in the list breaks
        # the aspect of having the list being a "time info" variable
        time_info.append(issue.fields.summary)

        for time in [issue.fields.timeoriginalestimate,
                     issue.fields.timeestimate,
                     issue.fields.timespent]:

            if time == None:
                time = 0

            time_info.append(jira_seconds_to_days(time))

        output[issue.id] = time_info

    return output


def compare_and_report_ind(new, old):
    if not old:
        print("No old info, skipping comparison")
    else:
        diff = []
        new_issues = []

        for issue_id, timeinfo in new.items():

            if issue_id not in old.keys():
                new_issues.append(issue_id)
            else:
                if old[issue_id] != new[issue_id]:
                    diff.append(issue_id)

        print("These are the issues which are new:")
        for issue_id in new_issues:
            print("Issue Summary: {0}".format(new[issue_id][0]))
            print("Original_Estimate: {0}".format(new[issue_id][1]))
            print("Remaining_Estimate: {0}".format(new[issue_id][2]))
            print("Time Spent: {0}".format(new[issue_id][3]))

        print("These are the issues which have changed:")
        for issue_id in diff:
            print("Issue Summary: {0}".format(new[issue_id][0]))
            print ("Original Estimate:")
            print("Old  : {0}".format(old[issue_id][1]))
            print("New  : {0}".format(new[issue_id][1]))
            print("Diff : {0}").format(new[issue_id][1]-old[issue_id][1])

            print ("Remaining_Estimate")
            print("Old  : {0}".format(old[issue_id][2]))
            print("New  : {0}".format(new[issue_id][2]))
            print("Diff : {0}").format(new[issue_id][2]-old[issue_id][2])

            print("Time Spent")
            print("Old  : {0}".format(old[issue_id][3]))
            print("New  : {0}".format(new[issue_id][3]))
            print("Diff : {0}").format(new[issue_id][3]-old[issue_id][3])

        # Now compare totals:
        new_total_original_est = 0
        new_total_est = 0
        new_total_time_spent = 0
        old_total_original_est = 0
        old_total_est = 0
        old_total_time_spent = 0

        for issue_id, timeinfo in new.items():
            new_total_original_est += timeinfo[1]
            new_total_est += timeinfo[2]
            new_total_time_spent += timeinfo[3]

        for issue_id, timeinfo in old.items():
            old_total_original_est += timeinfo[1]
            old_total_est += timeinfo[2]
            old_total_time_spent += timeinfo[3]

        print("Old time:")
        print("Original_Estimate: {0}".format(old_total_original_est))
        print("Remaining_Estimate: {0}".format(old_total_est))
        print("Time Spent: {0}".format(old_total_time_spent))
        print("Total PRD Time: {0}".format(
              old_total_est + old_total_time_spent))

        print("New time:")
        print("Original_Estimate: {0}".format(new_total_original_est))
        print("Remaining_Estimate: {0}".format(new_total_est))
        print("Time Spent: {0}".format(new_total_time_spent))
        print("Total PRD Time: {0}".format(
              new_total_est + new_total_time_spent))


def main():
    args = parser.parse_args()

    mswJira = get_jira_client()
    new_issues = get_issues(mswJira, args.epic_key)

    if args.csv_file:
        old_issues = read_csv_into_issues(args.csv_file)
    else:
        old_issues = None

    new_issues = convert_issues_to_dict(new_issues)
    compare_and_report_ind(new_issues, old_issues)

    write_issues_into_csv(new_issues, args.csv_file)


if __name__ == '__main__':
    main()
