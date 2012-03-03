# Configuration
projectShort = 'kanjidic2'
projectDesc = 'Kanjidic2 i18n'
projectLangs = ('fr', 'it')
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

	def contextString(self):
		return '%s %d' % (self.kanji, self.rmgroup)

	def sourceString(self):
		return self.kanji + '\n' + self.trString('en')

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

class Kanjidic2Parser(xmlhandler.BasicHandler):
	def __init__(self):
		xmlhandler.BasicHandler.__init__(self)
		self.entries = {}
		self.currentEntry = None
		self.currentRM = 0
		self.currentEid = None
		self.lang = None

	def handle_end_character(self):
		self.currentEntry = None
		self.currentEid = None
		self.currentRM = 0

	def handle_data_literal(self, data):
		self.currentEid = data

	def handle_start_rmgroup(self, attrs):
		self.currentEntry = Kanjidic2Entry(self.currentEid, self.currentRM)

	def handle_end_rmgroup(self):
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

class AllFilter(efilter.Filter):
	def __init__(self):
		efilter.Filter.__init__(self, "others", projectShort, projectDesc, ownerInfo)

	def isfiltered(self, entry):
		return True

def filtersList():
	filters = []
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
