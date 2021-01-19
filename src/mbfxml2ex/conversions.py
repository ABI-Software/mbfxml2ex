def hex_to_rgb(hex_string):
    """
    Convert a hexadecimal string with leading hash into a three item list of values between [0, 1].

      E.g. #00ff00 --> [0, 1, 0]

    :return: The value of the hexadecimal string as a three element list with values in the range [0. 1].
    """
    hex_string = hex_string.lstrip('#')
    return [int(hex_string[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


