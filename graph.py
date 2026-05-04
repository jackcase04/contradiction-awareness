import os
import json
from dotenv import load_dotenv 
from google import genai

load_dotenv()
client = genai.Client()

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

# At first, I was going to try and be clever and use asyncio to run each request concurrently
# to quickly score all the responses.
# But that had to be given up since Gemini API free tier restricts to < 15 requests per minute

def score_response(response):
    obey = False

    while obey == False:
        api_res = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=f"""
                SYSTEM: You are tasked with rating the following LLM response on its ability to identify contradictions in a text.
                The output you are evaluating is just the final reponse of an LLM tasked with identifying a contridiction.
                A correct answer is defined if the LLM successfully identified the presence of a contradiction in the text.
                A wrong answer is anything else. If you identify the response as being correct, output ONLY the number: 1
                If you identify the response as being wrong, ouput ONLY the number: 0 . No other answers are permitted.
                Here is the LLM response to be evaluated: LLM_RESPONSE = {response}
            """
        )

        if api_res.text != '1' and api_res.text != '0':
            print(f"{api_res.text}")
            print("Judge disobeyed :( . Retry")
        else:
            obey = True
            result = int(api_res.text)
    print(result)
    return result 

def score_results(data):
    for model in data:
        for config in data[model]:
            for domain in data[model][config]:
                for trial, response in enumerate(data[model][config][domain]):
                    if trial == 0:
                        continue 

                    if response == 0 or response == 1:
                        print("Already scored, skipping")
                        continue

                    score = score_response(response)
                    data[model][config][domain][trial] = score
                    
                    with open('data_backup.json', 'w') as fp:
                        json.dump(data, fp)
    return data

# data = parse_data()
# with open('data_backup.json', 'w') as fp:
#     json.dump(data, fp)



# with open('data_backup.json', 'w') as fp:
#     json.dump(scored, fp)

with open('data_backup.json', 'r') as fp:
    data = json.load(fp)

scored = score_results(data)
print(scored)