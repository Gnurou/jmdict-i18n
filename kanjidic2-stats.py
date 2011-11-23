#!/usr/bin/python3

import sys
from kanjidic2 import *

def parseKanjidicFile(f):
	meanings = {}
	while True:
		l = f.readline()
		match = literalRe.match(l)
		if match:
			literal = match.group(1)
			rmgroup = 0
		match = rmgroupEndRe.match(l)
		if match:
			rmgroup += 1
		match = otherMeaningRe.match(l)
		if match:
			lang = match.group(1)
			if not lang in meanings:
				meanings[lang] = []
			meanings[lang].append((literal, rmgroup))
		if len(l) == 0: break
	return meanings

if __name__ == "__main__":
	kdic = open(sys.argv[1], 'r', encoding='utf-8')
	kdic2 = open(sys.argv[2], 'r', encoding='utf-8')
	meanings = parseKanjidicFile(kdic)
	meanings2 = parseKanjidicFile(kdic2)

	allLangs = set(list(meanings.keys()) + list(meanings2.keys()))
	for lang in allLangs:
		if lang in meanings: l1 = set(meanings[lang])
		else: l1 = set()
		if lang in meanings2: l2 = set(meanings2[lang])
		else: l2 = set()
		print("%s: %5d %5d (%d new, %d regressions)" % (lang, len(l1), len(l2), len(l2 - l1), len(l1 - l2)))