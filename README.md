# iccsfai-2026_research-paper
Research paper for ICCSDFAI 2026 Conference

## Description
- Based on "IEEE Conference Template" and [ICCSDFAI 2026 requirements](https://iccsdfai.org/author-guidelines).
- Conference track: "Blockchain and AI for Data Integrity and Secure Transactions".
- It is a partial white paper and research paper for "open-unit" which describes possibility to use edge devices (like smartphones or embedded hardware) for general-purpose computing (inference of small models, training, annotating/labeling data, storing data, and so on).
- MISC.md contains hardware side, AI-specific optimization, and other unused details. After our initial review, we chose to prioritize on distributed networks and specific use cases, as the previous draft was becoming overly broad.
- The .odt version of the paper includes:
    - @NOTEs to mark relevant but unofficial materials, as well as personal comments from authors intended for readers.
    - @TODOs as unfinished tasks to complete after initial review.

## Practical experiments
The source materials for experiments are located in /practice. All scripts and resources are only prototypes and not production-ready solutions for regular use, nor do they fully reflect latest capabilities of fields or toolkits discussed.

The dataset that was used in analysis is located in `/practice/data/wiki_export_year-month-day-hour-minute-second.json`:
- name `wiki_export_2026-04-15-19-08-20.json`
- sha256 `1351f2b9dd6811bdd391fbc3146015cb6c7e6dd36c15fa29ec8b39f8707b4ec9`

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
