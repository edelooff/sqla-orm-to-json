"""Adds JSON serialization to SQLalchemy ORM objects.

Use the `add_json_converter` function to attach the default JSON Converter to
the SQLAlchemy declarative baseclass for automatich record to dict conversion.
"""

import datetime
import json


class Converter(object):
  def __init__(self):
    self.type_converters = {
        datetime.date: datetime.date.isoformat,
        datetime.datetime: datetime.datetime.isoformat}

  def __call__(self, record):
    """Returns a dictionary of the mapped ORM attributes.

    Attribute types are converted to plain Python types which can be dumped by
    JSON serializers.
    """
    result = {}
    for attr in vars(record):
      if attr.startswith('_sa_'):
        continue  # Do not include SQLAlchemy internal attributes
      value = getattr(record, attr)
      converter = self.type_converters.get(type(value))
      if converter is not None:
        value = converter(value)
      result[attr] = value
    return result

DEFAULT_CONVERTER = Converter()


def add_json_converter(declarative_base, pyramid=False, converter=None):
  """Adds a converters to JSON-ready dictionary and JSON string."""
  if converter is None:
    converter = DEFAULT_CONVERTER
  declarative_base.to_dict = lambda self: converter(self)
  declarative_base.to_json = lambda self: json.dumps(self.to_dict())
  if pyramid:
    declarative_base.__json__ = lambda self, _request: self.to_dict()
  return declarative_base
