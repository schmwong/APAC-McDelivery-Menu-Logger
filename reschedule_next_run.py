
# This script only works within Github Actions
# pip install ruamel.yaml
# ---


import os
from ruamel.yaml import YAML


# import env variable from runner's bash shell
workflow_file = os.environ["workflow_path"]
yaml = YAML()  # defaults to round-trip (typ="rt")

with open(workflow_file, "r") as file:
	wf = yaml.load(file) # yaml contents loaded as a python dictionary
	schedules = wf["on"]["schedule"]
	
	# edit cron strings
	for schedule in schedules:
		cron = (schedule["cron"]).split()
		new_hour = int(cron[1]) + 3
		if new_hour > 23:
			new_hour = f'0{new_hour - 23}'
		elif new_hour < 10:
			new_hour = f'0{new_hour}'
		else:
			new_hour = str(new_hour)
		cron[1] = new_hour
		cron = " ".join(cron)
		schedule["cron"] = cron


with open(workflow_file, "w") as file:
	yaml.dump(wf, file)


print(wf)