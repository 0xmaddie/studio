from typing import Optional

import os
import pprint
import zipfile
import tempfile
import wasmtime
import dataclasses

@dataclasses.dataclass(frozen=True)
class Result:
  """The result of a Python computation. Includes standard output,
  standard error, and various metrics related to space and time usage.
  """
  stdout: str
  stderr: str
  data_len: int
  memory_size: int
  fuel_consumed: int

  def __str__(self) -> str:
    data = {
      'stdout': self.stdout,
      'stderr': self.stderr,
      'data_len': self.data_len,
      'memory_size': self.memory_size,
      'fuel_consumed': self.fuel_consumed,
    }
    return pprint.pprint(data)

class Context:
  """Evaluate Python code within a sandbox using Wasmtime. This
  class behaves like a function-as-a-service platform, like AWS Lambda,
  in that it's stateless and re-evaluates the code it's given every time
  it's called.
  """
  python_wasm_path: str
  engine: wasmtime.Engine
  linker: wasmtime.Linker
  # todo: i guess if we want to load packages, we'll need
  # more modules?
  module: wasmtime.Module

  def __init__(
    self,
    python_wasm_path: str,
  ):
    self.python_wasm_path = python_wasm_path
    self.engine_config = wasmtime.Config()
    self.engine_config.consume_fuel = True
    self.engine_config.cache = True

    self.engine = wasmtime.Engine(self.engine_config)
    self.linker = wasmtime.Linker(self.engine)
    self.linker.define_wasi()

    self.module = wasmtime.Module.from_file(
      self.engine,
      self.python_wasm_path,
    )

  def __call__(
    self,
    source: Optional[str] = None,
    wheel: Optional[str] = None,
    module: Optional[str] = None,
    fuel: int = 500_000_000,
  ) -> Result:
    with tempfile.TemporaryDirectory() as chroot:
      stdout_file = os.path.join(chroot, 'stdout')
      stderr_file = os.path.join(chroot, 'stderr')

      wasi_config = wasmtime.WasiConfig()
      wasi_config.stdout_file = stdout_file
      wasi_config.stderr_file = stderr_file
      wasi_config.preopen_dir(chroot, '/')

      if source is not None:
        assert wheel is None
        assert module is None
        wasi_config.argv = ('python', '-c', source)
      elif wheel is not None:
        assert source is None
        assert module is not None:
        with zipfile.ZipFile(wheel, 'r') as package:
          package.extractall(chroot)
          wasi_config.argv = ('python', '-m', module)
      else:
        raise ValueError(f'''
Context: you must provide either source code or a wheel path
'''.strip())

      store = wasmtime.Store(self.engine)
      store.add_fuel(fuel)
      store.set_wasi(wasi_config)

      instance = self.linker.instantiate(store, self.module)
      # why doesn't this get assigned in the instance constructor?
      # why should i need to pass it again here?
      exports = instance.exports(store)
      start   = exports['_start']
      memory  = exports['memory']

      start(store)

      with open(stdout_file) as file:
        stdout_content = file.read()

      with open(stderr_file) as file:
        stderr_content = file.read()

      return Result(
        stdout_content,
        stderr_content,
        memory.data_len(store),
        memory.size(store),
        store.fuel_consumed(),
      )
