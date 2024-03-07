
# The pydop Library


**pydop** is a small python library for Delta-Oriented Software Product Lines development, that provides classes for
 - feature models
 - modular and transformation-based SPL (a generalization of Delta-Oriented Programming)
 - modular Multi-SPL
 - standard transformation operations, like the addition or the removal of a field or a method in a class

### Installation

This library is available using the `pip` command:
```bash
$ pip install pydop
```

Alternatively, it is possible to simply clone this repository:
 this library is implemented in pure python and only depends on [networkx](https://networkx.org/):
 installing networkx using `pip` and cloning this repository is enough to install it:
```bash
$ pip install networkx
$ git clone https://github.com/onera/pydop.git
```

### An Hello World Example

This example is taken from [[1]](#1) and consists of a *Multi-Lingual Hello World Product Line*, 
 i.e., an SPL that generates a class named **Greater** that can say *Hello World* in multiple languages, and possibly multiple times.

In pydop, a product line is split in 5 parts:
 - the feature model, that states the variability of the SPL
 - the base artifact factory, that generates the initial artifact for every variant generation
 - the SPL object itself
 - a list of deltas, that are python functions that modify the base artifact
 - the configuration knowledge, that links the deltas to the SPL by stating which delta execute for which combination of features, and in which order

#### Part 0: the imports

In this Example, we have 5 imports:
```python
from pydop.fm_constraint import *
```
This line loads all the classes to declare cross-tree constraints, i.e., boolean constraints over feature names.
```python
from pydop.fm_diagram import *
```
This line loads all the classes used to declare a feature model.
```python
from pydop.spl import SPL, RegistryGraph
```
This line loads the `SPL` class and `RegistryGraph`.
The later is a class that allows to specify the ordering between delta as a generic dependency graph.
```python
from pydop.operations.modules import *
```
This line loads all the basic delta operation on standard python objects (including classes and modules)
```python
import sys
```
This line loads the `sys` module, to access `sys.exit` in case of problems.


#### Part 1: the Feature Model

```python
fm = FD("HelloWorld",
 FDMandatory(
  FD("Language",
   FDAlternative(
    FD("English"),
    FD("Dutch"),
    FD("German")
 ))),
 FDOptional(
  FD("Repeat", times=Int(0,1000))
))
```

Here, `FD` introduces a new feature.
Hence the root feature of this Feature Model is `HelloWorld`, with one mandatory feature `Language`
 (with the languages `English`, `Dutch` and `German` available);
 and with one optional feature `Repeat`.
That last feature has an attribute `times`, that states that the number of repetition must be in the interval `[0, 1000[`.

#### Part 2: the Base Artifact Factory

```python
def gen_base_artifact():
 class Greeter(object):
   def sayHello(self): return "Hello World"
 return Greeter
```

The factory is a python function with no parameter, that returns the initial artifact of a variant generation process.
In our case, the initial variant is the `Greeter` class with the method `sayHello` that returns `"Hello World"` said in english.

#### Part 3: the SPL Object

```python
spl = SPL(fm, RegistryGraph(), gen_base_artifact)
```

The `SPL` constructor takes three parameters:
 - the feature model of the SPL
 - an object stating how the ordering between delta can be specified (in our case, that object is an instance of the `RegistryGraph` class)
 - and the base artifact factory


**Note:** it is possible in pydop to use a *Pure* Delta-Oriented Programming approach [[2]](#2) by putting `None` in place of the base artifact factory.
In that case, the parameter of the first delta being executed will be `None`, and this delta would be in charge of providing the base artifact.


#### Part 4: the Deltas

```python
def Nl(Greeter):
 @modify(Greeter)
 def sayHello(self): return "Hallo wereld"

def De(Greeter):
 @modify(Greeter)
 def sayHello(self): return "Hallo Welt"

def Rpt(Greeter, product):
 @modify(Greeter)
 def sayHello(self):
  tmp_str = self.original()
  return " ".join(tmp_str for _ in range(product["times"]))
```

Deltas are python functions that modify the base artifact to construct the expected variant.
The first delta implements the `Dutch` feature.
It is a function that takes one argument: the artifact to be modified.
This delta modifies that artifact (in our case, the class `Greeter`) by replacing its `sayHello` method and making it return `"hello World` in dutch.
The second delta implements the `German` feature and is implemented like the `Dutch` one.
The third delta implements the `Repeat` feature and takes two parameters:
 the first one is the artifact to be modified (like for the two previous deltas),
 and the second one is the product that triggered the variant generation.
This delta uses this additional argument to retrieve the number of repetition requested by the user, with `product["times"]` in the last line.

#### Part 5: the Configuration Knowledge

```python
spl.delta("Dutch")(Nl)
spl.delta("German")(De)
spl.delta("Repeat", after=["Nl", "De"])(Rpt)
```

This Configuration Knowledge (CK) simply states that
 the `Nl` delta is activated by the `Dutch` feature,
 the `De` delta is activated by the `German` feature,
 and the `Rpt` delta is activated by the `Repeat` feature.
Moreover, the statement `after=["Nl", "De"]` means that the `Nl` delta cannot be executed before the `Nl` or the `De` delta,
 to ensure that the repeated sentence is the correct one.


**Note:** it is possible in pydop to declare the CK together with the delta.
In this case, the delta declaration would look like

```python
@spl.delta("Dutch")
def Nl(Greeter): ...

@spl.delta("German")
def De(Greeter): ...

@spl.delta("Repeat", after=["Nl", "De"])
def Rpt(Greeter, product): ...
```

#### Using the SPL

Now that the SPL is constructed, we can generate variant right away.
For instance, the following generates a variant corresponding to selecting the `Dutch` language, with 4 repetition,
 and calls the `sayHello` method on an instance of that variant:

```python
# 1. create a full configuration from a partial specification of features
conf, err = spl.close_configuration({"Dutch": True, "Repeat": True, "times": 4})
if(err): # possibly the partial specification was erroneous
  print(err); sys.exit(-1)

# 2. create the variant by simply calling the SPL with the configuration in parameter
Greater = spl(conf)

# 3. use the variant
print(Greater().sayHello())
```

Moreover, other variants can also be created in the same python program, like this second one, with the `German` language selected and no repetition:

```python
conf, err = spl.close_configuration({"German": True, "Repeat": False})
if(err):
  print(err); sys.exit(-1)

Greater = spl(conf)
print(Greater().sayHello())
```

### Other Examples

Other examples are available in the [examples](https://github.com/onera/pydop/tree/master/examples) folder.



## References

<a name="1">[1]</a> 
Dave Clarke, Radu Muschevici, José Proença, Ina Schaefer, and Rudolf Schlatte.
2010. Variability Modelling in the ABS Language.
In FMCO (LNCS, Vol. 6957). Springer, 204–224.
*doi: 10.1007/978-3-642-25271-6_11*

<a name="2">[2]</a>
Ina Schaefer, and Ferruccio Damiani.
2010. Pure delta-oriented programming.
In FOSD'10. ACM, 49--56.
*doi: 10.1145/1868688.1868696*

