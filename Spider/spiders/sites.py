import json


class BRCASite:
    endpoints = dict(
        parcel="getParcelInformationData",
        next="getRealNextParcel",
        prev="getRealPreviousParcel",
    )
    base_url = "https://web.bcpa.net/bcpaclient/search.aspx/"
    tax_year = 2019

    def __init__(self, spider):
        self.spider = spider
        self.logger = spider.logger

    def payload_for(self, folio):
        return json.dumps(dict(folioNumber=folio, taxyear=self.tax_year))

    def url_for(self, endpoint):
        return self.base_url + self.endpoints[endpoint]
