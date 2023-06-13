
# This file is part of the pydop library.
# Copyright (c) 2021 ONERA.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.
#

# Author: Michael Lienhardt
# Maintainer: Michael Lienhardt
# email: michael.lienhardt@onera.fr

"""
This file contains the class for an SPL configuration.
This class is a wrapper around a simple dictionary mapping variables (features and attributes) to their values.
We use a wrapper to manage the fact that a variable may not have a unique name:
 if that variable lives in a feature model,
  any unabiguous partial path identifying where this variable lives in that FM is a valid name for that variable.
"""

import itertools

from pydop.utils import _empty__
from pydop.fm_result import decl_errors__c


################################################################################
# configuration class
################################################################################

class configuration__c(object):
  """This class implements Feature Model configurations.
It is a wrapper around a simple dictionary mapping variables (features and attributes) to their values,
 with an optional name resolver (e.g., the resolver of a feature model).
In case a name resolver is provided, the configuration uses the unique and unabiguous identifiers provided by the resolver
 to refer to the variables in its dictionary, and save the original names in an annex registry
 in case the user want to retrieve the original dictionary.

This class is supposed to be used only internally, the user should only see dictionaries.
  """
  __slots__ = ("m_dict", "m_resolver", "m_names")
  def __init__(self, d, resolver=None, names=None):
    """__init__(dict, object, dict) -> configuration__c
Creates a new configuration from the dictionary in input.
Parameters:
  d: the dictionary mapping variable identifiers to their values
  resolver: a name resolver (e.g., the resolver of a feature model)
  names: mapping giving the names of all relevant variables in d
    """
    assert(isinstance(d, dict))
    assert((resolver is None) == (names is None))
    self.m_dict = d
    self.m_resolver = resolver
    self.m_names = names

  ## base mapping API

  def get(self, key, errors, default=None):
    """get(object, decl_errors__c, object) -> object
Retrieves a value from the configuration
Parameters:
  key: any hashable object (should correspond to a key of the configuration's dictionary, modulo the name resolver)
  errors: the object storing the possible errors during the lookup
  default: the returned object, if the key does not correspond to a valid entry in the configuration's dictionary.
    """
    global _empty__
    res = self.m_dict.get(key, _empty__)
    if(res is _empty__):
      if(isinstance(key, str) and (self.m_resolver is not None)):
        key_resolved = self.m_resolver(key, errors, None)
        if(key_resolved is not None):
          return self.m_dict.get(key_resolved, default)
    return res

  def __getitem__(self, key):
    """ __getitem__(object) -> object
Retrieves a value from the configuration.
Raises KeyError if the input key does not correspond to a valid entry in the configuration's dictionary.
    """
    global _empty__
    errors = decl_errors__c()
    res = self.get(key, errors, _empty__)
    if(res is _empty__):
      if(errors):
        raise KeyError(str(errors))
      else: KeyError(key)
    else: return res

  def items(self):
    """items() -> a set-like object providing a view on the configuration's items"""
    return self.m_dict.items()
  def __iter__(self):
    """__iter__() -> an iterator over the configuration's keys"""
    return self.m_dict.__iter__()


  ## linking and unlinking

  def link(self, resolver):
    """link(object) -> configuration__c
Returns a configuration identical to `self`, but using the name resolver in parameter
Raises KeyError if a name in `self` is not known by the resolver
    """
    if(resolver is self.m_resolver): return self
    else:
      d = self.unlink().m_dict
      errors = decl_errors__c()
      d_new = {}
      names = {}
      for key, val in d.items():
        key_resolved = resolver.resolve(key, errors, None)
        if(key_resolved is not None):
          names[key_resolved] = key
          d_new[key_resolved] = val
      if(errors):
        raise KeyError(str(errors))        
      return configuration__c(d_new, resolver, names)

  def unlink(self, full=False):
    """unlink(bool) -> configuration__c
Unlink the configuration from its name resolver, and returns a configuration using the names given by the user.
If the parameter `full` is `True`, put also the variables without names in the resuting configuration
    """
    global _empty__
    if(self.m_resolver is None):
      return self
    elif(full):
      return configuration__c({(self.m_names.get(key, key)): val for key, val in self.m_dict.items()})
    else:
      d_new = {}
      for k,v in self.m_dict.items():
        k_new = self.m_names.get(k, _empty__)
        if(k_new is not _empty__):
          d_new[k_new] = v
      return configuration__c(d_new)

  ## basic manipulation

  def __eq__(self, other):
    if(isinstance(other, configuration__c)):
      return ((self.m_dict == other.m_dict) and (self.m_resolver == other.m_resolver))
    return False

  def __hash__(self):
    return hash(frozenset((k,v) for k,v in itertools.chain(self.m_dict.items(), self.m_names.items())))

  def __str__(self):
    return str(self.unlink().m_dict)



##########################################
# Translates common product representations into dict

def make_configuration(fm, data):
  if(isinstance(data, dict)):
    res = data
  elif(isinstance(data, (set, tuple, list,))):
    res = {}
    for el in data:
      if(isinstance(el, str)):
        res[el] = True
      elif(isinstance(el, (tuple, list,)) and (len(el) == 2)):
        res[el[0]] = el[1]
      else:
        raise TypeError(f"ERROR: unexpected type in configuration (expected: str or tuple/list or size 2; found {type(el)})")
  else:
    raise TypeError(f"ERROR unexpected configuration type (expected: dict/set/tuple/list; found {type(configuration)}")
  return res


