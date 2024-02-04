import expression as expr

class Statement:
  pass

class Equals(Statement):
  fst: expr.Variable
  snd: expr.Expression

class HasType(Statement):
  fst: expr.Variable
  snd: expr.Expression

def from_string(string: str) -> Statement:
  pass

class Module:
  body: dict[str, list[Statement]]
