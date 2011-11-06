#!/usr/bin/python3

from gettextformat import *
from kanjidic2 import *

# PO header
headerStr = """Project-Id-Version: kanjidic2 i18n
Report-Msgid-Bugs-To: Alexandre Courbot <gnurou@gmail.com>
POT-Creation-Date: 2011-11-05 19:00:00+09:00
PO-Revision-Date: 
Last-Translator: 
Language-Team: 
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Language: %s"""

def processGloss(lang, match, glosses):
	if not lang in glosses: gloss = ''
	else: gloss = glosses[lang]
	gloss += match + '\n'
	glosses[lang] = gloss

class Filter:
	def __init__(self, basename, langs):
		self.basename = basename
		self.langs = langs
		self.files = {}
		for lang in langs:
			if lang == 'en': fstr = "%s.pot" % (self.basename,)
			else: fstr = "%s_%s.po" % (self.basename, lang)
			f = open(fstr, 'w', encoding='utf-8')
			entry = GetTextEntry()
			entry.msgstr = headerStr % (lang,)
			f.write(str(entry))
			self.files[lang] = f

	def processEntry(self, kentry):
		cpt = 0
		for group in kentry.groups:
			glosses = group.glosses
			# Dump all meanings
			msgctxt = '%s %d' % (kentry.literal, cpt)
			if 'en' in glosses: enGlosses = glosses['en']
			else: return False
			if len(group.readings) > 0: msgid = '%s\t%s\n' % (kentry.literal, str(group.readings)) + enGlosses
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

class JouyouFilter:
	def __init__(self, langs):
		Filter.__init__(self, "kanjidic2-jouyou", langs)

	def processEntry(self, kentry):
		if kentry.grade > 0 and kentry.grade <= 8: return Filter.processEntry(self, kentry)
		else: return False

class RMGroup:
	def __init__(self):
		self.readings = []
		self.glosses = {}

if __name__ == "__main__":
	kdic = open('kanjidic2.xml', 'r', encoding='utf-8')

	filt = JouyouFilter([ 'en', 'fr', 'es', 'pt' ])
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
		match = literalRe.match(l)
		if match:
			kentry = KEntry(match.group(1))
			rmgroup = RMGroup()
			glosses = {}
			continue
		match = entryEndRe.match(l)
		if match:
			filt.processEntry(kentry)
		if len(l) == 0: break
