import json
import pathlib
import datetime
import urllib.request
import urllib.error
import hashlib
import typing
import dataclasses

from bs4 import BeautifulSoup

def _request_with_retries(request: urllib.request.Request, retries: int):
    """
    Tries to request with retries, but returns
    either None or actual response object 
    without returning raised errors
    """
    i = 0
    data = None
    while i < retries:
        try:
            with urllib.request.urlopen(request) as req:
                data = req.read().decode("utf-8")
        except urllib.error.HTTPError:
            i += 1
            continue
        else:
            data = data
            break
    return data

def parse_wiki(wikipedia_links: dict[str, str], output_path: pathlib.Path, headers: dict, is_compressed: bool, retries: int = 5):
    """
    Parse tabular data from wikipedia links related
    to mobile devices and operating systems. For now,
    we don't parse information about "mobile_based_os"
    and "android_custom_distributions". Also, we probably
    need to use MediaWiki API instead of raw wiki links.
    """

    wiki_link_template = "https://en.wikipedia.org/w/index.php?title={title}&oldid={oldid}"
    export_time = datetime.datetime.now(tz=datetime.UTC)
    export_time_str = export_time.strftime("%Y-%m-%d-%H-%M-%S")
    export_filename = f"wiki_export_{export_time_str}.json"
    output_path.mkdir(exist_ok=True)

    parsed_data = []
    for link in wikipedia_links:
        current_link = wiki_link_template.format(title=link["title"], oldid=link["oldid"])
        request = urllib.request.Request(url=current_link, headers=headers)
        response = _request_with_retries(request=request, retries=retries) # @TODO: handle if empty then goes to other step and report about errors
        if link["type"] == "android_compatible_smartphones":
            smartphones = []
            parser = BeautifulSoup(response, "lxml")
            rows = parser.select("table.wikitable > tbody > tr:not(:first-child)")
            for row in rows: # @TODO: :nth-last-child()?
                cells = [cell.text.strip() for cell in row.find_all(["th", "td"])]
                smartphone = {
                    "model": cells[0],
                    "developer": cells[1],
                    "release_date": cells[2],
                    "android_version": cells[3]
                }
                smartphones.append(smartphone)
            parsed_data.append({"type": link["type"], "source": current_link, "data": smartphones}) # @TODO: "sha256": hashlib.sha256().hexdigest() for data to check integrity?
        elif link["type"] == "android_versions":
            version_statuses = {
                "unsupported": "swatch-unsupported",
                "supported": "swatch-maintained",
                "latest": "swatch-latest",
                "preview": "swatch-preview",
            }
            versions = []
            parser = BeautifulSoup(response, "lxml")

            # @TODO: we need to parse all page with minor versions, because single table with major versions is not enough
            rows = parser.select("table.wikitable:first-of-type > tbody > tr:not(:first-child):not(:last-child)")

            extended_cells: list[dict[str, int]] = []
            for i_r, row in enumerate(rows):
                cells = [cell for cell in row.find_all(["th", "td"])]

                extended_cells = [c for c in extended_cells if c["rowspan"] > 1]
                for entry in sorted(extended_cells, key=lambda x: x["cell_id"]):
                    entry["rowspan"] -= 1 # cell["rowspan"] - 1 >= 0: cell["rowspan"] -= 1 ???
                    cells.insert(entry["cell_id"], entry["cell"])

                # @TODO: simplify this one or add explanations
                for i_c, cell in enumerate(cells):
                    rowspan_val = cell.get("rowspan")
                    if rowspan_val:
                        rowspan_int = int(rowspan_val)
                        if rowspan_int > 1:
                            if not any(c['cell'] == cell for c in extended_cells):
                                extended_cells.append({
                                    "cell_id": i_c,
                                    "rowspan": rowspan_int,
                                    "cell": cell
                                })

                status = "unknown"
                for key, value in version_statuses.items():
                    if any([value in c for c in cells[2]["class"]]):
                        status = key
                        break
                
                version = {
                    "name": cells[0].text.strip(),
                    "version": cells[2].text.strip(),
                    "status": status,
                    "api_level": cells[3].text.strip(),
                    "release_date": cells[4].text.strip(),
                    "latest_security_patch_date": cells[5].text.strip(),
                    "latest_google_play_date_release": cells[6].text.strip(), # @TODO: decompose to two seperate columns
                }
                versions.append(version)
            parsed_data.append({"type": link["type"], "source": current_link, "data": versions})
        else:
            msg = f"Not implemented for provided type: {link}"
            print(msg)

    with open(str(output_path / export_filename), "w") as file:
        parsed_data = json.dumps(parsed_data, ensure_ascii=False, indent = None if is_compressed else 4) # @TODO: compression with gzip
        file.write(parsed_data)

@dataclasses.dataclass
class Config:
    HEADERS: dict
    WIKIPEDIA_LINKS: list[dict]
    BASE_DIRECTORY: pathlib.Path = pathlib.Path(__file__).parent.parent
    OUTPUT_DIRECTORY: pathlib.Path = BASE_DIRECTORY / "data"
    RETRIES: int = 5
    IS_COMPRESSED: bool = True

    @classmethod
    def load_from_json(cls, config_path: pathlib.Path = None) -> typing.Self:
        config_path = config_path if config_path is not None else cls.BASE_DIRECTORY / "config.json"
        try:
            with open(str(config_path), "r") as file:
                config_loaded = json.load(file)
        except OSError as e:
            error = f"Cannot open file with necessary non-default and default data due to: {e}"
            raise Exception(error)
        else:
            config = {}
            for defined_field in dataclasses.fields(cls):
                for key, value in config_loaded.items():
                    if key == defined_field.name.lower():
                        # @TODO: optionally validate value by types specified
                        # and validation rules attached to fields
                        config[f"{defined_field.name}"] = value
            # @TODO: if not enought data then raise error
            # because non-default fields still needed
            return cls(**config)

def main():
    """
    This scripts is intended to gather data about their Android versions
    with related smartphones in order to find out amount of phones
    that have Android >= 5.0, >=6.0, >=7.0 and distribution of versions
    due to limited compatability support in Termux. Potentially, we 
    can extend such logic for other categories of devices and OS
    (e.g., iOS / iPhones, linux phones, IoT devices, etc.).
    """

    config = Config.load_from_json()
    config.OUTPUT_DIRECTORY.mkdir(exist_ok=True)
    parse_wiki(
        wikipedia_links=config.WIKIPEDIA_LINKS,
        output_path=config.OUTPUT_DIRECTORY,
        retries=config.RETRIES,
        headers=config.HEADERS,
        is_compressed=config.IS_COMPRESSED
    )
    
if __name__ == "__main__":
    main()
