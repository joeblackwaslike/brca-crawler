import re


class PropertyIDNumber(dict):
    pattern = re.compile(
        r"(?P<township>\d{2})"
        r"(?P<range>\d{2})"
        r"(?P<section>\d{2})"
        r"(?P<subdivision>\w{2})"
        r"(?P<parcel>(?:\w*?)(?P<split>[1-8]?))$"
    )
    defaults = dict(
        township_direction="south",
        range_direction="east",
        is_back_assessment=False,
        is_split=False,
    )

    def _classify_subdivision(self):
        subdivision = self["subdivision"]
        if subdivision.isalpha():
            return "condo/co-op"
        else:
            if int(subdivision):
                return "platted subdivision"
            return "unplatted land"

    def __init__(self, string):
        for key, val in self.defaults.items():
            self[key] = val

        self["id"] = string
        m = self.pattern.search(string)
        for key, val in m.groupdict().items():
            self[key] = val
        self["subdivision_type"] = self._classify_subdivision()

        split = self["split"]
        if split and 9 > int(split) > 0:
            self["is_split"] = True
        elif split and int(split) == 9:
            self["is_back_assessment"] = True

        super(PropertyIDNumber, self).__init__()
