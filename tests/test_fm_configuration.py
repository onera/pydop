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

from pydop.fm_configuration import *


empty = object()


def resolver_dummy(key, errors, default=None):
  if(key):
    return key[0]
  else:
    return "" # no error management in testing

def mk_configuration(d):
  res = {}
  names = {}
  for k,v in d.items():
    key = resolver_dummy(k, None)
    if(key in res):
      raise KeyError(f"ERROR: key {k} is ambiguous")
    else:
      res[key] = v
      names[key] = k
  return configuration__c(res, resolver_dummy, names)


def fn_test_conf(conf, conf_d, size):
  assert(isinstance(conf, configuration__c))
  assert(len(conf.m_dict) == size)
  assert(conf.m_resolver is resolver_dummy)
  assert(len(conf.m_names) == size)
  assert(conf.unlink().m_dict == conf_d)


def test_configuration():
  print("==========================================")
  print("= test_configuration")

  global empty

  ## 1. test empty conf
  conf_d = {}
  conf = mk_configuration(conf_d)
  fn_test_conf(conf, conf_d, 0)

  ## 2. test non empty correct conf
  conf_d = {"a": 1, "bb": 2, "ccc": 3}
  conf = mk_configuration(conf_d)
  fn_test_conf(conf, conf_d, 3)
  assert(conf.m_names["a"] == "a")
  assert(conf.m_names["b"] == "bb")
  assert(conf.m_names["c"] == "ccc")
  # 2.1. positive tests
  tests = (("a", 1), ("aa", 1), ("aaa", 1), ("b", 2), ("bb", 2), ("bbb", 2), ("c", 3), ("cc", 3), ("ccc", 3),)
  for k,v in tests:
    assert(conf[k] == v)
  # 2.2. negative tests
  tests = ("", "d", "dd",)
  for k in tests:
    assert(conf.get(k, None, default=empty) is empty)

  ## 3. test non correct conf
  conf_d = {"a": 1, "aa": 2}
  errs = tuple(k for k in conf_d.keys() if(k.startswith("a") and (len(k) > 1)))
  try:
    conf = mk_configuration(conf_d)
    assert(False)
  except KeyError as e:
    assert(str(e) == f"'ERROR: key {errs[0]} is ambiguous'")



if(__name__ == "__main__"):
  test_configuration()

