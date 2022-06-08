 
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


def eval(el, product):
  res = None
  if(callable(el)):
    res = el(product)
  else:
    res = product.get(el, el)
  if(isinstance(res, bool)):
    return res
  else:
    raise ValueError(f"ERROR: predicate evaluation must return a boolean (found {type(res)} while evaluating {el})")
