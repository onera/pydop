
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


from pydop.utils import _empty__


################################################################################
# configuration class
################################################################################

class configuration__c(object):
  __slots__ = ("m_dict", "m_resolver", "m_names")
  def __init__(self, d, resolver=None, names=None):
    assert(isinstance(d, dict))
    assert((resolver is None) == (names is None))
    self.m_dict = d
    self.m_resolver = resolver
    self.m_names = names

  ## base mapping API

  def get(self, key, errors, default=None):
    global _empty__
    res = self.m_dict.get(key, _empty__)
    if(res is _empty__):
      if(isinstance(key, str) and (self.m_resolver is not None)):
        key_path = _path_from_str__(key)
        key_resolved = self.m_resolver.resolve(key_path, errors, None)
        if(key_resolved is not None):
          return self.m_dict.get(key_resolved, default)
    return res

  def __getitem__(self, key):
    global _empty__
    errors = decl_errors__c()
    res = self.get(key, errors, _empty__)
    if(res is _empty__):
      if(errors):
        raise KeyError(str(errors))
      else: KeyError(key)
    else: return res

  def items(self): return self.m_dict.items()
  def __iter__(self): return self.m_dict.__iter__()


  ## linking and unlinking

  def link(self, fm):
    conf = self.unlink()
    return fm.link_configuration(conf)

  def unlink(self):
    if(self.m_resolver is None): return self
    else: return configuration__c({(self.m_names.get(key, key)): val for key, val in self.m_dict.items()})


  ## basic manipulation

  def __eq__(self, other):
    if(isinstance(other, _configuration__c)):
      return ((self.m_dict == other.m_dict) and (self.m_resolver == other.m_resolver))
    return False

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


