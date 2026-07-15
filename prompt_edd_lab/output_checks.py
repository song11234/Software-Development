from rubric import REQUIRED_SECTIONS


def check_required_sections(output: str) -> list[str]:
    errors = []
    for section in REQUIRED_SECTIONS:
        if section not in output:
            errors.append(f"missing section: {section}")
    return errors


def check_min_length(output: str, min_chars: int = 40) -> list[str]:
    if len(output.strip()) < min_chars:
        return ["output is too short"]
    return []


def check_forbidden_points(output: str, forbidden_points: list[str]) -> list[str]:
    errors = []
    for phrase in forbidden_points:
        if phrase in output:
            errors.append(f"forbidden phrase appears: {phrase}")
    return errors


def run_static_checks(output: str, forbidden_points: list[str]) -> list[str]:
    errors = []
    errors.extend(check_required_sections(output))
    errors.extend(check_min_length(output))
    errors.extend(check_forbidden_points(output, forbidden_points))
    return errors