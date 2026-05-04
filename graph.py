import os
import json
from dotenv import load_dotenv 
from google import genai

load_dotenv() 

print(os.getenv("GEMINI_API_KEY"))

def parse_data():
    data = {}

    for model in ["gemma4:latest", "llama3.2:latest", "qwen3.5:latest"]:
        data[model] = {}
        for config in ["control", "pre-prompt"]:
            data[model][config] = {}
            for domain in ["biology", "geography", "history"]:
                data[model][config][domain] = []
                for trial in range(0, 11):
                    data[model][config][domain].append("")

    for file in os.scandir("results"):
        if file.is_file():
            y = []

            with open("results/" + file.name, mode="r") as file:
                file_content = file.read()

            parts = file.name.split('_')

            model = parts[0].split('/')[1]
            config = parts[1]
            domain = parts[2]
            trial = int(parts[3].split('.')[0].split('l')[1])

            data[model][config][domain][trial] = file_content

    return data

data = parse_data()



# with open('data_backup.json', 'w') as fp:
#     json.dump(data, fp)

# data = ""

# with open('data_backup.json', 'r') as fp:
#     data = json.load(fp)

# print(data)