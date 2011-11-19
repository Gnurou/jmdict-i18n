#!/usr/bin/python3

from efilter import *
from kanjidic2 import *

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

class KyouikuFilter(Kanjidic2Filter):
	def __init__(self, langs):
		Kanjidic2Filter.__init__(self, "kanjidic2-kyouiku", langs)

	def processEntry(self, kentry):
		if kentry.grade > 0 and kentry.grade <= 6: return Kanjidic2Filter.processEntry(self, kentry)
		else: return False

class JouyouFilter(Kanjidic2Filter):
	def __init__(self, langs):
		Kanjidic2Filter.__init__(self, "kanjidic2-jouyou", langs)

	def processEntry(self, kentry):
		if kentry.grade > 6 and kentry.grade <= 8: return Kanjidic2Filter.processEntry(self, kentry)
		else: return False

class FreqFilter(Kanjidic2Filter):
	def __init__(self, langs):
		Kanjidic2Filter.__init__(self, "kanjidic2-freq", langs)

	def processEntry(self, kentry):
		if kentry.freq > 0: return Kanjidic2Filter.processEntry(self, kentry)
		else: return False

class JinmeiFilter(Kanjidic2Filter):
	def __init__(self, langs):
		Kanjidic2Filter.__init__(self, "kanjidic2-jinmei", langs)

	def processEntry(self, kentry):
		if kentry.grade > 8: return Kanjidic2Filter.processEntry(self, kentry)
		else: return False

class AllFilter(Kanjidic2Filter):
	def __init__(self, langs):
		Kanjidic2Filter.__init__(self, "kanjidic2-others", langs)

if __name__ == "__main__":
	kdic = open('kanjidic2.xml', 'r', encoding='utf-8')

	filters = []
	langs = [ 'en', 'fr', 'es', 'pt' ]
	filters.append(KyouikuFilter(langs))
	filters.append(JouyouFilter(langs))
	filters.append(FreqFilter(langs))
	filters.append(JinmeiFilter(langs))
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
