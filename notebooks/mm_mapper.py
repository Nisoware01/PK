import re

def full_part_number_pipeline(
    output_range_partnumber: str,
    output_specs: dict,
    input_specs: dict, 
    data_list: list = [],
    input_map: dict = {},
    output_map: dict = {},
   
):
    # print(output_range_partnumber)
    # print(output_specs)
    # print(input_specs)
    # print(data_list)
    # print(input_map)
    # print(output_map)
    # ✅ Early return if data_list is empty
    if not data_list:
        return input_specs or {}, output_specs, output_range_partnumber

    # ✅ Step 1: Update input_specs using input_map and data_list
    def update_input_specs_with_map():
        if not input_specs or not input_map:
            return input_specs or {}

        updated = input_specs.copy()
        for i, (key, transform_rule) in enumerate(input_map.items()):
            if key not in updated or i >= len(data_list):
                continue

            value = data_list[i]

            # Apply transformation
            if transform_rule == 1:
                transformed = value
            elif isinstance(transform_rule, int):
                transformed = value * transform_rule
            elif isinstance(transform_rule, str):
                try:
                    delta = int(transform_rule)
                    transformed = value + delta
                except ValueError:
                    continue
            else:
                continue

            # Only replace content inside [] if it exists
            original_val = updated[key]
            if isinstance(original_val, str) and '[' in original_val and ']' in original_val:
                updated[key] = re.sub(r'\[.*?\]', str(transformed), original_val)
            else:
                updated[key] = str(transformed)

        return updated


    # ✅ Step 2: Apply transformation to input values for output specs
    def apply_data_with_mixed_mapping():
        if not input_map:
            return None
        input_keys = list(input_map.keys())
        if len(data_list) != len(input_keys):
            raise ValueError("Length of data_list must match number of keys in input_map.")
        
        updated = {}
        for i, key in enumerate(input_keys):
            val = data_list[i]
            map_val = input_map[key]
            if isinstance(map_val, str):
                updated[key] = val + int(map_val)
            else:
                updated[key] = val * map_val
        return updated

    # ✅ Step 3: Update output_specs with those modified values
    def update_output_specs_with_values(modified_values):
        if not modified_values:
            return update_specs_directly_with_data_list()
        updated = output_specs.copy()
        for key, value in modified_values.items():
            if key in updated:
                original = updated[key]
                updated[key] = re.sub(r'\[.*?\]', str(value), original)
        return updated

    # ✅ Step 4: If no maps, just replace values inside [] directly using data_list
    def update_specs_directly_with_data_list():
        updated = output_specs.copy()
        i = 0
        for key in updated:
            val = updated[key]
            if isinstance(val, str) and '[' in val and ']' in val and i < len(data_list):
                updated[key] = re.sub(r'\[.*?\]', str(data_list[i]), val)
                i += 1
        return updated

    # ✅ Step 5: Build output_map from modified specs
    def update_output_map_from_specs(modified_specs):
        if not output_map:
            return update_map_directly_with_data_list(modified_specs)
        new_output_map = {}
        for key, factor in output_map.items():
            if key in modified_specs:
                try:
                    val = float(re.sub(r"[^\d.]", "", modified_specs[key]))
                    result = val * factor
                    new_output_map[key] = int(result) if result.is_integer() else result
                except (ValueError, TypeError):
                    new_output_map[key] = output_map[key]
            else:
                new_output_map[key] = output_map[key]
        return new_output_map

    def update_map_directly_with_data_list(modified_specs):
        result = {}
        i = 0
        for key in modified_specs:
            if i >= len(data_list):
                break
            val = modified_specs[key]
            if isinstance(val, str) and '[' not in val:
                num_part = re.sub(r"[^\d.]", "", val)
                if num_part.isdigit():
                    result[key] = int(num_part)
                    i += 1
            elif isinstance(val, str) and '[' in val:
                result[key] = data_list[i]
                i += 1
        return result

    # ✅ Step 6: Replace placeholders in part number string
    def replace_placeholders_in_partnumber(updated_output_map):
        brackets = re.findall(r"\[.*?\]", output_range_partnumber)
        values = list(updated_output_map.values())

        result = output_range_partnumber

        # Replace as many placeholders as we have values for
        for i, val in enumerate(values):
            if i < len(brackets):
                result = result.replace(brackets[i], str(val), 1)

        # If fewer values than brackets, the remaining brackets will stay
        if len(values) < len(brackets):
            print(f"⚠️ Warning: Only replaced {len(values)} of {len(brackets)} placeholders in part number.")

        return result



    # === Pipeline execution ===
    updated_input_specs = update_input_specs_with_map()
    modified_input_values = apply_data_with_mixed_mapping()
    updated_output_specs = update_output_specs_with_values(modified_input_values)
    final_output_map = update_output_map_from_specs(updated_output_specs)
    final_partnumber = replace_placeholders_in_partnumber(final_output_map)

    return updated_input_specs, updated_output_specs, final_partnumber
input_specs = {
    "accuracy": "normal grade",
    "rail width": "37mm",
    "rail length": "[130-3000/1]mm",
    "mounting pitch": "50mm",
    "overall height": "21mm",
    "number of blocks": "1",
    "rail material category": "carbon steel",
    "block material category": "carbon steel",
    "rail fastening bolt size": "M4",
    "seal presence or absence": "yes",
    "block fastening bolt size": "M5",
    "radial clearance (preload)": "normal",
    "end seal presence or absence": "yes",
    "retainer presence or absence": "yes",
    "block mounting pitch (vertical)": "29mm",
    "double seal presence or absence": "-",
    "block mounting pitch (horizontal)": "60mm",
    "metal scraper presence or absence": "-",
    "dust protection presence or absence": "yes",
    "lubrication device presence or absence": "-"
  }

output_specs = {
        "accuracy": "normal grade",
        "rail width": "37mm",
        "rail length": "[130-3000/1]mm",
        "mounting pitch": "50mm",
        "overall height": "21mm",
        "number of blocks": "1",
        "rail material category": "carbon steel",
        "block material category": "carbon steel",
        "rail fastening bolt size": "M4",
        "seal presence or absence": "yes",
        "block fastening bolt size": "M5",
        "radial clearance (preload)": "normal",
        "end seal presence or absence": "yes",
        "retainer presence or absence": "yes",
        "block mounting pitch (vertical)": "29mm",
        "double seal presence or absence": "-",
        "block mounting pitch (horizontal)": "60mm",
        "metal scraper presence or absence": "-",
        "dust protection presence or absence": "yes",
        "lubrication device presence or absence": "-"
      }

# input_map = {
#     "rail length" :1
# }

# output_map = {"rail length" :1}
# data_list = [132]
# part_number_str = "SHW21CA1UUF+[130-3000/1]LF"

# result = full_part_number_pipeline(
#     output_range_partnumber=part_number_str,
#     data_list=data_list,
#     input_map=input_map,
#     output_map=output_map,
#     output_specs=output_specs,
#     input_specs=input_specs
# )

# print("🔹 Updated Input Specs:\n", result[0])
# print("\n🔹 Updated Output Specs:\n", result[1])
# print("\n🔹 Final Part Number:\n", result[2])
