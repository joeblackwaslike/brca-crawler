import os.path
import json
import pickle

import scrapy
from scrapy.spiders import Spider

from ..items import ParcelLoader
from ..util import format_folio
from .sites import BRCASite
from .persistence import BRCASpiderState


class MultiBRCASpider(Spider):
    name = "multi-BRCA"
    _state_file_path = "{}-state.bin".format(name)
    loader_factory: "scrapy.loader.ItemLoader" = ParcelLoader.from_bcpa

    def __init__(self, *args, **kwargs):
        self.site = BRCASite(self)
        self._state = self.load_state()
        super(MultiBRCASpider, self).__init__(*args, **kwargs)

    def load_state(self):
        if not os.path.isfile(self._state_file_path):
            self.logger.info("State file doesn't exist, creating")
            open(self._state_file_path, "ab").close()

        with open(self._state_file_path, "rb") as fd:
            try:
                state = pickle.load(fd)
            except EOFError:
                state = BRCASpiderState()
            self.logger.debug("State loaded: %s", state)
            return state

    def save_state(self, state):
        self.logger.debug("Saving state: %s", state)
        with open(self._state_file_path, "wb") as fd:
            pickle.dump(state, fd)

    def start_requests(self):
        for township in self._state.townships.values():
            for direction in ("next", "prev"):
                state = getattr(township, direction)
                yield self.request(state)

    def closed(self, reason):
        self.save_state(self._state)

    def request(self, state):
        if state.current_folio not in self._state.seen:
            return self.request_parcel(state)
        else:
            return self.request_new_folio_number(state)

    def request_parcel(self, state):
        self.logger.info(">> %s", format_folio(state.current_folio))
        return scrapy.Request(
            self.site.url_for("parcel"),
            method="POST",
            body=self.site.payload_for(state.current_folio),
            callback=self.parse_parcel,
            meta=dict(state=state),
        )

    def parse_parcel(self, response):
        state = response.meta["state"]
        data = json.loads(response.body)["d"]

        if data:
            record = data[0]
            self.logger.debug(
                "got record: (current_folio: %s, record_folio: %s)",
                format_folio(state.current_folio),
                format_folio(record["folioNumber"]),
            )
            yield self.load_parcel(record)
        else:
            self.logger.info(
                "folio: %s has no data, skipping",
                format_folio(state.current_folio),
            )
        yield self.request_new_folio_number(state)

    def load_parcel(self, record):
        folio = record["folioNumber"]
        if folio in self._state.seen:
            return None

        self._state.seen.add(folio)
        return self.loader_factory(record)

    def request_new_folio_number(self, state):
        self.logger.debug(
            "direction: %s, current_folio: %s",
            state.direction,
            format_folio(state.current_folio),
        )
        return scrapy.Request(
            self.site.url_for(state.direction),
            method="POST",
            body=self.site.payload_for(state.current_folio),
            callback=self.parse_new_folio_number_request,
            meta=dict(state=state),
        )

    def parse_new_folio_number_request(self, response):
        state = response.meta["state"]

        new_folio_number = json.loads(response.body)["d"]
        self.logger.debug(
            "new folio number returned! %s, last_folio: %s, direction: %s",
            new_folio_number,
            format_folio(state.current_folio),
            state.direction,
        )
        if new_folio_number:
            if new_folio_number in self._state.seen:
                self.logger.info(
                    "new_folio_number %s already seen. (last_folio: %s, direction: %s)",
                    new_folio_number,
                    format_folio(state.current_folio),
                    state.direction,
                )
            elif new_folio_number != state.current_folio:
                state.current_folio = new_folio_number
                yield self.request_parcel(state)
