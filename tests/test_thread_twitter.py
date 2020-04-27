import unittest
import random
import string
from unittest.mock import Mock
from unittest.mock import create_autospec
from bot.twitter import ThreadTwitter
from bot.twitter import MediaType
from twitter.api import CHARACTER_LIMIT


class MockStatus:

    current_id = 0

    def __init__(self, id):
        self.id = id

    @staticmethod
    def new():
        mocked_status = MockStatus(MockStatus.current_id)
        MockStatus.current_id = MockStatus.current_id + 1
        return mocked_status


def side_effect(*args, **kwargs):
    return MockStatus.new()


def create_mock():
    tt = ThreadTwitter(None, None, None, None)
    mock = create_autospec(
        tt._ThreadTwitter__api.PostUpdate, side_effect=side_effect)
    tt._ThreadTwitter__api.PostUpdate = mock
    return tt, mock


def random_string(string_length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(string_length))


class ThreadTwitterTest(unittest.TestCase):

    def setUp(self):
        MockStatus.current_id = 0

    def test_set_header_too_long(self):
        tt, mock = create_mock()
        with self.assertRaises(ValueError):
            tt.set_header(random_string(ThreadTwitter.HEADER_MAX_LENGTH + 1))

    def test_set_footer_too_long(self):
        tt, mock = create_mock()
        with self.assertRaises(ValueError):
            tt.set_footer(random_string(ThreadTwitter.FOOTER_MAX_LENGTH + 1))

    def test_set_repeating_header(self):
        tt, mock = create_mock()
        hdr = "HEADER"
        line_1 = "First line"
        line_2 = "Second line"
        tt.set_header(hdr, repeat=True)
        tt.add_line(line_1)
        tt.add_line(line_2, force_new_tweet=True)
        tt.tweet()

        calls = mock.call_args_list
        self.assertEqual(2, len(calls))
        self.assertTrue(hdr in calls[0].args[0])
        self.assertTrue(calls[0].kwargs["in_reply_to_status_id"] is None)
        self.assertTrue(line_1 in calls[0].args[0])
        self.assertFalse(line_2 in calls[0].args[0])
        self.assertTrue(hdr in calls[1].args[0])
        self.assertEqual(calls[1].kwargs["in_reply_to_status_id"], 0)
        self.assertFalse(line_1 in calls[1].args[0])
        self.assertTrue(line_2 in calls[1].args[0])

    def test_non_repeating_header(self):
        tt, mock = create_mock()
        hdr = "HEADER"
        line_1 = "First line"
        line_2 = "Second line"
        tt.set_header(hdr, repeat=False)
        tt.add_line(line_1)
        tt.add_line(line_2, force_new_tweet=True)
        tt.tweet()

        calls = mock.call_args_list
        self.assertEqual(2, len(calls))
        self.assertTrue(hdr in calls[0].args[0])
        self.assertTrue(calls[0].kwargs["in_reply_to_status_id"] is None)
        self.assertTrue(line_1 in calls[0].args[0])
        self.assertFalse(line_2 in calls[0].args[0])
        self.assertFalse(hdr in calls[1].args[0])
        self.assertEqual(calls[1].kwargs["in_reply_to_status_id"], 0)
        self.assertFalse(line_1 in calls[1].args[0])
        self.assertTrue(line_2 in calls[1].args[0])

    def test_repeating_footer(self):
        tt, mock = create_mock()
        ftr = "FOOTER"
        line_1 = "First line"
        line_2 = "Second line"
        tt.set_footer(ftr, repeat=True)
        tt.add_line(line_1)
        tt.add_line(line_2, force_new_tweet=True)
        tt.tweet()

        calls = mock.call_args_list
        self.assertEqual(2, len(calls))
        self.assertTrue(ftr in calls[0].args[0])
        self.assertTrue(calls[0].kwargs["in_reply_to_status_id"] is None)
        self.assertTrue(line_1 in calls[0].args[0])
        self.assertFalse(line_2 in calls[0].args[0])
        self.assertTrue(ftr in calls[1].args[0])
        self.assertEqual(calls[1].kwargs["in_reply_to_status_id"], 0)
        self.assertFalse(line_1 in calls[1].args[0])
        self.assertTrue(line_2 in calls[1].args[0])

    def test_non_repeating_footer(self):
        tt, mock = create_mock()
        ftr = "FOOTER"
        line_1 = "First line"
        line_2 = "Second line"
        line_3 = "Third line"
        tt.set_footer(ftr, repeat=False)
        tt.add_line(line_1)
        tt.add_line(line_2, force_new_tweet=True)
        tt.add_line(line_3, force_new_tweet=True)
        tt.tweet()

        calls = mock.call_args_list
        self.assertEqual(3, len(calls))

        self.assertFalse(ftr in calls[0].args[0])
        self.assertTrue(calls[0].kwargs["in_reply_to_status_id"] is None)
        self.assertTrue(line_1 in calls[0].args[0])

        self.assertFalse(ftr in calls[1].args[0])
        self.assertEqual(calls[1].kwargs["in_reply_to_status_id"], 0)
        self.assertTrue(line_2 in calls[1].args[0])

        self.assertTrue(ftr in calls[2].args[0])
        self.assertEqual(calls[2].kwargs["in_reply_to_status_id"], 1)
        self.assertTrue(line_3 in calls[2].args[0])

    def test_tweet_splitting_correctly(self):
        tt, mock = create_mock()
        hdr = "HEADER"
        ftr = "FOOTER"
        long_msg_1 = random_string(ThreadTwitter.LINE_MAX_LENGTH)
        long_msg_2 = random_string(ThreadTwitter.LINE_MAX_LENGTH)
        tt.set_header(hdr, repeat=False)
        tt.set_footer(ftr, repeat=False)
        tt.add_line(long_msg_1)
        tt.add_line(long_msg_2)
        tt.tweet()

        calls = mock.call_args_list
        self.assertEqual(2, len(calls))

        self.assertTrue(calls[0].kwargs["in_reply_to_status_id"] is None)
        self.assertTrue(hdr in calls[0].args[0])
        self.assertFalse(ftr in calls[0].args[0])
        self.assertTrue(long_msg_1 in calls[0].args[0])
        self.assertFalse(long_msg_2 in calls[0].args[0])

        self.assertEqual(calls[1].kwargs["in_reply_to_status_id"], 0)
        self.assertFalse(hdr in calls[1].args[0])
        self.assertTrue(ftr in calls[1].args[0])
        self.assertFalse(long_msg_1 in calls[1].args[0])
        self.assertTrue(long_msg_2 in calls[1].args[0])

    def test_ignoring_force_new_on_first_line(self):
        tt, mock = create_mock()
        tt.add_line("line")
        tt.tweet()

        calls = mock.call_args_list
        self.assertEqual(1, len(calls))

    def test_tweet_limits(self):
        tt, mock = create_mock()
        hdr = random_string(ThreadTwitter.HEADER_MAX_LENGTH)
        ftr = random_string(ThreadTwitter.FOOTER_MAX_LENGTH)
        msg = random_string(ThreadTwitter.LINE_MAX_LENGTH)
        tt.set_header(hdr)
        tt.set_footer(ftr)
        tt.add_line(msg)
        tt.tweet()

        calls = mock.call_args_list
        self.assertEqual(1, len(calls))
        self.assertLessEqual(len(calls[0].args[0]), CHARACTER_LIMIT)

    def test_tweet_with_media_only(self):
        tt, mock = create_mock()
        media_file_ref = "file1.jpg"
        tt.add_media(media_file_ref, MediaType.PHOTO)
        tt.tweet()

        calls = mock.call_args_list
        self.assertEqual(1, len(calls))
        self.assertTrue("Service tweet" in calls[0].args[0])
        self.assertTrue(media_file_ref in calls[0].kwargs["media"])

    def test_tweet_with_more_media_than_text_tweets(self):
        tt, mock = create_mock()
        media1 = "file1.jpg"
        media2 = "file.mov"
        txt = "My Text Content"

        tt.add_line(txt)
        tt.add_media(media1, MediaType.PHOTO)
        tt.add_media(media2, MediaType.VIDEO)
        tt.tweet()

        calls = mock.call_args_list
        self.assertEqual(2, len(calls))
        self.assertTrue(txt in calls[0].args[0])
        self.assertTrue("Service tweet" in calls[1].args[0])
        self.assertEqual(1, len(calls[0].kwargs["media"]))
        self.assertTrue(media1 in calls[0].kwargs["media"])
        self.assertEqual(1, len(calls[1].kwargs["media"]))
        self.assertTrue(media2 in calls[1].kwargs["media"])

    def test_subsequent_photo_aggregation(self):
        tt, mock = create_mock()
        media1 = "file1.jpg"
        media2 = "file2.jpg"
        media3 = "file3.jpg"
        media4 = "file.gif"
        media5 = "file4.jpg"
        tt.add_line("Line1")
        tt.add_line("Line2", force_new_tweet=True)
        tt.add_line("Line3", force_new_tweet=True)
        tt.add_line("Line4", force_new_tweet=True)
        tt.add_media(media1, MediaType.PHOTO)
        tt.add_media(media2, MediaType.PHOTO)
        tt.add_media(media3, MediaType.PHOTO)
        tt.add_media(media4, MediaType.GIF)
        tt.add_media(media5, MediaType.PHOTO)
        tt.tweet()

        calls = mock.call_args_list
        self.assertEqual(4, len(calls))
        self.assertEqual(3, len(calls[0].kwargs["media"]))
        self.assertTrue(media1 in calls[0].kwargs["media"])
        self.assertTrue(media2 in calls[0].kwargs["media"])
        self.assertTrue(media3 in calls[0].kwargs["media"])
        self.assertEqual(1, len(calls[1].kwargs["media"]))
        self.assertTrue(media4 in calls[1].kwargs["media"])
        self.assertEqual(1, len(calls[2].kwargs["media"]))
        self.assertTrue(media5 in calls[2].kwargs["media"])


if __name__ == "__main__":
    unittest.main()
