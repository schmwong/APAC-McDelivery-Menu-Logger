import os
import re
import asyncio
import shutil

# Each csv file contains a datetimestamp in its filename. We want to sort all files into subfolders by year.

"""
This function takes a root directory as input and iterates over its immediate subdirectories.
For each subdirectory, it checks if the directory name matches the folder regex pattern.
If it does, it proceeds to iterate over the files in that folder, selecting only those that match the file regex pattern.
Each selected file is immediately moved into its respective year subfolder. The year subfolder is created if it does not exist.
Finally, it returns a list of tuples where each tuple contains the folder name and a list of selected file names within that folder.
"""


async def select_folders_and_files(root_dir):
    folder_regex = re.compile(r"^(mcd)-\w+-\w+$")
    file_regex = re.compile(r"^(\[\d{4}-\d{2}-\d{2}).+(\.csv)$")

    selected_folders_and_files = []

    async def process_folder(folder_name):
        folder_path = os.path.join(root_dir, folder_name, "scraped-data")
        if os.path.isdir(folder_path) and folder_regex.match(folder_name):
            selected_files = []
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                print(f"Looking in scraped-data subfolder in folder `{folder_name}`...")
                if os.path.isfile(file_path) and file_regex.match(file_name):
                    selected_files.append(file_name)
                    # Extract year portion from filename
                    year_match = re.match(r"\[(\d{4})-\d{2}-\d{2}.+\.csv$", file_name)
                    if year_match:
                        year_folder = year_match.group(1)
                        year_folder_path = os.path.join(folder_path, year_folder)
                        if not os.path.exists(year_folder_path):
                            os.makedirs(year_folder_path)
                            print(f"Creating year folder {year_folder} in {folder_name}.")
                        shutil.move(file_path, os.path.join(year_folder_path, file_name))
                        print(f"Moving {file_name} to {year_folder}.")
            if (len(selected_files) > 0):
                selected_folders_and_files.append((folder_name, selected_files))
                print(f"{len(selected_files)} files sorted in {folder_name}.")
            else:
                print(f"No files to be sorted in {folder_name}.")

    tasks = []
    for folder_name in os.listdir(root_dir):
        tasks.append(process_folder(folder_name))

    await asyncio.gather(*tasks)

    return selected_folders_and_files


if __name__ == "__main__":
    root_directory = "."
    selected_folders_and_files = asyncio.run(select_folders_and_files(root_directory))
    # for folder_name, files in selected_folders_and_files:
    #     print(f"Folder: {folder_name}")
    #     print("Selected files:")
    #     for file_name in files:
    #         print(f"- {file_name}")
