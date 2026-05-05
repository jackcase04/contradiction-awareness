import os
import json
import matplotlib.pyplot as plt
import numpy as np
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

def score_results_human(data, model):
    for config in data[model]:
        for domain in data[model][config]:
            for trial, response in enumerate(data[model][config][domain]):
                if trial == 0:
                    continue 

                if response == 0 or response == 1:
                    print("Already scored, skipping")
                    continue
                
                print(f"Score this response from {model}, domain {domain}, and trial {trial}:")
                print(f"Score it based on correct being identified a contradiction\n")
                print(f"{response}")
                score = input("Type \'y\' for correct and \'n\' for incorrect\n")

                while score != 'y' and score != 'n':
                    print("Invalid input")
                    score = input("Type \'y\' for correct and \'n\' for incorrect\n")

                data[model][config][domain][trial] = 1 if score == 'y' else 0
                print("\n")
                
    return data

def generate_plot(data):
    fix, ax = plt.subplots()
    cats = ["control", "pre-prompt"]
    w, x = 0.4, np.arange(len(cats))

    width_cluster = 0.7
    width_bar = width_cluster / 3

    index = 0

    for model in ["gemma4:latest", "llama3.2:latest", "qwen3.5:latest"]:
        percents = []

        for config in ["control", "pre-prompt"]:
            percentage = 0
            for domain in ["biology", "geography", "history"]:
                
                for trial in range(1, 11):
                    percentage += data[model][config][domain][trial]
                    
            percents.append(percentage)
            print(f"""
                Percentage of correctly identified responses for:\n\t
                model: {model} config: {config} result: {percentage} out of 30 correct 
            """)

        x_positions = x+(width_bar*index)-width_cluster/2
        ax.bar(x_positions, percents, width=width_bar, label=model)

        index += 1

    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.set_ylim([0,30])
    ax.set_ylabel('Trials')
    ax.set_xlabel('Testing configuration')
    ax.set_title('Amount of correctly identified contradictions')
    ax.legend()

    plt.show()

# with open('human_scored.json', 'r') as fp:
#     data = json.load(fp)
# human_scored = score_results_human(data, "qwen3.5:latest")

# with open('human_scored.json', 'w') as fp:
#     json.dump(data, fp)

with open('analysis/human_scored.json', 'r') as fp:
    data = json.load(fp)

generate_plot(data)