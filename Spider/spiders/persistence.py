class Request:
    _ranges = {
        "47": ["473725000000", "474331AC0480"],
        "48": ["483507000000", "484331PP0200"],
        "49": ["493501000000", "494331AB0430"],
        "50": ["503501000000", "504306000020"],
        "51": ["513501000000", "514235030191"],
    }

    _township: "Township" = ""
    direction: str = ""
    current_folio: str = ""

    def __init__(self, township, direction, current_folio=None):
        self._township = township
        self.direction = direction
        self.current_folio = current_folio or self._get_default_current_folio(
            township, direction
        )

    def _get_default_current_folio(self, township, direction):
        ranges = self._ranges[township.township]
        if direction == "next":
            return ranges[0]
        else:
            return ranges[1]

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                "{!s}={!r}".format(k, v)
                for k, v in self.__dict__.items()
                if not k.startswith("_")
            ),
        )


class Township:
    township: str = ""
    next: "Request" = None
    prev: "Request" = None

    def __init__(self, township, next_folio=None, prev_folio=None):
        self.township = township
        self.next = Request(self, direction="next", current_folio=next_folio)
        self.prev = Request(self, direction="prev", current_folio=prev_folio)

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                "{!s}={!r}".format(k, v)
                for k, v in self.__dict__.items()
                if not k.startswith("_")
            ),
        )


class BRCASpiderState:
    townships: dict = None
    seen: set = None
    _township_prefixes: tuple = ("47", "48", "49", "50", "51")

    def __init__(self):
        self.townships = {t: Township(t) for t in self._township_prefixes}
        self.seen = set()

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                "{!s}={!r}".format(k, v)
                for k, v in self.__dict__.items()
                if not k.startswith("_")
            ),
        )
