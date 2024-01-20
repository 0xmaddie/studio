import PIL
import PIL.Image

import IPython

import time
import math
import tqdm
import array
import requests
import hashlib

import cairocffi as cairo

from typing import Optional
from typing import Callable

def render_video(
  source: str = 'source.raw',
  target: str = 'target.webm',
  height: int = 512,
  width: int = 512,
  framerate: int = 15,
) -> IPython.display.DisplayObject:
  if target.endswith('.gif'):
    parts = [
      f'ffmpeg',
      f'-f rawvideo',
      f'-pix_fmt bgra',
      f'-r {framerate}',
      f'-s {width}x{height}',
      f'-i {source}',
      f'{target}',
    ]
    command = ' '.join(parts)
    os.system(command)
    image = IPython.display.Image(filename=target)
    return image
  elif ( False
    or target.endswith('.webm')
    or target.endswith('.mp4')
  ):
    parts = [
      f'ffmpeg',
      f'-f rawvideo',
      f'-pix_fmt bgra',
      f'-r {framerate}',
      f'-s {width}x{height}',
      f'-i {source}',
      f'-pix_fmt yuv420p',
      f'{target}',
    ]
    command = ' '.join(parts)
    os.system(command)
    video = IPython.display.Video(target, embed=True)
    return video
  else:
    raise ValueError(f'''                                                                                                                                                                       
Cannot render a video to the following target:                                                                                                                                                  
                                                                                                                                                                                                
{target}                                                                                                                                                                                        
'''.strip())

def fetch_image(url: str) -> PIL.Image.Image:
  bits = requests.get(url, stream=True).raw
  return PIL.Image.open(bits)

def cat_image(images: list[PIL.Image.Image], rows: int, cols: int):
  assert len(images) == rows * cols

  width, height = images[0].size
  grid = PIL.Image.new(
    'RGB',
    size=(cols * width, rows * height),
  )

  for index, image in enumerate(images):
    box = (index % cols * width, index // cols * height)
    grid.paste(image, box=box)

  return grid

def scale_image(image: PIL.Image.Image, factor: float) -> PIL.Image.Image:
  width  = int(image.width  * factor)
  height = int(image.height * factor)
  return image.resize((width, height), PIL.Image.ANTIALIAS)

def sha256(value) -> str:
  if isinstance(value, str):
    return hashlib.sha256(value.encode()).hexdigest()
  elif isinstance(value, PIL.Image.Image):
    return hashlib.sha256(value.tobytes()).hexdigest()
  else:
    raise ValueError(f'''
Cannot compute the SHA256 hash of the following value:

{value}
'''.strip())

def pil_from_cairo(surface: cairo.ImageSurface) -> PIL.Image.Image:
  buf = surface.get_data()
  width = surface.get_width()
  height = surface.get_height()
  stride = surface.get_stride()
  return PIL.Image.frombuffer("RGBA", (width, height), buf, "raw", "BGRA", stride)

def cairo_from_pil(image: PIL.Image.Image) -> cairo.ImageSurface:
  if image.mode != 'RGBA':
    image = image.convert('RGBA')
  data = array.array('B', image.tobytes())
  surface = cairo.ImageSurface.create_for_data(
    data,
    cairo.FORMAT_ARGB32,
    image.width,
    image.height,
  )
  return surface
