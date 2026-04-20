# iccsfai-2026_research-paper
Research paper for ICCSDFAI 2026 Conference

## Description
- Based on "IEEE Conference Template" and [ICCSDFAI 2026 requirements](https://iccsdfai.org/author-guidelines).
- Conference track: "Blockchain and AI for Data Integrity and Secure Transactions".
- It is a partial white paper and research paper for "open-unit" which describes possibility to use edge devices (like smartphones or embedded hardware) for general-purpose computing (inference of small models, training, annotating/labeling data, storing data, and so on).

## Practical experiments
The source materials for experiments are located in /practice. All scripts and resources are only prototypes and not production-ready solutions for regular use, nor do they fully reflect latest capabilities of fields or toolkits discussed.

### Gathering data about Android compatible devices
Setup environment and install necessary packages:
```sh
cd ./practice
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run web parsing/scraping and statistical analysis on that:
```sh
# change config.json or source code to edit parameters of web scrapper
# (not implemented modifications of paths for config.json and /data in other scripts)
python3 ./scripts/wiki_parser.py

# analysis based on gathered data
python3 ./scripts/android_stats.py

# simples tests for version-related algorithms and utilities
python3 -m unittest ./scripts/tests.py
```
