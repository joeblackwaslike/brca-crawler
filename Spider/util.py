import string

import money_parser
import dateparser
import usaddress


def parse_address(s):
    trans_table = s.maketrans("", "", string.punctuation)
    addr = s.translate(trans_table)
    addr_map = {k: v for v, k in usaddress.parse(addr)}
    parsed = {}

    if "PlaceName" in addr_map:
        parsed["city"] = addr_map["PlaceName"].capitalize()
    if "StateName" in addr_map:
        parsed["state"] = addr_map["StateName"].upper()
    if "ZipCode" in addr_map:
        parsed["postcode"] = addr_map["ZipCode"]
    return parsed


# Older implementation (slower and memory intesive but more accurate for complex parsing)
# from postal.parser import parse_address as _parse_address
# def parse_address(string):
#     components = {k: v for v, k in _parse_address(string)}
#     if "city" in components:
#         components["city"] = components["city"].capitalize()
#     if "state" in components:
#         components["state"] = components["state"].upper()
#     return components


def parse_date(s):
    return dateparser.parse(s).date()


def parse_currency(s):
    return float(money_parser.price_dec(s))


def format_folio(folio):
    return "{} {} {}  {} {}".format(
        folio[:2], folio[2:4], folio[4:6], folio[6:8], folio[8:]
    )
