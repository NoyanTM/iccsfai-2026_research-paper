import random

def normalize_version(version: str) -> str:
    """
    Converts version number to normalized/absolute format
    similar to semver with "major.minor.patch" specifiers
    """
    specifiers = version.split(".")
    if len(specifiers) < 3:
        if len(specifiers) == 2:
            specifiers.append("0")
        if len(specifiers) == 1:
            specifiers.extend(["0", "0"])
    return ".".join(specifiers)

# @TODO: generate_version like to semver and specified requirements or 
# with random_seed instead of having logic for generating versions inside tests.py
# and generating multiple versions by specifying their amount
# and refactoring because it is too raw for now
def generate_version(major_versions: list, minor_versions: list = None, patch_versions: list = None, is_normalized: bool = False):
    major_specifier = random.randint(major_versions[0], major_versions[1])
    minor_specifier = random.randint(minor_versions[0], minor_versions[1]) if minor_versions else (0 if is_normalized else None)
    patch_specifier = random.randint(patch_versions[0], patch_versions[1]) if patch_versions else (0 if is_normalized else None)
    specifiers = [str(major_specifier)]
    if minor_specifier is not None:
        specifiers.append(str(minor_specifier))
    elif is_normalized:
        specifiers.append("0")
        
    if patch_specifier is not None:
        if len(specifiers) == 1:
            specifiers.append("0")
        specifiers.append(str(patch_specifier))
    elif is_normalized:
        specifiers.append("0")
    
    # version = "{major}"
    # version += ".{minor}" if minor_versions or is_normalized else ""
    # version += ".{patch}" if patch_versions or is_normalized else ""

    version = ".".join(specifiers)
    
    return version

def parse_version(version: str) -> tuple[int, ...]:
    """
    Helper function for match_version to convert
    str(major.minor.patch) to tuple of integers
    """
    return tuple(int(part) for part in version.split('.'))

def match_version(incoming_version: str, version_ranges: list[tuple[str, str]]) -> tuple[str, str] | None:
    """
    Matches incoming_version with one of ranges by comparing major.middle.major
    specifiers via linear search algorithm.
    
    It has assumptions that version_ranges are [[start, end), ...] and pre-sorted.
    
    If not in ranges (out of upper and lower bounds) than returns None,
    else cases returns corresponding version_range.
    """
    target = parse_version(incoming_version)

    for start_str, end_str in version_ranges:
        start = parse_version(start_str)
        end = parse_version(end_str)
        if start <= target < end:
            return (start_str, end_str)

    return None
