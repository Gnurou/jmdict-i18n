# Configuration
projectShort = 'kanjidic2'
projectDesc = 'Kanjidic2 i18n'
projectLangs = ('fr', 'it', 'th', 'tr')
ownerInfo = 'Alexandre Courbot <gnurou@gmail.com>'
txProject = 'kanjidic2-i18n'
srcFile = 'kanjidic2.xml'

import re, xmlhandler, xml.sax, efilter
from gettextformat import *

# One entry per RMgroup of a kanjidic2 entry
class Kanjidic2Entry:
	def __init__(self, kanji, rmgroup):
		self.kanji = kanji
		self.rmgroup = rmgroup
		# One string per language
		self.translations = {}
		# Languages that should be outputed as 'fuzzy'
		self.fuzzies = []
		self.readings = []
		self.grade = 0
		self.freq = 0

	def contextString(self):
		return '%s %d' % (self.kanji, self.rmgroup)

	def sourceString(self):
		ret = self.kanji + '\n'
		if len(self.readings) != 0:
			ret += ', '.join(self.readings) + '\n'
		ret += self.trString('en')
		return ret

	def trString(self, lang):
		if not lang in self.translations: return ''
		else: return self.translations[lang]

	def asGettext(self, lang):
		entry = GetTextEntry()
		entry.msgctxt = self.contextString()
		entry.msgid = self.sourceString()
		entry.lang = lang
		if lang in self.fuzzies: entry.fuzzy = True
		if lang != 'en':
			entry.msgstr = self.trString(lang)
		return entry

	def toJMF(self, lang):
		ret = ""
		ts = self.trString(lang).split('\n')
		for s in ts:
			ret += "%s %s\n" % (self.kanji, s)
		return ret

class Kanjidic2Parser(xmlhandler.BasicHandler):
	def __init__(self):
		xmlhandler.BasicHandler.__init__(self)
		self.entries = {}
		self.lang = None
		self.takeReading = False
		self.readings = []

	def handle_start_character(self, attrs):
		self.currentEntry = None
		self.currentEid = None
		self.currentRM = 0
		self.currentGrade = 0
		self.currentFreq = 0

	def handle_data_literal(self, data):
		self.currentEid = data

	def handle_data_grade(self, data):
		self.currentGrade = int(data)

	def handle_data_freq(self, data):
		self.currentFreq = int(data)

	def handle_start_reading(self, attrs):
		if not 'r_type' in attrs: return
		if attrs['r_type'] in ('ja_on', 'ja_kun'):
			self.takeReading = True

	def handle_data_reading(self, data):
		if self.takeReading:
			self.readings.append(data)
		self.takeReading = False

	def handle_start_rmgroup(self, attrs):
		self.currentEntry = Kanjidic2Entry(self.currentEid, self.currentRM)
		self.currentEntry.grade = self.currentGrade
		self.currentEntry.freq = self.currentFreq

	def handle_end_rmgroup(self):
		self.currentEntry.readings = self.readings
		self.readings = []
		self.entries[self.currentEntry.contextString()] = self.currentEntry
		self.currentRM += 1
		self.currentEntry = None

	def handle_start_meaning(self, attrs):
		if 'm_lang' in attrs: self.lang = attrs['m_lang']
		else: self.lang = 'en'

	def handle_data_meaning(self, data):
		try:
			trans = self.currentEntry.translations[self.lang]
			trans += "\n" + data
		except KeyError:
			trans = data
		self.currentEntry.translations[self.lang] = trans
		self.lang = None

def parseSrcEntries(src):
	parser = xml.sax.make_parser()
	handler = Kanjidic2Parser()
	parser.setContentHandler(handler)
	parser.setFeature(xml.sax.handler.feature_external_ges, False)
	parser.setFeature(xml.sax.handler.feature_external_pes, False)
	parser.parse(src)
	return handler.entries

class GradeFilter(efilter.Filter):
	def __init__(self, grade):
		efilter.Filter.__init__(self, "grade%02d" % (grade,), projectShort, projectDesc, ownerInfo)
		self.grade = grade

	def isfiltered(self, entry):
		return entry.grade > 0 and entry.grade == self.grade

class FreqFilter(efilter.Filter):
	def __init__(self, freq):
		efilter.Filter.__init__(self, "freq%04d" % (freq,), projectShort, projectDesc, ownerInfo)
		self.freq = freq

	def isfiltered(self, entry):
		return entry.freq > 0 and entry.freq <= self.freq

class AllFilter(efilter.Filter):
	def __init__(self):
		efilter.Filter.__init__(self, "others", projectShort, projectDesc, ownerInfo)

	def isfiltered(self, entry):
		return True

def filtersList():
	filters = []
	filters.append(GradeFilter(1))
	filters.append(GradeFilter(2))
	filters.append(GradeFilter(3))
	filters.append(GradeFilter(4))
	filters.append(GradeFilter(5))
	filters.append(GradeFilter(6))
	filters.append(GradeFilter(8))
	filters.append(FreqFilter(3000))
	filters.append(GradeFilter(9))
	filters.append(GradeFilter(10))
	filters.append(AllFilter())
	return filters

literalRe = re.compile('<literal>(.*)</literal>')
rmgroupEndRe = re.compile('</rmgroup>')
entryEndRe = re.compile('</character>')
gradeRe = re.compile('<grade>(.*)</grade>')
freqRe = re.compile('<freq>(.*)</freq>')
readingRe = re.compile('<reading r_type="(.*)">(.*)</reading>')
enMeaningRe = re.compile('<meaning>(.*)</meaning>')
otherMeaningRe = re.compile('<meaning m_lang="(.*)">(.*)</meaning>')
