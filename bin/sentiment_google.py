from typing import Dict


from google.cloud import language
from google.cloud.language import enums, types
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/pi/cloud_speech.json'


class SentimentGoogle:
    """ Google の Cloud Natural Language API を利用して文章のネガポジ判定を行います。
    """

    def __init__(self):
        pass

    def sentiment(self, text: str) -> Dict:
        """ 入力した文章に対するネガポジの値を返します。

        Parameter
        ---
        text : str
            Sentences to analyze.
        """
        result = _analyze(text)
        response = _convert_response(result)
        response["text"] = text
        return response


def _analyze(text: str):
    """ Analyze sentiment of text using cloud native language api.

    Parameter
    ---
    text : str
        Sentences to analyze.
    """
    client = language.LanguageServiceClient()
    document = types.Document(content=text, type=enums.Document.Type.PLAIN_TEXT)
    result = client.analyze_sentiment(document=document)
    return result


def _convert_response(result) -> Dict:
    """ Convert from result of cloud native language api to python dict.

    Parameter
    ---
    result
        Result of cloud native language api.
    """
    response = {
        "score": result.document_sentiment.score,
        "magnitude": result.document_sentiment.magnitude,
        "language": result.language,
        "sentences": [],
    }
    for sentence in result.sentences:
        child_response = {
            "text": sentence.text.content,
            "score": sentence.sentiment.score,
            "magnitude": sentence.sentiment.magnitude,
        }
        response["sentences"].append(child_response)
    return response


if __name__ == '__main__':
    response = SentimentGoogle().sentiment("美味しかった")
    print("response", response)
