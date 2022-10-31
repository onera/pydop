
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


_empty__ = object()
_forward__ = object()


##########################################
# Default class for products
# wrapper around a dict for getting values

class product_default(object):
  __slots__ = ("m_content",)
  def __init__(self, content):
    self.m_content = content
  def get(self, el, default=_forward__):
    if(default is _forward__):
      default = el
    return self.m_content.get(el, default)


##########################################
# Default evaluation function
# DEPRECATED: replaced by product_default:get

def pred_eval(el, product, idx=None, expected=True):
  res = None
  if(callable(el)):
    res = el(product, idx, pred_eval, expected)
  elif(isinstance(el, pred_var)):
    res = product.get(el.m_content, _empty__)
  else:
    res = product.get(el, el)
  return res
  # if(isinstance(res, bool)):
  #   return res
  # else:
  #   raise ValueError(f"ERROR: predicate evaluation must return a boolean (found {type(res)} while evaluating {el})")


##########################################
# Translates common prodct representations
# into dict

def make_configuration(data):
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


##########################################
# Util function to combine generators

def gen_sequence(*args):
  i = 0
  l = len(args)
  while(i < l):
    yield from args[i]
    i += 1



class dict_sequence(object):
  __slots__ = ("m_content")
  def __init__(self, *args):
    self.m_content = tuple(args)

  def get(self, key, default=None):
    for sub in self.m_content:
      res = sub.get(key, _empty__)
      if(res is not _empty__):
        return res
    return default

