import subprocess
import xmltodict
import os
import logging

import wget

from iepy.utils import DIRS, unzip_file


logger = logging.getLogger(__name__)
_FOLDER = "stanford-corenlp-full-2014-08-27"
DOWNLOAD_URL = "http://nlp.stanford.edu/software/" + _FOLDER + ".zip"
COMMAND_PATH = os.path.join(DIRS.user_data_dir, _FOLDER, "corenlp.sh")


def get_analizer(*args, _singleton=[]):
    if not _singleton:
        logger.info("Loading StanfordCoreNLP...")
        _singleton.append(StanfordCoreNLP())
    return _singleton[0]


class StanfordCoreNLP:
    CORENLP_CMD = "-outputFormat xml -threads 4"
    PROMPT = b"\nNLP> "

    def __init__(self, tokenize_with_whitespace=False):
        cmd = self.CORENLP_CMD
        if tokenize_with_whitespace:
            cmd += " -tokenize.whitespace=true"
        args = [COMMAND_PATH] + cmd.split()
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
        self.output = self.iter_output_segments()
        self.receive()  # Wait until the prompt is ready

    def iter_output_segments(self):
        while True:
            buf = b""
            while self.PROMPT not in buf:
                buf += self.proc.stdout.read1(1024)
            segment, _, buf = buf.partition(self.PROMPT)
            yield segment.decode("utf8")

    def receive(self):
        return next(self.output)

    def send(self, data):
        data = data.replace("\n", " ") + "\n"
        self.proc.stdin.write(data.encode("utf8"))
        self.proc.stdin.flush()

    def analize(self, text):
        self.send(text)
        text = self.receive()
        i = text.index("<?xml version")
        text = text[i:]
        return xmltodict.parse(text)["root"]["document"]


def download():
    base = os.path.dirname(COMMAND_PATH)
    if os.path.isfile(COMMAND_PATH):
        logger.info("Stanford CoreNLP is already downloaded at {}.".format(base))
        return
    logger.info("Downloading Stanford CoreNLP...")

    if not os.path.exists(base):
        os.makedirs(base)

    zipfile = None
    try:
        zipfile = wget.download(DOWNLOAD_URL)
        unzip_file(zipfile, DIRS.user_data_dir)
    finally:
        if zipfile:
            os.remove(zipfile)
