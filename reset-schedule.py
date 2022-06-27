# This script only works within Github Actions
# pip install ruamel.yaml
# ---


import csv
import os
from ruamel.yaml import YAML


# import env variables from runner's bash shell
workflow_file = os.environ["workflow_path"]
workflow_name = os.environ["workflow_name"]

code = workflow_name.split("-")[1]
default_cron = []
wf_cron = []


with open("default-schedule.csv", mode="r") as csv_file:
	read_rows = csv.reader(csv_file)
	header_row = next(read_rows)
	if header_row != None:
		for row in read_rows:
			if row[1] in code:
				default_cron.append(row[4])

print(f"\n\nDefault cron times for {workflow_name} are:\n{default_cron}\n\n")
		

yaml = YAML()  # defaults to round-trip (typ="rt")

with open(workflow_file, "r") as file:
	wf = yaml.load(file)
	schedules = wf["on"]["schedule"]
	for schedule in schedules:
		wf_cron.append(schedule["cron"])

print(f"Current cron times are:\n{wf_cron}\n\n")



if wf_cron == default_cron:
	print("\nNo reset needed.\n\n")
	
else:
	for schedule, Cron in zip(schedules, default_cron):
		if schedule["cron"] != Cron:
			schedule["cron"] = Cron
	print("\nSchedule has been reset.\n\n")
			

with open(workflow_file, "w") as file:
	yaml.dump(wf, file)


print(wf)