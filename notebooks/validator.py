import re
from decimal import Decimal

def build_validator_fn(range_dict):
    if range_dict['type'] == 'range':
        start = Decimal(str(range_dict['start']))
        end = Decimal(str(range_dict['end']))
        step = Decimal(str(range_dict['step']))

        def validator(value):
            try:
                val = Decimal(str(value))
                if not (start <= val <= end):
                    return False
                return (val - start) % step == 0
            except:
                return False

        return validator

    elif range_dict['type'] == 'list':
        valid_values = set(str(v) for v in range_dict['values'])

        def validator(value):
            return str(value) in valid_values

        return validator

    else:
        raise ValueError(f"Unknown range_dict type: {range_dict['type']}")

def validate_user_input(user_input: str, regex: str, ranges_json: list):
    """
    Validates whether the user_input matches the regex AND the captured groups
    pass the range validators from ranges_json.

    Returns (True, validated_values) if valid, otherwise (False, []).
    """
    pattern = re.compile(regex)
    match = pattern.match(user_input)
    if not match:
        return False, []

    groups = match.groups()
    if len(groups) != len(ranges_json):
        return False, []

    validators = [build_validator_fn(r) for r in ranges_json]
    validated_values = []

    for fn, val in zip(validators, groups):
        if not fn(val):
            return False, []
        validated_values.append(float(val))  # or Decimal(val) if you need more precision
    
    return True, validated_values


# result = validate_user_input(
#     "SB15-3020",
#     "^SB1\.5\-3020$",
#     []
# )

# print(result)
# # Output: (True, [9.0, 11.0, 11.0])
