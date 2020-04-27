import twitter
from twitter.api import CHARACTER_LIMIT
from enum import Enum


class MediaType(Enum):
    PHOTO = 1,
    GIF = 2,
    VIDEO = 3


class ThreadTwitter:

    HEADER_MAX_LENGTH = 40
    FOOTER_MAX_LENGTH = 40
    LINE_MAX_LENGTH = CHARACTER_LIMIT - HEADER_MAX_LENGTH - FOOTER_MAX_LENGTH - 4

    def __init__(self, consumer_key, consumer_secret, access_token_key, access_token_secret):
        self.__header = None
        self.__repeat_header = False
        self.__footer = None
        self.__repeat_footer = False
        self.__lines = []
        self.__media = []
        self.__api = twitter.Api(
            consumer_key, consumer_secret, access_token_key, access_token_secret, sleep_on_rate_limit=True, tweet_mode="extended")

    def set_header(self, header: str, repeat=True):
        if header is None:
            self.__header = None
            return
        if len(header) > ThreadTwitter.HEADER_MAX_LENGTH:
            raise ValueError(
                "len(header) must be < ThreadTwitter.HEADER_MAX_LENGTH")
        self.__header = header + "\n\n"
        self.__repeat_header = repeat

    def set_footer(self, footer: str, repeat=True):
        if footer is None:
            self.__footer = None
            self.__repeat_footer = False
            return
        if len(footer) > ThreadTwitter.HEADER_MAX_LENGTH:
            raise ValueError(
                "len(footer) must be < ThreadTwitter.FOOTER_MAX_LENGTH")
        self.__footer = "\n" + footer
        self.__repeat_footer = repeat

    def add_line(self, line: str, force_new_tweet=False):
        if len(line) > ThreadTwitter.LINE_MAX_LENGTH:
            raise ValueError(
                "len(line) must be < ThreadTwitter.LINE_MAX_LENGTH")
        if len(self.__lines) == 0:
            force_new_tweet = False
        tup = (line + "\n", force_new_tweet)
        self.__lines.append(tup)

    def add_media(self, media, media_type: MediaType):
        self.__media.append((media, media_type))

    def tweet(self):
        tweet_texts = []
        current_tweet = None
        if not self.__repeat_footer and self.__footer is not None:
            self.__lines.append((self.__footer, False))

        for i in range(len(self.__lines)):
            line, force_new = self.__lines[i]
            if current_tweet is None:
                current_tweet = self.__prep_new_tweet_text(len(tweet_texts))
            if force_new or not self.__can_add_line_in_tweet(current_tweet, line):
                tweet_texts.append(
                    self.__append_footer_if_needed(current_tweet).strip())
                current_tweet = self.__prep_new_tweet_text(len(tweet_texts))
            current_tweet = current_tweet + line
            if i == len(self.__lines) - 1:
                tweet_texts.append(
                    self.__append_footer_if_needed(current_tweet).strip())

        if not self.__repeat_footer and self.__footer is not None:
            self.__lines.pop()

        tweets = []

        media_index = 0
        for i in range(len(tweet_texts)):
            medias = []
            if media_index < len(self.__media):
                medias = self.__get_next_medias(media_index)
                media_index = media_index + len(medias)
            if len(medias) == 0:
                medias = None
            tweets.append((tweet_texts[i], medias))

        while media_index < len(self.__media):
            medias = self.__get_next_medias(media_index)
            media_index = media_index + len(medias)
            if len(medias) == 0:
                medias = None
            tweets.append(("Service tweet", medias))

        status_id_reply = None
        for tweet_txt, tweet_media in tweets:
            status = self.__api.PostUpdate(
                tweet_txt, media=tweet_media, in_reply_to_status_id=status_id_reply, auto_populate_reply_metadata=False)
            status_id_reply = status.id

    def __get_next_medias(self, index):
        medias = []
        media, media_type = self.__media[index]
        if media_type == MediaType.VIDEO or media_type == MediaType.GIF:
            medias.append(media)
        elif media_type == MediaType.PHOTO:
            for i in range(min(index, len(self.__media) - 1), min(index + 4, len(self.__media))):
                if self.__media[i][1] == MediaType.PHOTO:
                    medias.append(self.__media[i][0])
                else:
                    break
        return medias

    def __prep_new_tweet_text(self, tweet_num):
        if (tweet_num == 0 or self.__repeat_header) and (self.__header is not None):
            return self.__header
        else:
            return ""

    def __can_add_line_in_tweet(self, current_tweet, new_line):
        footer_size = len(
            self.__footer) if self.__repeat_footer and self.__footer is not None else 0
        return len(current_tweet) + len(new_line) + footer_size <= CHARACTER_LIMIT

    def __append_footer_if_needed(self, current_tweet):
        if self.__repeat_footer and self.__footer is not None:
            return current_tweet + self.__footer
        else:
            return current_tweet
