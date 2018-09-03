import jira
import argparse
from datetime import datetime
from utils.common import get_jira_client, jira_seconds_to_days
from utils.common import MSW_JIRA
import csv
from utils.slack import barryBot

##############################################################################
# A quick and dirty script which does the following:
# Uses the read-only user for jira
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

            issue_reader = csv.reader(csv_file, delimiter=',')
            for row in issue_reader:
                # Pop 2 do stuff
                # Pop the key first as otherwise the variable assignment is
                # executed last & messes up the ordering.
                # CSV order is ID, Summary, Original est, Remaining Est, TimeSpent
                key = row.pop(0)
                issues[key] = {"Summary": row.pop(0),
                               "Original_Estimate": float(row.pop(0)),
                               "Remaining_Estimate": float(row.pop(0)),
                               "TimeSpent": float(row.pop(0))}

    except IOError:
        print("File doesn't exist, creating.")

    return issues


def write_issues_into_csv(issues, file_name="default.csv"):
    """
    """
    # Must open with type 'wb' and not just 'w' because
    # of https://stackoverflow.com/questions/3191528/csv-in-python-adding-an-extra-carriage-return-on-windows
    with open(file_name, 'w', newline="\n") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for issue_id, info in issues.items():
            writer.writerow([issue_id, info['Summary'],
                            info["Original_Estimate"],
                            info["Remaining_Estimate"],
                            info["TimeSpent"]])


def convert_issues_to_dict(issues):
    """
    For the Jira issues, convert to a dict where the ID is
    the Key and the items are a dict of the issue information
    """
    output = {}

    for issue in issues:

        time_info = {}
        time_info["Summary"] = issue.fields.summary
        time_info["Original_Estimate"] = jira_seconds_to_days(
            issue.fields.timeoriginalestimate)
        time_info["Remaining_Estimate"] = jira_seconds_to_days(
            issue.fields.timeestimate)
        time_info["TimeSpent"] = jira_seconds_to_days(issue.fields.timespent)

        output[issue.id] = time_info

    return output


def compare_and_report_ind(new, old):
    if not old:
        print("No old info, skipping comparison")
        result = (0, "None")
    else:
        diff = []
        new_issues = []

        for issue_id, timeinfo in new.items():

            if issue_id not in old.keys():
                new_issues.append(issue_id)
            else:
                if old[issue_id] != new[issue_id]:
                    diff.append(issue_id)

        report = []

        report_message = "\nReport for *new* issues:"
        report.append(report_message)

        for issue_id in new_issues:
            report_message = "\nIssue Summary: {0}".format(
                new[issue_id]["Summary"])
            report_message += "\n```"
            report_message += "\n{:<6} {:<10} {:<10} {:<12}".format(
                "", "Ori. Est.", "Rem. Est.", "Time Spent")

            report_message += "\n{:<6} {:<10} {:<10} {:<12}".format(
                "",
                new[issue_id]["Original_Estimate"],
                new[issue_id]["Remaining_Estimate"],
                new[issue_id]["TimeSpent"])

            # We need an faff line here incase the new section is empty.
            report_message += "\n" + "_"*20
            report_message += "\n```"
            report.append(report_message)

        report_message = "\nReport for *old* issues:"
        report.append(report_message)
        for issue_id in diff:
            report_message = "\nIssue Summary: {0}".format(
                old[issue_id]["Summary"])

            report_message += "\n```"

            report_message += "\n{:<6} {:<10} {:<10} {:<12}".format(
                "", "Ori. Est.", "Rem. Est.", "Time Spent")
            report_message += "\n{:<6} {:<10} {:<10} {:<12}".format(
                "Old",
                old[issue_id]["Original_Estimate"],
                old[issue_id]["Remaining_Estimate"],
                old[issue_id]["TimeSpent"])

            report_message += "\n{:<6} {:<10} {:<10} {:<12}".format(
                "New",
                new[issue_id]["Original_Estimate"],
                new[issue_id]["Remaining_Estimate"],
                new[issue_id]["TimeSpent"])

            report_message += "\n{:<6} {:<10} {:<10} {:<12}".format(
                "Diff",
                new[issue_id]["Original_Estimate"] - old[issue_id][
                    "Original_Estimate"],
                new[issue_id]["Remaining_Estimate"] - old[issue_id][
                    "Remaining_Estimate"],
                new[issue_id]["TimeSpent"] - old[issue_id][
                    "TimeSpent"],)

            report_message += "\n" + "_"*20
            report_message += "\n```"
            report.append(report_message)

        # Now compare totals:
        new_total_original_est = 0
        new_total_est = 0
        new_total_time_spent = 0
        old_total_original_est = 0
        old_total_est = 0
        old_total_time_spent = 0

        for issue_id, timeinfo in new.items():
            new_total_original_est += timeinfo["Original_Estimate"]
            new_total_est += timeinfo["Remaining_Estimate"]
            new_total_time_spent += timeinfo["TimeSpent"]

        for issue_id, timeinfo in old.items():
            old_total_original_est += timeinfo["Original_Estimate"]
            old_total_est += timeinfo["Remaining_Estimate"]
            old_total_time_spent += timeinfo["TimeSpent"]

        new_totals = new_total_est + new_total_time_spent
        old_totals = old_total_est + old_total_time_spent

        report_message = "\n*Summary of Totals:*"
        report_message += "\n```"
        report_message += "\n{:<4} {:<10} {:<10} {:<12} {:<15}".format(
                "", "Ori. Est.", "Rem. Est.", "Time Spent",
                "Total PRD Time")
        report_message += "\n{:<4} {:<10} {:<10} {:<12} {:<15}".format(
                "Old", old_total_original_est, old_total_est, 
                old_total_time_spent, old_totals)

        report_message += "\n{:<4} {:<10} {:<10} {:<12} {:<15}".format(
                "New", new_total_original_est, new_total_est, 
                new_total_time_spent, new_totals)
        
        report_message += "\n" + "_"*20
        report_message += "\n```"
        report.append(report_message)

        print(len(diff + new_issues))
        if len(diff + new_issues) > 0:
            return (1, report)
        else:
            return (0, report)


def check_activity():
    args = parser.parse_args()

    mswJira = get_jira_client()
    new_issues = get_issues(mswJira, args.epic_key)

    if args.csv_file:
        old_issues = read_csv_into_issues(args.csv_file)
    else:
        old_issues = None

    new_issues = convert_issues_to_dict(new_issues)
    result = compare_and_report_ind(new_issues, old_issues)

    write_issues_into_csv(new_issues, args.csv_file)

    if result[0]:
        for message in result[1]:
            barryBot.send_message(message)


if __name__ == '__main__':
    check_activity()
