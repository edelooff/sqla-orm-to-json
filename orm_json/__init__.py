"""Adds JSON serialization to SQLalchemy ORM objects.

Use the `add_json_converter` function to attach the default JSON Converter to
the SQLAlchemy declarative baseclass for automatich record to dict conversion.
"""

import datetime
import json
import re

JSON_SAFE_TYPES = set([type(None), list, dict, int, float, basestring])


class Converter(object):
  def __init__(self, **settings):
    self.convert_key = settings.get('key_converter', to_camelcase)
    self.str_fallback = settings.get('str_fallback', True)
    self.type_converters = {}
    if 'type_converters' in settings:
      self.type_converters.update(settings['type_converters'])

  def __call__(self, record):
    """Returns a dictionary of the mapped ORM attributes.

    Attribute types are converted to plain Python types which can be dumped by
    JSON serializers.
    """
    result = {}
    for attr in vars(record):
      if attr.startswith('_sa_'):
        continue  # Do not include SQLAlchemy internal attributes
      result[self.convert_key(attr)] = self.convert_value(getattr(record, attr))
    return result

  def convert_value(self, value):
    """Converts and returns the value using the appropriate type converter.

    If no suitable type converter is found and the value is not of a known safe
    type, a default conversion to string is performed.
    """
    val_type = type(value)
    if val_type in self.type_converters:
      return self.type_converters[val_type](value)
    if self.str_fallback and not isinstance(value, JSON_SAFE_TYPES):
      return str(value)
    return value

  def add_type_converter(self, type_, converter):
    """Adds or replaces an existing converter for the given type."""
    self.type_converters[type_] = converter


def add_json_converter(declarative_base, pyramid=False, converter=None):
  """Adds a converters to JSON-ready dictionary and JSON string."""
  if converter is None:
    converter = DEFAULT_CONVERTER
  declarative_base.to_dict = lambda self: converter(self)
  declarative_base.to_json = lambda self: json.dumps(self.to_dict())
  if pyramid:
    declarative_base.__json__ = lambda self, _request: self.to_dict()
  return declarative_base


def add_type_converter(type_, converter):
  """Adds or replaces a converter to the default converter."""
  DEFAULT_CONVERTER.add_type_converter(type_, converter)


def default_converter():
  """Returs a default JSON-preparer class."""
  return Converter(type_converters={
      datetime.date: datetime.date.isoformat,
      datetime.datetime: datetime.datetime.isoformat})

DEFAULT_CONVERTER = default_converter()


def to_camelcase(varname):
  """Converts a name from lower_with_under naming to camelCase.

  The assumption is made that the given variable name is in all lowercase and
  uses single underscores to separate words.
  """
  def _convert(match):
    return match.group(1).upper()

  return re.sub('_([a-z])', _convert, varname)
