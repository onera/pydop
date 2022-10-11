 
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


def eval_predicate(el, product, idx=None):
  res = None
  if(callable(el)):
    res = el(product, idx, eval_predicate)
  else:
    res = product.get(el, el)
  return res
  # if(isinstance(res, bool)):
  #   return res
  # else:
  #   raise ValueError(f"ERROR: predicate evaluation must return a boolean (found {type(res)} while evaluating {el})")



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
