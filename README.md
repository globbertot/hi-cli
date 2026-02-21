# hi-cli
A hianime.to cli/tui to watch and manage anime locally from your terminal.


## Usage
```
usage: hi-cli [-h] [-v] [-s] [-i]

A hianime.to cli/tui to watch and manage anime locally from your terminal.

options:
  -h, --help         show this help message and exit
  -v, --version
  -s, --search
  -i, --interactive
```

## Installation (source)
You can install hi-cli with the following commands
Note that this assumes you have installed UV [instructions](https://github.com/astral-sh/uv)
```bash
git clone https://github.com/globbertot/hi-cli.git
cd hi-cli
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python main.py
```

