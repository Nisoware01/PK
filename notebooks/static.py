def get_static_part(part_number: str) -> str:
    """Returns the static part before the first [ in the template."""
    bracket_index = part_number.find('[')
    if bracket_index == -1:
        return part_number  # No [ found, entire part is static
    return part_number[:bracket_index]
