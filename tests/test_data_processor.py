import unittest

from bot.processing import DataProcessor
from bot.processing import InvalidDataFormatException
from bot import constants


class DataProcessorTest(unittest.TestCase):

    def test_create_data_processor_with_invalid_data_type(self):
        with self.assertRaises(InvalidDataFormatException):
            DataProcessor.initialize(12345, constants.DATE_FORMAT)

    def test_create_data_processor_with_empty_list(self):
        try:
            dp = DataProcessor.initialize([], constants.DATE_FORMAT)
            self.assertEqual(dp.size(), 0)
        except Exception:
            self.fail("should not fail, empty data should be accepted")

    def test_create_data_process_from_json_empty_list(self):
        try:
            dp = DataProcessor.initialize("[]", constants.DATE_FORMAT)
            self.assertEqual(dp.size(), 0)
        except Exception:
            self.fail("should not fail, empty JSON data should be accepted")

    def test_create_data_processor_with_field_with_wrong_type(self):
        with self.assertRaises(InvalidDataFormatException):
            DataProcessor.initialize([{
                "data": "2020-02-28T18:00:00",
                "ricoverati_con_sintomi": "345",    # Wrong type, should be int
                "terapia_intensiva": 64,
                "totale_ospedalizzati": 409,
                "isolamento_domiciliare": 412,
                "totale_positivi": 821,
                "variazione_totale_positivi": 233,
                "nuovi_positivi": 238,
                "dimessi_guariti": 46,
                "deceduti": 21,
                "totale_casi": 888,
                "tamponi": 15695,
            }], constants.DATE_FORMAT)

    def test_create_data_processor_with_one_correct_entry(self):
        dp = DataProcessor.initialize([{
            "data": "2020-02-28T18:00:00",
            "ricoverati_con_sintomi": 345,
            "terapia_intensiva": 64,
            "totale_ospedalizzati": 409,
            "isolamento_domiciliare": 412,
            "totale_positivi": 821,
            "variazione_totale_positivi": 233,
            "nuovi_positivi": 238,
            "dimessi_guariti": 46,
            "deceduti": 21,
            "totale_casi": 888,
            "tamponi": 15695,
        }], constants.DATE_FORMAT)
        self.assertEqual(dp.size(), 1)

    def test_get_non_existing_property(self):
        dp = DataProcessor.initialize([{
            "data": "2020-02-28T18:00:00",
            "ricoverati_con_sintomi": 345,
            "terapia_intensiva": 64,
            "totale_ospedalizzati": 409,
            "isolamento_domiciliare": 412,
            "totale_positivi": 821,
            "variazione_totale_positivi": 233,
            "nuovi_positivi": 238,
            "dimessi_guariti": 46,
            "deceduti": 21,
            "totale_casi": 888,
            "tamponi": 15695,
        }], constants.DATE_FORMAT)
        with self.assertRaises(KeyError):
            dp.get("non-existing-key")

    def test_get_all_values_of_existing_property(self):
        dp = DataProcessor.initialize([{
            "data": "2020-02-24T18:00:00",
            "stato": "ITA",
            "ricoverati_con_sintomi": 101,
            "terapia_intensiva": 26,
            "totale_ospedalizzati": 127,
            "isolamento_domiciliare": 94,
            "totale_positivi": 221,
            "variazione_totale_positivi": 0,
            "nuovi_positivi": 221,
            "dimessi_guariti": 1,
            "deceduti": 7,
            "totale_casi": 229,
            "tamponi": 4324
        },
            {
            "data": "2020-02-25T18:00:00",
            "stato": "ITA",
            "ricoverati_con_sintomi": 114,
            "terapia_intensiva": 35,
            "totale_ospedalizzati": 150,
            "isolamento_domiciliare": 162,
            "totale_positivi": 311,
            "variazione_totale_positivi": 90,
            "nuovi_positivi": 93,
            "dimessi_guariti": 1,
            "deceduti": 10,
            "totale_casi": 322,
            "tamponi": 8623
        },
            {
            "data": "2020-02-26T18:00:00",
            "stato": "ITA",
            "ricoverati_con_sintomi": 128,
            "terapia_intensiva": 36,
            "totale_ospedalizzati": 164,
            "isolamento_domiciliare": 221,
            "totale_positivi": 385,
            "variazione_totale_positivi": 74,
            "nuovi_positivi": 78,
            "dimessi_guariti": 3,
            "deceduti": 12,
            "totale_casi": 400,
            "tamponi": 9587
        }], constants.DATE_FORMAT)
        self.assertEqual(
            dp.get("total_hospitalized_with_symptoms"), [101, 114, 128])
        self.assertEqual(dp.get("total_intensive_care"), [26, 35, 36])
        self.assertEqual(dp.get("total_hospitalized"), [127, 150, 164])
        self.assertEqual(dp.get("total_home_confinement"), [94, 162, 221])
        self.assertEqual(dp.get("total_active_positives"), [221, 311, 385])
        self.assertEqual(dp.get("delta_active_positives"), [0, 90, 74])
        self.assertEqual(dp.get("new_infected"), [221, 93, 78])
        self.assertEqual(dp.get("total_recovered"), [1, 1, 3])
        self.assertEqual(dp.get("total_deaths"), [7, 10, 12])
        self.assertEqual(dp.get("total_cases"), [229, 322, 400])
        self.assertEqual(dp.get("total_tests"), [4324, 8623, 9587])

    def test_get_partial_data(self):
        dp = DataProcessor.initialize([{
            "data": "2020-02-24T18:00:00",
            "stato": "ITA",
            "ricoverati_con_sintomi": 101,
            "terapia_intensiva": 26,
            "totale_ospedalizzati": 127,
            "isolamento_domiciliare": 94,
            "totale_positivi": 221,
            "variazione_totale_positivi": 0,
            "nuovi_positivi": 221,
            "dimessi_guariti": 1,
            "deceduti": 7,
            "totale_casi": 229,
            "tamponi": 4324
        },
            {
            "data": "2020-02-25T18:00:00",
            "stato": "ITA",
            "ricoverati_con_sintomi": 114,
            "terapia_intensiva": 35,
            "totale_ospedalizzati": 150,
            "isolamento_domiciliare": 162,
            "totale_positivi": 311,
            "variazione_totale_positivi": 90,
            "nuovi_positivi": 93,
            "dimessi_guariti": 1,
            "deceduti": 10,
            "totale_casi": 322,
            "tamponi": 8623
        },
            {
            "data": "2020-02-26T18:00:00",
            "stato": "ITA",
            "ricoverati_con_sintomi": 128,
            "terapia_intensiva": 36,
            "totale_ospedalizzati": 164,
            "isolamento_domiciliare": 221,
            "totale_positivi": 385,
            "variazione_totale_positivi": 74,
            "nuovi_positivi": 78,
            "dimessi_guariti": 3,
            "deceduti": 12,
            "totale_casi": 400,
            "tamponi": 9587
        }], constants.DATE_FORMAT)
        self.assertEqual(dp.get("total_tests", start=1), [8623, 9587])
        self.assertEqual(dp.get("total_tests", end=1), [4324])
        self.assertEqual(dp.get("total_tests", start=2, end=2), [])
        self.assertEqual(dp.get("total_tests", start=1, end=5), [8623, 9587])

    def test_create_data_processor_with_wrong_date_type_format(self):
        with self.assertRaises(InvalidDataFormatException):
            DataProcessor.initialize([{
                "data": "2020-02-28",
                "ricoverati_con_sintomi": "345",
                "terapia_intensiva": 64,
                "totale_ospedalizzati": 409,
                "isolamento_domiciliare": 412,
                "totale_positivi": 821,
                "variazione_totale_positivi": 233,
                "nuovi_positivi": 238,
                "dimessi_guariti": 46,
                "deceduti": 21,
                "totale_casi": 888,
                "tamponi": 15695,
            }], constants.DATE_FORMAT)

    def test_data_localization(self):
        dp = DataProcessor.initialize([{
            "data": "2020-02-26T18:00:00",
            "ricoverati_con_sintomi": 345,
            "terapia_intensiva": 64,
            "totale_ospedalizzati": 409,
            "isolamento_domiciliare": 412,
            "totale_positivi": 821,
            "variazione_totale_positivi": 233,
            "nuovi_positivi": 238,
            "dimessi_guariti": 46,
            "deceduti": 21,
            "totale_casi": 888,
            "tamponi": 15695,
        }], constants.DATE_FORMAT)
        self.assertIsNone(dp.get("date")[0].tzinfo)
        dp.localize_dates("UTC", "Europe/Rome")
        self.assertIsNotNone(dp.get("date")[0].tzinfo)


if __name__ == "__main__":
    unittest.main()
