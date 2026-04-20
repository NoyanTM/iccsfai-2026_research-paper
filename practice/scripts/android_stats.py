import pathlib
import json
import re
import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from utils import match_version, normalize_version, parse_version

def analysis(**kwargs):
    """Superficial analysis on columns/rows of df_phones and df_versions"""
    df_phones, df_versions = kwargs.get("df_phones"), kwargs.get("df_versions")
    
    print("analysis_for_android_compatible_smartphones", "-" * 100)
    print(df_phones.head(10), "\n", df_phones.tail(10), "\n", df_phones.columns, "\n", df_phones.dtypes, "\n", df_phones.describe(), "\n")
    print(df_phones["developer"].unique(), "\n", df_phones[df_phones["model"].duplicated(keep="last")])
    
    print("analysis_for_well_known_android_versions", "-" * 100)
    print(df_versions.head(10), "\n", df_versions.tail(10), "\n", df_versions.columns, "\n", df_versions.dtypes, "\n", df_versions.describe(), "\n")
    print(df_versions["status"].unique(), df_versions["version"].to_list())
    print(df_versions[(df_versions["latest_security_patch_date"] == "—N/a") & (df_versions["latest_google_play_date_release"] == "—N/a")])
    print(df_versions["version"].to_list(), "\n",
          df_versions["name"].to_list(), "\n",
          df_versions["latest_security_patch_date"].to_list(), "\n",
          df_versions["latest_google_play_date_release"].to_list())

def cleanup(**kwargs) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalization, transformations, and cleanup operations on df_phones and df_versions"""
    df_phones: pd.DataFrame = kwargs.get("df_phones").copy(deep=True)
    df_versions: pd.DataFrame = kwargs.get("df_versions").copy(deep=True)

    # drop duplicates in df_phones[model], because we can't handle cases
    # when smartphone has multiple base minimal versions of android, but it
    # should be mitigated like "phone:list[version]" or considering major/major.minor version
    df_phones = df_phones.drop_duplicates(subset=["model"]).reset_index(drop=True)

    versions_pattern = r"(?P<version>\d+(?:\.\d+)?(?:\.\d+)?)"
    os_name_pattern = r"(?P<os_name>Android)"
    df_versions["latest_security_patch_date"] = df_versions["latest_security_patch_date"].replace("—N/a", np.nan)
    df_versions["latest_google_play_date_release"] = df_versions["latest_google_play_date_release"].replace("—N/a", np.nan)
    android_version_pattern = fr"^{os_name_pattern}\s{versions_pattern}"
    df_phones["android_version"] = df_phones["android_version"].str.extract(android_version_pattern)["version"]
    df_versions["version_range"] = df_versions["version"].str.extract(versions_pattern)
    # print(df_phones["android_version"].unique(), df_versions["version_range"].to_list())

    # drop duplicates in df_versions["version"] due to 4.4 and 4.4W duplicate
    # and weird/inconsistent android versioning that includes letters, but maybe we 
    # can merge them or find other better way to handle it
    # print(df_versions["version_range"], df_phones["android_version"].unique())
    # print(df_versions[df_versions["version_range"] == "4.4"])
    df_versions = df_versions.drop_duplicates(subset=["version_range"]).reset_index(drop=True)
    # print(df_versions["version_range"].unique())
    
    # normalize versions, convert pd.nan to 0.0.0 version, and sort by versions
    # sorted(key=lambda s: list(map(int, s.split("."))))
    df_versions["version_range"] = df_versions["version_range"].apply(normalize_version, 0)
    df_phones["android_version"] = df_phones["android_version"].fillna("0.0.0")
    df_phones["android_version"] = df_phones["android_version"].apply(normalize_version, 0)

    # convert df_versions to range(start_version, end_version)
    df_versions["next_version"] = df_versions["version_range"].shift(-1)
    def increment_major(version_str):
        major = int(version_str.split('.')[0])
        return f"{major + 1}.0.0"
    last_idx = df_versions.index[-1]
    last_version = df_versions.at[last_idx, "version_range"]
    df_versions.at[last_idx, "next_version"] = increment_major(last_version)
    df_versions["version_ranges"] = list(zip(df_versions["version_range"], df_versions["next_version"]))
    df_versions = df_versions.drop(columns=["next_version"])

    # convert dates to datetime type using regex
    # because .strptime(x, "%Y/%m") is not enough for certain cases
    # but probably can use pd.to_datetime?
    def extract_datetime(value: str):
        release_date = re.compile(r"(?P<quarter>Q[1-4]\s)?(?P<year>\d{4})(/(?P<month>\d{1,2}))?", flags=re.IGNORECASE)
        result = re.search(release_date, value)
        if not result:
            # change year to 1970 as stub
            # for not matching data
            return datetime.datetime(year=1970, month=1, day=1)
        
        if result.group("quarter") and result.group("year"):
            # handle quarter and year
            months = list(range(1, 12 + 1))
            quarters = [months[i: i + 3] for i in range(0, 12, 3)]
            month = quarters[int(result.group("quarter")[1])][0]
            date = datetime.datetime(year=int(result.group("year")), month=int(month), day=1)
        elif result.group("year") and result.group("month"):
            # handle year/month (2025/04, 2026/4, 2025/12, ...)
            year = result.group("year")
            month = result.group("month")
            if month[0] == "0" and len(month) == 2: month = month[1]
            date = datetime.datetime(year=int(year), month=int(month), day=1)
        else:
            date = datetime.datetime(year=int(result.group("year")), month=1, day=1)
        return date
    df_phones["release_date"] = df_phones["release_date"].apply(extract_datetime)

    # convert dates column in df_versions if possible
    df_versions["latest_security_patch_date"] = df_versions["latest_security_patch_date"].apply(
        lambda x: datetime.datetime.strptime(x, "%B %Y") if isinstance(x, str) else datetime.datetime(year=1970, month=1, day=1)
    )
    df_versions = df_versions.drop(columns=["latest_google_play_date_release"])
    
    # map columns from df_version to df_phones depending on version
    # by using match_version function "version_ranges" from df_version
    ranges_list = df_versions["version_ranges"].tolist()
    df_phones["matched_range"] = df_phones["android_version"].apply(
        lambda x: match_version(x, ranges_list)
    )
    cols_to_map = ["version_ranges", "name", "api_level", "status", "latest_security_patch_date"]
    df_phones = df_phones.merge(
        df_versions[cols_to_map],
        left_on="matched_range",
        right_on="version_ranges",
        how="left"
    )
    df_phones = df_phones.drop(columns=["matched_range"])

    return df_phones, df_versions

def plot_android_versions_groups_on_devices(output_path: pathlib.Path, **kwargs):
    """
    Group/categorize devices by version groups
    (<5.0.0; >=5.0.0 and <7.0.0; >=7.0.0)
    and render them as pie chart figure,
    excluding 0.0.0 versions
    """
    df: pd.DataFrame = kwargs.get("df_phones").copy()

    original_df_len = len(df)
    exclude = (df["android_version"] == "0.0.0")
    df_excluded = df[exclude]
    df = df[~exclude]

    def categorize(v_str):
        v = parse_version(v_str)
        if v < (5, 0, 0): return "Incompatible (<5.0.0)"
        elif (5, 0, 0) <= v < (7, 0, 0): return "Deprecated (>=5.0.0 and <7.0.0)"
        elif v >= (7, 0, 0): return "Compatible (>=7.0.0)"
    
    df["comparison_group"] = df["android_version"].apply(categorize)
    version_counts = df["comparison_group"].value_counts()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.pie(
        version_counts, 
        labels=version_counts.index, 
        autopct="%1.1f%%", 
        startangle=65,
        colors=["tab:green", "tab:red", "tab:blue"],
        wedgeprops={"edgecolor": "white", "alpha": 0.7},
    )
    ax.set_title(f"Compatibility with Termux depending on Android Versions (% of Smartphones)", pad=20)

    ax.axis('equal') 
    ax.legend(
        title="Compatibility groups:",
        loc="upper left",
        fontsize="small",
        alignment="left",
    )
    stats_text = (
        f"- Total smartphones: {original_df_len}\n"
        f"- Excluded ones: {len(df_excluded)}\n"
        f"- Represented ones: {len(df)}"
    )
    ax.text(-3.05, 0.47, stats_text, ha='left', va='top', fontsize=9)
    fig.tight_layout()
    fig.savefig(str(output_path / "android_3_groups_comparison.pdf"), format="pdf")

def plot_android_major_versions_on_devices(output_path: pathlib.Path, **kwargs):
    """
    Amount of devices per major version in bar
    plot figure, excluding 0.0.0 versions
    """

    df: pd.DataFrame = kwargs.get("df_phones").copy()

    original_df_len = len(df)
    exclude = (df["android_version"] == "0.0.0")
    df_excluded = df[exclude]
    df = df[~exclude]

    df['major_version'] = df['android_version'].apply(
        lambda x: int(str(x).split(".")[0])
    )
    version_counts = df['major_version'].value_counts().sort_index()
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.grid(visible=True, linestyle="--", alpha=0.3)
    bars = ax.bar(
        version_counts.index.astype(str), 
        version_counts.values, 
        color="tab:blue", 
        edgecolor='#333333',
        linewidth=1,
        alpha=0.7
    )
    max_height = version_counts.max()
    ax.set_ylim(0, max_height * 1.15) 
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., 
            height + (max_height * 0.01),
            f'{int(height)}', 
            ha='center', 
            va='bottom', 
            fontsize=10,
        )
    ax.set_title(f"Major Android Versions across Smartphones", pad=20)
    ax.set_xlabel("Major Version")
    ax.set_ylabel("Amount of Smartphones")
    plt.xticks(rotation=0)
    fig.tight_layout()
    ax.set_axisbelow(True)
    stats_text = (
        f"- Total smartphones: {original_df_len}\n"
        f"- Excluded ones: {len(df_excluded)}\n"
        f"- Represented ones: {len(df)}"
    )
    ax.text(
        15.0, 300, 
        stats_text, 
        ha='right', 
        va='top', 
        fontsize=9,
    )
    fig.savefig(str(output_path / "major_version_distribution.pdf"), format="pdf")

# @TODO: render as log scale due to extreme values difference
def plot_android_versions_statuses_on_devices(output_path: pathlib.Path, **kwargs):
    """
    Render versions statuses of Android versions on devices
    in order to find amount of devices that are under security risks
    due to absence of support and patches
    """
    df: pd.DataFrame = kwargs.get("df_phones").copy()

    status_counts = df["status"].fillna("unknown").value_counts().sort_index()
    print(status_counts)
    fig, ax = plt.subplots(figsize=(10, 4))
    bars = ax.bar(
        status_counts.index.astype(str), 
        status_counts.values, 
        color="tab:blue", 
        edgecolor='#333333',
        linewidth=1,
        alpha=0.7
    )
    max_height = status_counts.max()
    ax.set_ylim(0, max_height * 1.15) 
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., 
            height + (max_height * 0.01),
            f'{int(height)}', 
            ha='center', 
            va='bottom', 
            fontsize=10,
        )
    stats_text = f"Total represented smartphones: {len(df)}"
    ax.text(0.90, 2070, stats_text, ha='left', va='top', fontsize=9)
    ax.set_title("Android Versions Statuses across Smartphones", pad=20)
    plt.xlabel("Version Status")
    plt.ylabel("Amount of Smartphones")
    plt.legend(title="unknown - not found status\nlatest - newest versions\nsupported - on-going maintenance\nunsupported - end-of-life versions", loc="upper left")
    fig.tight_layout()
    fig.savefig(str(output_path / "phone_android_version_status_distribution.pdf"), format="pdf")

def plot_android_by_latest_patch_and_release_dates(output_path: pathlib.Path, **kwargs):
    df: pd.DataFrame = kwargs.get("df_phones").copy(deep=True)

    phone_releases_df = df.copy(deep=True)
    security_releases_df = df.copy(deep=True)

    phone_releases_condition = (phone_releases_df["release_date"] == "1970-01-01")
    represented_phone_releases_df = df.copy(deep=True)
    represented_phone_releases_df = represented_phone_releases_df[~phone_releases_condition]

    security_releases_condition = (security_releases_df["latest_security_patch_date"] == "1970-01-01")
    represented_security_releases_df = df.copy(deep=True)
    represented_security_releases_df = represented_security_releases_df[~security_releases_condition]

    yearly_counts = represented_phone_releases_df["release_date"].dt.year.value_counts().sort_index()
    years_diff = (datetime.datetime.now() - represented_security_releases_df["latest_security_patch_date"]).dt.days / 365.25
    bins = [0, 1, 3, 5, np.inf]
    labels = ["< 1 year", "1-3 years", "3-5 years", "> 5 years"]
    counts = pd.cut(years_diff, bins=bins, labels=labels).value_counts().reindex(labels)

    print(counts)

    plot_1_stats_text = (
        f"- Total smartphones: {len(df)}\n"
        f"- Excluded ones: {len(df[phone_releases_condition])}\n"
        f"- Represented ones: {len(represented_phone_releases_df)}"
    )
    plot_2_stats_text = (
        f"- Total smartphones: {len(df)}\n"
        f"- Excluded ones: {len(df[security_releases_condition])}\n"
        f"- Represented ones: {len(represented_security_releases_df)}"
    )

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(yearly_counts.index, yearly_counts.values, marker="o", linestyle="-")
    axes[0].set(    
        title="Smartphones Released per Year",
        xlabel="Year",
        ylabel="Amount of Smartphones",
        xticks=yearly_counts.index
    )
    axes[0].yaxis.set_major_locator(ticker.MultipleLocator(20))
    axes[0].grid(True, linestyle='--', alpha=0.3)
    axes[0].text(
        0.43, 0.95, plot_1_stats_text, transform=axes[0].transAxes, ha='right', va='top',
        fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.5)
    )
    axes[0].tick_params("x", rotation=45)
    axes[1].bar(counts.index, counts.values, color="tab:blue", edgecolor='#333333', linewidth=1, alpha=0.7)
    axes[1].yaxis.set_major_locator(ticker.MultipleLocator(40))
    axes[1].set(
        title='Smartphones by Latest Android Security Patch',
        xlabel="Age of Latest Security Patch",
        ylabel="Amount of Smartphones"
    )
    axes[1].grid(True, linestyle='--', alpha=0.3)
    axes[1].text(
        0.43, 0.95, plot_2_stats_text, transform=axes[1].transAxes, ha='right', va='top',
        fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.5)
    )
    fig.tight_layout()
    fig.savefig(str(output_path / "android_latest_patches_and_smartphones_release_dates.pdf"), format="pdf")

# @TODO: convert analysis into jupyter/ipython or use pprint
# for convenience for code snippets for analysis process
def main():
    """
    Trying to represent/identity that old Android devices are under risk
    of old firmware/software state due to unpatched vulnerabilities and security
    issues. So it is hard or impossible to update them without rooting or
    installing other OS (e.g., Ubuntu Touch or custom builds). Therefore, it 
    is only applicable in air-gapped and local environments in the seperate network
    without being exposed to the internet.
    """

    BASE_PATH = pathlib.Path(__file__).parent.parent
    DATA_PATH = BASE_PATH / "data"
    IMAGES_PATH = BASE_PATH / "images" 
    EXPORT_FILE_PATH = sorted(list(DATA_PATH.glob("wiki_export_*.json")))[-1]

    with open(EXPORT_FILE_PATH, "r") as file:
        export_data = json.load(file)
    
    for data in export_data:
        if data["type"] == "android_compatible_smartphones": df_phones = pd.DataFrame(data["data"])
        if data["type"] == "android_versions": df_versions = pd.DataFrame(data["data"])

    analysis(df_phones=df_phones, df_versions=df_versions)

    # filled pd.nan and unparsable data with empty values
    # like 0.0.0 versions and 1970 dates, but during visualization
    # and analysis they are explicitly omitted if needed
    df_phones, df_versions = cleanup(df_phones=df_phones, df_versions=df_versions)
    print(df_phones)

    # @TODO: reuse rendering and general stylesheets for plots instead of duplicating
    # @TODO: find way to render text relative to specific components instead of pixel-based
    plot_android_versions_groups_on_devices(IMAGES_PATH, df_phones=df_phones)
    plot_android_major_versions_on_devices(IMAGES_PATH, df_phones=df_phones)
    plot_android_versions_statuses_on_devices(IMAGES_PATH, df_phones=df_phones)
    plot_android_by_latest_patch_and_release_dates(IMAGES_PATH, df_phones=df_phones)

if __name__ == "__main__":
    main()
