import re
import unittest
import dataclasses

from typing import Optional

class Expression:
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

  def quote(self) -> 'Expression':
    return Quote(self)

  def seq(self, rhs: 'Expression') -> 'Expression':
    if isinstance(rhs, Identity):
      return self
    return Catenate(self, rhs)

  @staticmethod
  def normalize(expr: 'Expression') -> 'Expression':
    state = State(expr)
    while state.has_next:
      state.step()
    return state.value

  @staticmethod
  def from_array(xs: list['Expression']) -> 'Expression':
    state = Identity()
    for child in reversed(xs):
      state = child.seq(state)
    return state

  @staticmethod
  def from_string(string: str) -> 'Expression':
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
        value = Expression.from_array(build).quote()
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
    return Expression.from_array(build)


class Error(Exception):
  pass

class WrongTag(Error):
  expected: str
  actual: Expression
  state: Optional['State']

  def __init__(
    self,
    expected: str,
    actual: Expression,
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
class Identity(Expression):
  def assert_identity(self):
    pass

  def seq(self, rhs: Expression) -> Expression:
    return rhs

  def __str__(self) -> str:
    return ''

@dataclasses.dataclass(frozen=True)
class Constant(Expression):
  name: str

  def assert_constant(self):
    pass

  def __str__(self) -> str:
    return self.name

@dataclasses.dataclass(frozen=True)
class Variable(Expression):
  name: str

  def assert_variable(self):
    pass

  def __str__(self) -> str:
    return self.name

@dataclasses.dataclass(frozen=True)
class Annotate(Expression):
  name: str

  def assert_annotate(self):
    pass

  def __str__(self) -> str:
    return self.name

@dataclasses.dataclass(frozen=True)
class Quote(Expression):
  body: Expression

  def assert_quote(self):
    pass

  def __str__(self) -> str:
    return f'[{self.body}]'

@dataclasses.dataclass(frozen=True)
class Catenate(Expression):
  fst: Expression
  snd: Expression

  def assert_catenate(self):
    pass

  def seq(self, rhs: Expression) -> Expression:
    if isinstance(rhs, Identity):
      return self
    if isinstance(rhs, Catenate):
      hidden = self.snd.seq(rhs)
      return self.fst.seq(hidden)
    return Catenate(self, rhs)

  def __str__(self) -> str:
    return f'{self.fst} {self.snd}'

class State:
  code: list[Expression]
  data: list[Expression]
  sink: list[Expression]

  def __init__(self, init: Expression):
    self.code = [init]
    self.data = []
    self.sink = []

  @property
  def value(self) -> Expression:
    hidden = self.sink+self.data+list(reversed(self.code))
    return Expression.from_array(hidden)

  @property
  def has_next(self) -> bool:
    return len(self.code) > 0

  def next(self) -> Expression:
    if len(self.code) == 0:
      raise NoMoreCode(self)
    result = self.code.pop()
    return result

  def send(self, expr: Expression):
    self.code.append(expr)

  def push(self, expr: Expression):
    self.data.append(expr)

  def pop(self) -> Expression:
    if len(self.data) == 0:
      raise NoMoreData(self)
    result = self.data.pop()
    return result

  def peek(self, index: int = 0) -> Expression:
    if index >= len(self.data):
      raise NoMoreData(self)
    result = self.data[-1-index]
    return result

  def thunk_with(self, point: Expression):
    self.sink.extend(self.data)
    self.data = []
    self.sink.append(point)

  def step(self):
    point = self.next()
    match point:
      case Identity():
        pass
      case Catenate(fst, snd):
        self.send(snd)
        self.send(fst)
      case Quote(_):
        self.push(point)
      case Variable(name):
        self.thunk_with(point)
      case Annotate(name):
        pass
      case Constant(name):
        try:
          self._exec(point)
        except Error:
          self.thunk_with(point)

  def _exec(self, inst: Constant):
    match inst.name:
      case 'a':
        value = self.peek(0)
        value.assert_quote()
        self.pop()
        self.send(value.body)
      case 'b':
        value = self.peek(0)
        self.pop()
        result = value.quote()
        self.push(result)
      case 'c':
        snd = self.peek(0)
        snd.assert_quote()
        fst = self.peek(1)
        fst.assert_quote()
        self.pop()
        self.pop()
        body = fst.body.seq(snd.body)
        result = body.quote()
        self.push(result)
      case 'd':
        value = self.peek(0)
        self.push(value)
      case 'e':
        value = self.peek(0)
        self.pop()
      case 'f':
        fst = self.peek(0)
        snd = self.peek(1)
        self.pop()
        self.pop()
        self.push(fst)
        self.push(snd)
      case 'g':
        pass
      case 'h':
        pass

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
      expected = Expression.from_string(expected_source)
      value = Expression.from_string(source)
      actual = Expression.normalize(value)
      actual_source = f'{actual}'
      self.assertEqual(expected, actual)
      self.assertEqual(expected_source, actual_source)
