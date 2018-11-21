import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Identity

from . import util


class PropertyAssessmentItem(scrapy.Item):
    year: str = scrapy.Field()
    land_value: float = scrapy.Field()
    building_value: float = scrapy.Field()
    market_value: float = scrapy.Field()
    assessed_value: float = scrapy.Field()
    tax: float = scrapy.Field()


class PropertyAssessmentLoader(ItemLoader):
    year_selectors = {
        "2017": dict(
            land_value="landLastTwoYearsValue",
            building_value="bldgLastTwoYearsValue",
            market_value="justLastTwoYearsValue",
            assessed_value="sohLastTwoYearsValue",
            tax="assessedLastTwoYearsValue",
        ),
        "2018": dict(
            land_value="landLastYearValue",
            building_value="bldgLastYearValue",
            market_value="justLastYearValue",
            assessed_value="sohLastYearValue",
            tax="assessedLastYearValue",
        ),
        "2019": dict(
            land_value="landValue",
            building_value="bldgValue",
            market_value="justValue",
            assessed_value="sohValue",
            tax=None,
        ),
    }
    default_item_class = PropertyAssessmentItem
    default_input_processor = MapCompose(util.parse_currency)
    default_output_processor = TakeFirst()
    year_in = MapCompose(str.strip)

    @classmethod
    def year_from_bcpa(cls, year, result):
        loader = cls()
        selectors = cls.year_selectors[year]
        for key in cls.default_item_class.fields:
            loader.add_value(key, result.get(selectors.get(key)))
        loader.add_value("year", year)
        return loader.load_item()

    @classmethod
    def from_bcpa(cls, result):
        return [
            cls.year_from_bcpa(str(year), result)
            for year in reversed(range(2017, 2020))
        ]


class SalesHistoryItem(scrapy.Item):
    date: str = scrapy.Field()
    type: str = scrapy.Field()
    verification: str = scrapy.Field()
    price: float = scrapy.Field()
    reference: str = scrapy.Field()


class SalesHistoryLoader(ItemLoader):
    default_item_class = SalesHistoryItem
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()
    price_in = MapCompose(util.parse_currency)

    selector_template = dict(
        date="saleDate{}",
        type="deedType{}",
        verification="saleVerification{}",
        price="stampAmount{}",
        reference="bookAndPageOrCin{}",
    )

    @classmethod
    def get_selectors(cls, num):
        return {
            key: val.format(num) for key, val in cls.selector_template.items()
        }

    @classmethod
    def item_from_bcpa(cls, num, result):
        loader = cls()
        selectors = cls.get_selectors(num)
        for key in cls.default_item_class.fields.keys():
            value = result.get(selectors[key])
            if not value:
                return
            loader.add_value(key, value)
        return loader.load_item()

    @classmethod
    def from_bcpa(cls, result):
        items = [cls.item_from_bcpa(num, result) for num in range(1, 6)]
        return [item for item in items if item]


class LandCalculationItem(scrapy.Item):
    type: str = scrapy.Field()
    unit_price: float = scrapy.Field()
    units: str = scrapy.Field()
    zoning: str = scrapy.Field()


class LandCalculationLoader(ItemLoader):
    default_item_class = LandCalculationItem
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()
    unit_price_in = MapCompose(util.parse_currency)

    selector_template = dict(
        type="landCalcType{}",
        unit_price="landCalcPrice{}",
        units="landCalcFact{}",
        zoning="landCalcZoning",
    )

    @classmethod
    def get_selectors(cls, num):
        return {
            key: val.format(num) for key, val in cls.selector_template.items()
        }

    @classmethod
    def item_from_bcpa(cls, num, result):
        loader = cls()
        selectors = cls.get_selectors(num)
        for key in cls.default_item_class.fields.keys():
            value = result.get(selectors[key])
            if not value:
                return
            loader.add_value(key, value)
        return loader.load_item()

    @classmethod
    def from_bcpa(cls, result):
        items = [cls.item_from_bcpa(num, result) for num in range(1, 5)]
        return [item for item in items if item]


class AddressItem(scrapy.Item):
    street: str = scrapy.Field()
    city: str = scrapy.Field()
    state: str = scrapy.Field()
    zip_code: str = scrapy.Field()


class AddressLoader(ItemLoader):
    default_item_class = AddressItem
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()
    city_in = MapCompose(str.capitalize)

    @classmethod
    def type_from_bcpa(cls, type, result):
        if type == "physical":
            line1 = result["situsAddress1"]
            line2 = dict(
                city=result["situsCity"], postcode=result["situsZipCode"]
            )
        elif type == "mailing":
            line1 = result["mailingAddress1"]
            line2 = util.parse_address(result["mailingAddress2"])

        loader = cls()
        loader.add_value(
            None,
            dict(
                street=line1,
                city=line2.get("city"),
                state=line2.get("state"),
                zip_code=line2.get("postcode"),
            ),
        )
        return loader.load_item()


class ParcelItem(scrapy.Item):
    folio: str = scrapy.Field()
    owners: list = scrapy.Field()
    mailing_address: AddressItem = scrapy.Field()
    physical_address: AddressItem = scrapy.Field()
    neighborhood: str = scrapy.Field()
    property_use: str = scrapy.Field()
    millage_code: str = scrapy.Field()
    effective_year: str = scrapy.Field()
    actual_year: str = scrapy.Field()
    legal_description: str = scrapy.Field()

    assessment_history: "List[PropertyAssessmentItem]" = scrapy.Field()
    sales_history: "List[SalesHistoryItem]" = scrapy.Field()
    land_calculations: "List[LandCalculationItem]" = scrapy.Field()


class ParcelLoader(ItemLoader):
    default_item_class = ParcelItem
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()

    owners_out = Identity()
    mailing_address_in = Identity()
    physical_address_in = Identity()

    assessment_history_in = Identity()
    assessment_history_out = Identity()
    sales_history_in = Identity()
    sales_history_out = Identity()
    land_calculations_in = Identity()
    land_calculations_out = Identity()

    @classmethod
    def from_bcpa(cls, result):
        loader = cls()

        loader.add_value("folio", result["folioNumber"])
        loader.add_value("owners", result["ownerName1"])
        loader.add_value("owners", result["ownerName2"])
        loader.add_value(
            "mailing_address", AddressLoader.type_from_bcpa("mailing", result)
        )
        loader.add_value(
            "physical_address",
            AddressLoader.type_from_bcpa("physical", result),
        )
        loader.add_value("neighborhood", result["neighborhood"])
        loader.add_value("property_use", result["useCode"])
        loader.add_value("millage_code", result["millageCode"])
        loader.add_value("effective_year", result["effectiveAge"])
        loader.add_value("actual_year", result["actualAge"])
        loader.add_value("legal_description", result["legal"])

        loader.add_value(
            "assessment_history", PropertyAssessmentLoader.from_bcpa(result)
        )
        loader.add_value("sales_history", SalesHistoryLoader.from_bcpa(result))
        loader.add_value(
            "land_calculations", LandCalculationLoader.from_bcpa(result)
        )
        return loader.load_item()
