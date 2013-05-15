#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Convert MOE dictionary data to gcin tsin file."""
import sys
import os
from multiprocessing import Pool
from subprocess import Popen
from subprocess import PIPE
from subprocess import call
import argparse


def download_json():
    fn = 'dict-revised.json'
    fn_unicode = 'dict-revised.unicode.json'
    sym_txt = 'sym.txt'
    json2unicode_pl = 'json2unicode.pl'
    if not os.path.exists(fn):
        p1 = Popen(["wget",
                   'http://kcwu.csie.org/~kcwu/moedict/dict-revised.json.bz2',
                   '-O', '-'], stdout=PIPE)
        p2 = Popen(['bunzip2'], stdin=p1.stdout, stdout=open(fn, "wb"))
        p1.stdout.close()
        p2.communicate()
        #call(['wget',
        #     'https://github.com/g0v/moedict-data/blob/master/dict-revised.json?raw=true']
        #     )
    if not os.path.exists(sym_txt):
        call(['wget',
             'https://github.com/g0v/moedict-epub/raw/master/sym.txt'])
    if not os.path.exists(json2unicode_pl):
        call(['wget',
             'https://github.com/g0v/moedict-epub/raw/master/json2unicode.pl'])
    if not os.path.exists(fn_unicode):
        p3 = Popen(['perl', './json2unicode.pl'],
                   stdout=open(fn_unicode, "wb"),
                   stderr=open('error.txt', "wb"))
        p3.communicate()
    return fn_unicode


def get_bopomofo(entry):
    if "heteronyms" in entry:
        for h in entry['heteronyms']:
            if "bopomofo" in h:
                return (entry['title'], h['bopomofo'])
    return (entry['title'], None)


def convert(moedict, parallel=True):
    result = []
    if parallel:
        pool = Pool()
        for k, d in pool.map(get_bopomofo, moedict):
            if d:
                result.append((k, d))
    else:
        for k, d in map(get_bopomofo, moedict):
            if d:
                result.append((k, d))
    return result


def transform_checked_tone(us):
    ul = []
    found = False
    for uc in us:
        if uc == u'˙':
            found = True
        elif found and uc == u' ':
            ul.append(u'1')
            ul.append(uc)
            found = False
        else:
            ul.append(uc)
    return u"".join(ul)


def transform_phonetic(s):
    return transform_checked_tone(s).replace(u'ˊ', u'2').replace(
        u'ˇ', u'3').replace(u'ˋ', u'4')


def convert_from_json(fn, output_fd):
    import json
    moedict = json.load(open(fn, "rt"))
    result = convert([
        entry for entry in moedict if '{[' not in entry['title'] and len(entry['title'])>1])
    for title, bopomofo in result:
        output_fd.write(u"{0} {1} 0\n".format(
            title, transform_phonetic(bopomofo)).encode('utf-8'))


def main(args):
    convert_from_json(download_json(), args.output_fd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert moedict to gcin tsin file.')
    parser.add_argument("-o", "--output", dest="output_fd",
            help="write tabfile to FILE", metavar="FILE",
            type=argparse.FileType('wt'), required=True)
    args = parser.parse_args()

    main(args)
