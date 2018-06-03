import argparse
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

def main():
	args = parser.parse_args()
	print(args.start_date)
	print(args.sprints.split(","))

if __name__ == '__main__':
	main()