#!/usr/bin/python3

import sys
from efilter import *
from kanjidic2 import *
from langs import *

def processGloss(lang, match, glosses):
	if not lang in glosses: gloss = ''
	else: gloss = glosses[lang]
	gloss += match + '\n'
	glosses[lang] = gloss

class Kanjidic2Filter(Filter):
	def __init__(self, basename, langs):
		Filter.__init__(self, basename, langs, "kanjidic2 i18n", "Alexandre Courbot <gnurou@gmail.com>")

	def processEntry(self, kentry):
		cpt = 0
		for group in kentry.groups:
			glosses = group.glosses
			# Dump all meanings
			if 'en' in glosses: enGlosses = glosses['en']
			else: return False
			msgctxt = '%s %d' % (kentry.literal, cpt)
			if len(group.readings) > 0: msgid = '%s\n%s\n' % (kentry.literal, ", ".join(group.readings)) + enGlosses
			else: msgid = '%s\n' % (kentry.literal,) + enGlosses
			for lang in self.langs:
				f = self.files[lang]
				entry = GetTextEntry(lang)
				entry.msgctxt = msgctxt
				entry.msgid = msgid.rstrip('\n')
				if lang == 'en' or not lang in glosses: entry.msgstr = ''
				else: entry.msgstr = glosses[lang].rstrip('\n')
				f.write(str(entry))
			cpt += 1
		return True

class GradeFilter(Kanjidic2Filter):
	def __init__(self, langs, grade):
		Kanjidic2Filter.__init__(self, 'kanjidic2-grade%d' % (grade,), langs)
		self.grade = grade

	def processEntry(self, kentry):
		if kentry.grade == self.grade: return Kanjidic2Filter.processEntry(self, kentry)
		else: return False

class FreqFilter(Kanjidic2Filter):
	def __init__(self, langs):
		Kanjidic2Filter.__init__(self, "kanjidic2-freq", langs)

	def processEntry(self, kentry):
		if kentry.freq > 0: return Kanjidic2Filter.processEntry(self, kentry)
		else: return False

class AllFilter(Kanjidic2Filter):
	def __init__(self, langs):
		Kanjidic2Filter.__init__(self, "kanjidic2-others", langs)

if __name__ == "__main__":
	kdic = open(sys.argv[1], 'r', encoding='utf-8')

	filters = []
	for i in range(1, 7):
		filters.append(GradeFilter(langs, i))
	for i in range(8, 11):
		filters.append(GradeFilter(langs, i))
	filters.append(FreqFilter(langs))
	filters.append(AllFilter(langs))

	while True:
		l = kdic.readline()
		match = enMeaningRe.match(l)
		if match:
			processGloss('en', match.group(1), glosses)
			continue
		match = otherMeaningRe.match(l)
		if match:
			processGloss(match.group(1), match.group(2), glosses)
			continue
		match = rmgroupEndRe.match(l)
		if match:
			rmgroup.glosses = glosses
			kentry.groups.append(rmgroup)
			glosses = {}
			continue
		match = readingRe.match(l)
		if match and match.group(1) in ( 'ja_on', 'ja_kun'):
			rmgroup.readings.append(match.group(2))
		match = gradeRe.match(l)
		if match:
			kentry.grade = int(match.group(1))
		match = freqRe.match(l)
		if match:
			kentry.freq = int(match.group(1))
		match = literalRe.match(l)
		if match:
			kentry = KEntry(match.group(1))
			rmgroup = RMGroup()
			glosses = {}
			continue
		match = entryEndRe.match(l)
		if match:
			for filt in filters:
				if filt.processEntry(kentry): break
		if len(l) == 0: break
