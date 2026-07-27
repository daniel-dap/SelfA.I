import json
import os
import random
import signal
import sys
from typing import Literal

import requests

OPTIONS = [{"complete": "--help", "simplified": "-h", "name": "help", "explanation": "prints this message"}, {"complete": "--verbose", "simplified": "-v", "name": "verbose", "explanation": "activates verbose mode that prints more details during execution"}, {"complete": "--save-history", "simplified": "-s", "name": "save history", "explanation": "saves the conversation histories to history1.json and history2.json"}]
HELP_MESSAGE = f"SelfA.I: a program designed to make an AI model converse with itself.\nUsage: {sys.argv[0]} [OPTIONS] API MODEL TURNS_NUM INITIAL_MESSAGE [SYSTEM_PROMPT 1] [SYSTEM_PROMPT 2]\n\nOptions:\n{'\n'.join(f'\t{o["name"].capitalize()}: can be enabled with {o["complete"]} or {o["simplified"]}; {o["explanation"]}.' for o in OPTIONS)}\n\nArgs:\n\tAPI: API endpoint URL that will be used; must start with \"http://\" or \"https://\".\n\tMODEL: model to specify for the API.\n\tTURNS_NUM: number of turns that will run. In a turn, Model 2 and Model 1 talk to each other.\n\tINITIAL_MESSAGE: first message (tip: use it to define a main topic, like a human starting a conversation topic; examples: \"Hey, what's up? Let's talk about chess.\"); model 1 will say it to initiate the conversation.\n\t\n\nTo configure API keys, please create a file named \".api_key\" in the script's directory and put your raw key inside it.\nMalformed arguments will not be corrected; please be careful with your arguments and use quotes.\nADVICE: \"Model 1\" and \"Model 2\" are just personas/aliases, not really different models.\nThings like \"-hvs\" don't work, sorry.\nFor better results, don't use things like \"You is X.\" in system prompts; instead, use \"Assistant is X.\" Refer to the assistant in the third person."

def quitprog(sig = 0, frame = None, verbose = False) -> None: #generic function to quit the program
    print(f"\n\033[0mQuitting{' successfully' if sig == 0 else (f' with signal {sig}' if verbose else '')}...")
    sys.exit(sig)

def detectopt(index: int, argv: list[str]) -> tuple[Literal["simplified", "complete"], int] | None: #function to make my life (and maybe other devs'/modders' lives) easier
    if OPTIONS[index]["simplified"] in argv:
        return "simplified", argv.index(OPTIONS[index]["simplified"])
    elif OPTIONS[index]["complete"] in argv:
        return "complete", argv.index(OPTIONS[index]["complete"])
    else:
        return None

def arg_parser(argv: list[str]) -> dict: #kind of main arg "lexer"
    options = {
        "verbose":  False,
        "savehistory": False,
        "API": None,
        "MODEL": None,
        "TURNS_NUM": None,
        "INITIAL_MESSAGE": None,
        "KEY": None,
        "SYSTEM_PROMPT1": None,
        "SYSTEM_PROMPT2": None
    } #final dict to return

    if len(argv) == 0: #fallback to runs without args
        print("No arguments were passed...\nPrinting help message.\n")
        print(HELP_MESSAGE)
        quitprog()

    if o := detectopt(0, argv): #help option fallback
        argv.pop(o[1])
        print(HELP_MESSAGE)
        quitprog(verbose=(detectopt(1, argv)))

    if o := detectopt(1, argv): #verbose mode detection
        argv.pop(o[1])
        options["verbose"] = True

    if o := detectopt(2, argv): #save history option detection
        argv.pop(o[1])
        options["savehistory"] = True

    argv = [arg for arg in argv if arg not in ["-v", "--verbose", "-h", "--help", "-s", "--save-history"]] #clean duplicated options

    if len(argv) < 4: #missing args detection
        print(f"Missing {4-len(argv)} mandatory arguments.")
        quitprog(4096, verbose=options["verbose"])

    options["API"] = argv[0]
    options["MODEL"] = argv[1]
    options["TURNS_NUM"] = argv[2]
    options["INITIAL_MESSAGE"] = argv[3]

    if len(argv) == 6: #system prompts detection
        options["SYSTEM_PROMPT1"] = argv[4]
        options["SYSTEM_PROMPT2"] = argv[5]
    elif len(argv) == 5:
        options["SYSTEM_PROMPT1"] = argv[4]
    elif len(argv) >= 7:
        print(f"Unexpected arguments: {','.join(argv[6::])}.")
        quitprog(4097, verbose=options["verbose"])

    if os.path.exists(".api_key"): #API key detection
        with open(".api_key", "r") as f:
            options["KEY"] = f.read()

    return options

def process_processed_args_and_validate(processed_args: dict[str, str]) -> dict: #self-explanatory name
    if not (processed_args["API"].startswith("http://") or processed_args["API"].startswith("https://")):
        print(f"API URL \"{processed_args['API']}\" doesn't start with \"https://\" or \"http://\".")
        quitprog(4098, verbose=processed_args["verbose"])
    try:
        processed_args["TURNS_NUM"] = int(processed_args["TURNS_NUM"])
        if processed_args["TURNS_NUM"] < 0:
            print(f"The number of turns \"{processed_args['TURNS_NUM']}\" can't be a negative number.")
            quitprog(4099, verbose=processed_args["verbose"])
    except ValueError:
        print(f"The number of turns \"{processed_args['TURNS_NUM']}\" isn't a number.")
        quitprog(4100, verbose=processed_args["verbose"])
    return processed_args    

def generate_response(api: str, history: list[dict[str, str]], model: str, key: str, verbose: bool) -> str: #another function to make my life easier
    headers = {
        **({"Authorization": f"Bearer {key}"} if key else {}),
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": history,
        "stream": True
    }

    complete_response = ""
    usage_data = None

    try:
        response = requests.post(api, headers=headers, json=payload, stream=True)

        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue

            decoded_line = line.decode("utf-8")

            if decoded_line.startswith("data: "):
                chunk_data = decoded_line[6:]

                if chunk_data == "[DONE]":
                    if verbose:
                        print("\033[0m\n[DONE] marker received.")
                    break

                try:
                    chunk_json = json.loads(chunk_data)

                    if "usage" in chunk_json:
                        usage_data = chunk_json["usage"]

                    if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                        delta = chunk_json["choices"][0].get("delta", {})
                        if "content" in delta:
                            dataslice = delta["content"]
                            complete_response += dataslice

                            print(dataslice, end="", flush=True)

                except json.JSONDecodeError:
                    continue
    except requests.exceptions.RequestException as e:
        print(f"\033[0m\nAPI error {e}")
        if verbose and hasattr(e, 'response') and e.response is not None:
            print(f"Response detail: {e.response.text}")
        if verbose:
            print("Treating response as an empty string.")
            return ""

    print()

    if verbose and usage_data:
            print(f"\033[0mUsed tokens (input/output/total): {usage_data.get('prompt_tokens')} / {usage_data.get('completion_tokens')} / {usage_data.get('total_tokens')}")

    return complete_response
        
signal.signal(signal.SIGINT, quitprog) #telling signal lib which handler to use

#PROCESS ARGS
processed_args = arg_parser(sys.argv[1::])
processed_args = process_processed_args_and_validate(processed_args)

colors = [tuple(random.getrandbits(8) for _ in range(3)) for _ in range(4)]

model1 = []
model2 = []

if processed_args["SYSTEM_PROMPT1"]:
    model1.append({"role": "system", "content": processed_args["SYSTEM_PROMPT1"]})
    print(f"\033[38;2;{colors[0][0]};{colors[0][1]};{colors[0][2]}mSystem (to Model 1): {processed_args['SYSTEM_PROMPT1']}\033[0m")

if processed_args["SYSTEM_PROMPT2"]:
    model2.append({"role": "system", "content": processed_args["SYSTEM_PROMPT2"]})
    print(f"\033[38;2;{colors[1][0]};{colors[1][1]};{colors[1][2]}mSystem (to Model 2): {processed_args['SYSTEM_PROMPT2']}\033[0m")

print(f"\033[38;2;{colors[2][0]};{colors[2][1]};{colors[2][2]}mModel 1: {processed_args['INITIAL_MESSAGE'] if processed_args['INITIAL_MESSAGE'] else 'Hello! How are you? Let\'s talk about AIs.'}\033[0m")
model1.append({"role": "assistant", "content": (processed_args["INITIAL_MESSAGE"] if processed_args["INITIAL_MESSAGE"] else "Hello! How are you? Let's talk about AIs.")})
model2.append({"role": "user", "content": (processed_args["INITIAL_MESSAGE"] if processed_args["INITIAL_MESSAGE"] else "Hello! How are you? Let's talk about AIs.")})

print()

#main loop
for i in range(processed_args["TURNS_NUM"]):
    print(f"Turn {i+1}.")
    print(f"\033[38;2;{colors[3][0]};{colors[3][1]};{colors[2][2]}mModel 2: ", end="")
    response = generate_response(processed_args["API"], model2, processed_args["MODEL"], processed_args["KEY"], processed_args["verbose"])
    print("\033[0m", end="")

    model2.append({"role": "assistant", "content": response})
    model1.append({"role": "user", "content": response})

    print(f"\033[38;2;{colors[2][0]};{colors[2][1]};{colors[3][2]}mModel 1: ", end="")
    response = generate_response(processed_args["API"], model1, processed_args["MODEL"], processed_args["KEY"], processed_args["verbose"])
    print("\033[0m", end="")

    model1.append({"role": "assistant", "content": response})
    model2.append({"role": "user", "content": response})

if processed_args["savehistory"]:
    if not os.path.exists("history1.json") or (os.path.exists("history1.json") and (input("File history1.json already exists; do you want to overwrite it? (Y/n): ").lower() in ["y", ""])):
        with open("history1.json", "w") as f:
            json.dump(model1, f)
    if not os.path.exists("history2.json") or (os.path.exists("history2.json") and (input("File history2.json already exists; do you want to overwrite it? (Y/n): ").lower() in ["y", ""])):
        with open("history2.json", "w") as f:
            json.dump(model2, f)