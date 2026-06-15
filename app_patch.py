def parse_data(data):
    if not isinstance(data, list):
        raise ValueError('Input must be a list')
    parsed_data = []
    for index, item in enumerate(data):
        parsed_data.append({'index': index, 'value': item})
    return parsed_data