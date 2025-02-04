"""
test_factories.py
This module contains tests for the factories of the pyfed package.
"""
import factory
from factory.fuzzy import FuzzyText, FuzzyFloat
from pyfed.models import APObject, APEvent, APPlace

class APObjectFactory(factory.Factory):
    class Meta:
        model = APObject

    id = factory.Sequence(lambda n: f"https://example.com/object/{n}")
    type = "Object"
    name = FuzzyText()
    content = FuzzyText(length=200)

class APPlaceFactory(factory.Factory):
    class Meta:
        model = APPlace

    id = factory.Sequence(lambda n: f"https://example.com/place/{n}")
    type = "Place"
    name = FuzzyText()
    latitude = FuzzyFloat(-90, 90)
    longitude = FuzzyFloat(-180, 180)

class APEventFactory(factory.Factory):
    class Meta:
        model = APEvent

    id = factory.Sequence(lambda n: f"https://example.com/event/{n}")
    type = "Event"
    name = FuzzyText()
    location = factory.SubFactory(APPlaceFactory)

# Usage example:
# event = APEventFactory()
