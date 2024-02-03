import re
import unittest
import dataclasses

from typing import Optional

class Object:
  def assert_identity(self):
    raise WrongTag(expected='identity', actual=self)

  def assert_variable(self):
    raise WrongTag(expected='variable', actual=self)

  def assert_annotate(self):
    raise WrongTag(expected='annotate', actual=self)

  def assert_quote(self):
    raise WrongTag(expected='quote', actual=self)

  def assert_catenate(self):
    raise WrongTag(expected='catenate', actual=self)

  def quote(self) -> 'Object':
    return Quote(self)

  def seq(self, rhs: 'Object') -> 'Object':
    if isinstance(rhs, Identity):
      return self
    return Catenate(self, rhs)

class Error(Exception):
  pass

class WrongTag(Error):
  expected: str
  actual: Object
  state: Optional['State']

  def __init__(
    self,
    expected: str,
    actual: Object,
    state: Optional['State'] = None,
  ):
    self.expected = expected
    self.actual = actual
    self.state = state

  def __str__(self) -> str:
    return f'''
Expected a value with tag {self.expected}, but got {self.actual}
'''.strip()

class UnknownToken(Error):
  source: str
  token: str

  def __init__(self, source: str, token: str):
    self.source = source
    self.token = token

  def __str__(self) -> str:
    return f'''
Unknown token `{self.token}` in source code:

{self.source}
'''.strip()

class UnbalancedBrackets(Error):
  source: str

  def __init__(self, source: str):
    self.source = source

  def __str__(self) -> str:
    return f'''
Unbalanced brackets in source code:

{self.source}
'''.strip()

class NoMoreCode(Error):
  state: 'State'

  def __init__(self, state: 'State'):
    self.state = state

  def __str__(self) -> str:
    return f'''
No more code
'''.strip()

class NoMoreData(Error):
  state: 'State'

  def __init__(self, state: 'State'):
    self.state = state

  def __str__(self) -> str:
    return f'''
No more data
'''.strip()

@dataclasses.dataclass(frozen=True)
class Identity(Object):
  def assert_identity(self):
    pass

  def seq(self, rhs: Object) -> Object:
    return rhs

  def __str__(self) -> str:
    return ''

@dataclasses.dataclass(frozen=True)
class Constant(Object):
  name: str

  def assert_constant(self):
    pass

  def __str__(self) -> str:
    return self.name

@dataclasses.dataclass(frozen=True)
class Variable(Object):
  name: str

  def assert_variable(self):
    pass

  def __str__(self) -> str:
    return self.name

@dataclasses.dataclass(frozen=True)
class Annotate(Object):
  name: str

  def assert_annotate(self):
    pass

  def __str__(self) -> str:
    return self.name

@dataclasses.dataclass(frozen=True)
class Quote(Object):
  body: Object

  def assert_quote(self):
    pass

  def __str__(self) -> str:
    return f'[{self.body}]'

@dataclasses.dataclass(frozen=True)
class Catenate(Object):
  fst: Object
  snd: Object

  def assert_catenate(self):
    pass

  def seq(self, rhs: Object) -> Object:
    if isinstance(rhs, Identity):
      return self
    if isinstance(rhs, Catenate):
      hidden = self.snd.seq(rhs)
      return self.fst.seq(hidden)
    return Catenate(self, rhs)

  def __str__(self) -> str:
    return f'{self.fst} {self.snd}'

class State:
  code: list[Object]
  data: list[Object]
  sink: list[Object]

  def __init__(self, init: Object):
    self.code = [init]
    self.data = []
    self.sink = []

  @property
  def value(self) -> Object:
    hidden = self.sink+self.data+list(reversed(self.code))
    return from_array(hidden)

  @property
  def has_next(self) -> bool:
    return len(self.code) > 0

  def next(self) -> Object:
    if len(self.code) == 0:
      raise NoMoreCode(self)
    result = self.code.pop()
    return result

  def send(self, obj: Object):
    self.code.append(obj)

  def push(self, obj: Object):
    self.data.append(obj)

  def pop(self) -> Object:
    if len(self.data) == 0:
      raise NoMoreData(self)
    result = self.data.pop()
    return result

  def peek(self, index: int = 0) -> Object:
    if index >= len(self.data):
      raise NoMoreData(self)
    result = self.data[-1-index]
    return result

  def thunk_with(self, point: Object):
    self.sink.extend(self.data)
    self.data = []
    self.sink.append(point)

class Container:
  state: State

  def __init__(self, init: Object):
    self.state = State(init)

  @property
  def value(self) -> Object:
    return self.state.value

  @property
  def is_done(self) -> bool:
    return not self.state.has_next

  def step(self):
    point = self.state.next()
    match point:
      case Identity():
        pass
      case Catenate(fst, snd):
        self.state.send(snd)
        self.state.send(fst)
      case Quote(_):
        self.state.push(point)
      case Variable(name):
        self.state.thunk_with(point)
      case Annotate(name):
        pass
      case Constant(name):
        try:
          self._exec(point)
        except Error:
          self.state.thunk_with(point)

  def _exec(self, inst: Constant):
    match inst.name:
      case 'a':
        value = self.state.peek(0)
        value.assert_quote()
        self.state.pop()
        self.state.send(value.body)
      case 'b':
        value = self.state.peek(0)
        self.state.pop()
        result = value.quote()
        self.state.push(result)
      case 'c':
        snd = self.state.peek(0)
        snd.assert_quote()
        fst = self.state.peek(1)
        fst.assert_quote()
        self.state.pop()
        self.state.pop()
        body = fst.body.seq(snd.body)
        result = body.quote()
        self.state.push(result)
      case 'd':
        value = self.state.peek(0)
        self.state.push(value)
      case 'e':
        value = self.state.peek(0)
        self.state.pop()
      case 'f':
        fst = self.state.peek(0)
        snd = self.state.peek(1)
        self.state.pop()
        self.state.pop()
        self.state.push(fst)
        self.state.push(snd)
      case 'g':
        pass
      case 'h':
        pass

def normalize(obj: Object) -> Object:
  container = Container(obj)
  while not container.is_done:
    container.step()
  return container.value

def from_array(xs: list[Object]) -> Object:
  state = Identity()
  for child in reversed(xs):
    state = child.seq(state)
  return state

def from_string(string: str) -> Object:
  stack = []
  build = []
  tokens = string
  tokens = tokens.replace('\t', ' ')
  tokens = tokens.replace('\r', ' ')
  tokens = tokens.replace('\n', ' ')
  tokens = tokens.replace('[', '[ ')
  tokens = tokens.replace(']', ' ]')
  tokens = tokens.split(' ')
  for token in tokens:
    if token == '[':
      stack.append(build)
      build = []
    elif token == ']':
      if len(stack) == 0:
        raise UnbalancedBrackets(source=string)
      value = from_array(build).quote()
      build = stack.pop()
      build.append(value)
    elif token in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
      value = Constant(token)
      build.append(value)
    elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', token):
      value = Variable(token)
      build.append(value)
    elif re.match(r'^@[a-zA-Z_][a-zA-Z0-9_]*$', token):
      value = Annotate(token)
      build.append(value)
    elif len(token) == 0:
      continue
    else:
      raise UnknownToken(source=string, token=token)
  return from_array(build)

class TestBasic(unittest.TestCase):
  def test_axioms(self):
    axioms = [
      ('[foo] a', 'foo'),
      ('[foo] b', '[[foo]]'),
      ('[foo] [bar] c', '[foo bar]'),
      ('[foo] d', '[foo] [foo]'),
      ('[foo] e', ''),
      ('[foo] [bar] f', '[bar] [foo]'),
    ]
    for (source, expected_source) in axioms:
      expected = from_string(expected_source)
      value = from_string(source)
      actual = normalize(value)
      actual_source = f'{actual}'
      self.assertEqual(expected, actual)
      self.assertEqual(expected_source, actual_source)
