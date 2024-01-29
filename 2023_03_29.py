import time
import PIL
import PIL.Image
import numpy
import cairocffi as cairo
import studio.media

def fire_blast() -> PIL.Image.Image:
  def hex_to_rgb(hex_color):
    r = int(hex_color[1:3], 16) / 255.0
    g = int(hex_color[3:5], 16) / 255.0
    b = int(hex_color[5:7], 16) / 255.0
    return (r, g, b)

  def rand_int(a, b=None):
    if b is None:
      a, b = 0, a
    return numpy.random.randint(a, b)

  surface = cairo.ImageSurface(cairo.FORMAT_RGB24, 4096, 4096)
  ctx = cairo.Context(surface)

  background = hex_to_rgb("#261426")
  ctx.set_source_rgb(*background)
  ctx.rectangle(0, 0, 4096, 4096)
  ctx.fill()

  palette = [
    hex_to_rgb(c) for c in [
      "#f2dac4",
      "#fff3e8",
      "#f2594b",
      "#f2594b",
      "#bf4949",
      "#bf4949",
    ]
  ]

  ctx.set_source_rgb(*hex_to_rgb("#f2dac4"))
  ctx.rectangle(64, 64, 4096-128, 4096-128)
  ctx.set_line_width(16)
  ctx.stroke()

  ctx.set_source_rgb(*hex_to_rgb("#594d48"))
  ctx.rectangle(128, 128, 4096-256, 4096-256)
  ctx.set_line_width(12)
  ctx.stroke()

  for i in range(724):
    ctx.save()
    ctx.translate(2048, 2048)
    ctx.rotate(rand_int(360))
    ctx.set_source_rgb(*palette[rand_int(len(palette))])
    ctx.rectangle(0, 0, 25 + i * 2, 25 + i * 2)
    ctx.set_line_width(rand_int(2, 32))
    dash = [rand_int(800) for _ in range(200)]
    ctx.set_dash(dash)
    ctx.stroke()
    ctx.restore()

  return studio.media.pil_from_cairo(surface)

if __name__ == '__main__':
  image = fire_blast()
  filename = f'{int(time.time())}.png'
  image.save(filename)
  print(filename)
