import unittest
import math

from bot.indicators import MovingAverageIndicator
from bot.indicators import DeltaIndicator
from bot.indicators import DeltaPercentageIndicator


class MovingAverageIndicatorTest(unittest.TestCase):

    def test_moving_average_period_3(self):
        mai = MovingAverageIndicator([1, 2, 3], 3)
        self.assertTrue(math.isnan(mai.calculate(0)))
        self.assertTrue(math.isnan(mai.calculate(1)))
        self.assertAlmostEqual(mai.calculate(2), 2.0)

    def test_moving_average_period_1(self):
        mai = MovingAverageIndicator([3, 4, 5, 6, 7], 1)
        self.assertEqual(mai.get_all(), [3, 4, 5, 6, 7])

    def test_moving_average_last_value(self):
        mai = MovingAverageIndicator([2, 4, 6, 8.5, 10], 3)
        self.assertAlmostEqual(mai.get_last(), 8.16, delta=0.01)

    def test_moving_average_with_invalid_periods(self):
        with self.assertRaises(ValueError):
            mai = MovingAverageIndicator([1, 2, 3], 0)
        with self.assertRaises(ValueError):
            mai = MovingAverageIndicator([1, 2, 3], -1)

    def test_moving_average_with_period_major_than_data_size(self):
        mai = MovingAverageIndicator([1, 2, 3], 4)
        vals = mai.get_all()
        for val in vals:
            self.assertTrue(math.isnan(val))

    def test_moving_average_calculate_out_of_range(self):
        mai = MovingAverageIndicator([1, 2, 3], 2)
        with self.assertRaises(IndexError):
            mai.calculate(-1)
        with self.assertRaises(IndexError):
            mai.calculate(3)

    def test_moving_average_with_none_list(self):
        with self.assertRaises(ValueError):
            mai = MovingAverageIndicator(None, 2)


class DeltaIndicatorTest(unittest.TestCase):

    def test_delta_calculate_out_of_range(self):
        di = DeltaIndicator([0, 1, 2])
        with self.assertRaises(IndexError):
            di.calculate(-1)
        with self.assertRaises(IndexError):
            di.calculate(3)

    def test_delta_calculate_with_none_list(self):
        with self.assertRaises(ValueError):
            di = DeltaIndicator(None)

    def test_delta_calculate_all(self):
        di = DeltaIndicator([1, 2, 3])
        self.assertEqual(di.get_all(), [1, 1, 1])

    def test_delta_calculate_last(self):
        di = DeltaIndicator([10, 20, 30])
        self.assertEqual(di.get_last(), 10)


class DeltaPercentageIndicatorTest(unittest.TestCase):

    def test_delta_percentage_calculate_out_of_range(self):
        dpi = DeltaPercentageIndicator([0, 1, 2])
        with self.assertRaises(IndexError):
            dpi.calculate(-1)
        with self.assertRaises(IndexError):
            dpi.calculate(3)

    def test_delta_percentage_calculate_with_none_list(self):
        with self.assertRaises(ValueError):
            dpi = DeltaPercentageIndicator(None)

    def test_delta_calculate_all_positives_change(self):
        dpi = DeltaPercentageIndicator([19, 25, 55])
        self.assertAlmostEqual(dpi.calculate(0), 0, delta=0.01)
        self.assertAlmostEqual(dpi.calculate(1), 31.57, delta=0.01)
        self.assertAlmostEqual(dpi.calculate(2), 120, delta=0.01)

    def test_delta_calculate_positives_and_negative_changes(self):
        dpi = DeltaPercentageIndicator([15, 20, 5])
        self.assertAlmostEqual(dpi.calculate(0), 0, delta=0.01)
        self.assertAlmostEqual(dpi.calculate(1), 33.33, delta=0.01)
        self.assertAlmostEqual(dpi.calculate(2), -75, delta=0.01)


if __name__ == "__main__":
    unittest.main()
