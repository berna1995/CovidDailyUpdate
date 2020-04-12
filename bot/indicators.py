from abc import ABC, abstractmethod


class Indicator(ABC):
    def __init__(self, data: list):
        if data is None:
            raise ValueError
        self._data = data

    @abstractmethod
    def calculate(self, i: int):
        pass

    def get_all(self):
        return list(map(lambda i: self.calculate(i), range(0, len(self._data))))

    def get_last(self):
        return self.calculate(len(self._data) - 1)

    def _check_range(self, i: int):
        if i < 0 or i >= len(self._data):
            raise IndexError


class MovingAverageIndicator(Indicator):

    def __init__(self, data, period: int):
        super().__init__(data)
        if period <= 0:
            raise ValueError
        self.__period = period

    def calculate(self, i):
        self._check_range(i)
        start = i + 1 - self.__period
        if start < 0:
            return float("NaN")
        data_sum = sum(self._data[start:i + 1])
        return data_sum / self.__period


class DeltaIndicator(Indicator):

    def __init__(self, data):
        super().__init__(data)

    def calculate(self, i):
        self._check_range(i)
        if i == 0:
            return self._data[0]
        else:
            return self._data[i] - self._data[i - 1]
