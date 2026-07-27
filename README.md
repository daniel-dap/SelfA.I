# SelfA.I
A lightweight command-line utility designed to make an AI model converse with itself.

## Requirements
- Python 3.12 or later
- The requests library

## Installation
- Install the `requests` library for Python if it is not already installed.
- Download selfai.py or clone the repository.

``` bash
# Example using wget
$ wget https://raw.githubusercontent.com/daniel-dap/SelfA.I/main/selfai.py

# Alternatively, clone the entire repository
$ git clone https://github.com/daniel-dap/SelfA.I.git
```

# Usage
You can use options --verbose (or -v), --save-history (or -s) and/or --help (or -h).
The arguments API, MODEL, TURNS_NUM and INITIAL_MESSAGE are mandatory. `SYSTEM_PROMPT 1` and `SYSTEM_PROMPT 2` are optional.
If you want to use API keys, create a file named .api_key in the same directory as selfai.py and put your raw API key inside it.
``` bash
# Example using gemma3, OpenAI API, 5 turns and --verbose
$ cat .api_key
ExampleAPIkey

$ python3 selfai.py --verbose "https://api.openai.com/v1/chat/completions" "gpt-5.6" 5 "Hello, how are you? I like trains." "Assistant loves trains." "Assistant hates trains."
System (to Model 1): Assistant loves trains.
System (to Model 2): Assistant hates trains.
Model 1: Hello, how are you? I like trains.

Turn 1.
Model 2: How dare you?!
...
```

# Warnings
"Model 1" and "Model 2" are just personas/aliases, not really different models.
For better results, don't use things like \"You is X.\" in your system prompts; instead, use \"Assistant is X.\" Refer to the assistant in the third person.
Things like \"-hvs\" don't work.
Malformed arguments will not be corrected; please be careful with your arguments and use quotes when needed.