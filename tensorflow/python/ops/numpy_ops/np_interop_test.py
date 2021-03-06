# Copyright 2020 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for interop between TF ops, numpy_ops, and numpy methods."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


from tensorflow.python.eager import backprop
from tensorflow.python.eager import def_function
from tensorflow.python.framework import ops
from tensorflow.python.ops import control_flow_ops
from tensorflow.python.ops.numpy_ops import np_array_ops
from tensorflow.python.ops.numpy_ops import np_arrays
from tensorflow.python.platform import test


class InteropTest(test.TestCase):

  def testGradientTapeInterop(self):
    with backprop.GradientTape() as t:
      x = np_array_ops.asarray(3.0)
      y = np_array_ops.asarray(2.0)

      t.watch([x, y])

      xx = 2 * x
      yy = 3 * y

    dx, dy = t.gradient([xx, yy], [x, y])

    # TODO(nareshmodi): Gradient tape returns tensors. Is it possible to rewrap?
    self.assertAllClose(dx, 2.0)
    self.assertAllClose(dy, 3.0)

  def testFunctionInterop(self):
    x = np_array_ops.asarray(3.0)
    y = np_array_ops.asarray(2.0)

    add = lambda x, y: x + y
    add_fn = def_function.function(add)

    raw_result = add(x, y)
    fn_result = add_fn(x, y)

    self.assertIsInstance(raw_result, np_arrays.ndarray)
    self.assertIsInstance(fn_result, np_arrays.ndarray)
    self.assertAllClose(raw_result, fn_result)

  def testCondInterop(self):
    x = np_array_ops.asarray(3.0)

    def fn(x):
      x_plus_1 = control_flow_ops.cond(x > 0, lambda: x+1, lambda: x+2)
      x_plus_2 = control_flow_ops.cond(x < 0, lambda: x+1, lambda: x+2)

      return x_plus_1, x_plus_2

    raw_x_plus_1, raw_x_plus_2 = fn(x)
    fn_x_plus_1, fn_x_plus_2 = def_function.function(fn)(x)

    self.assertAllClose(raw_x_plus_1, x + 1)
    self.assertAllClose(raw_x_plus_2, x + 2)

    self.assertAllClose(fn_x_plus_1, x + 1)
    self.assertAllClose(fn_x_plus_2, x + 2)

  def testWhileInterop(self):
    def fn():
      x = np_array_ops.asarray(0)
      c = lambda x: x < 10000
      b = lambda x: [x + 1]
      return control_flow_ops.while_loop_v2(c, b, [x], parallel_iterations=20)

    self.assertEqual(10000, fn()[0])
    self.assertEqual(10000, def_function.function(fn)()[0])


if __name__ == '__main__':
  ops.enable_eager_execution()
  test.main()
