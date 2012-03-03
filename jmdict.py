# Configuration
projectShort = 'jmdict'
projectDesc = 'JMdict i18n'
projectLangs = ('fr',)
ownerInfo = 'Alexandre Courbot <gnurou@gmail.com>'
txProject = 'jmdict-i18n-dummy'


import re, xmlhandler, xml.sax
from gettextformat import *
from langs import *

entryStartRe = re.compile('<ent_seq>(.*)</ent_seq>')
kebRe = re.compile('<keb>(.*)</keb>')
rebRe = re.compile('<reb>(.*)</reb>')
senseStartRe = re.compile('<sense>')
senseEndRe = re.compile('</sense>')
enGlossRe = re.compile('<gloss>(.*)</gloss>')
otherGlossRe = re.compile('<gloss xml:lang="(.*)">(.*)</gloss>')

# We use one entry per sense
class JMdictEntry:
	def __init__(self, eid, senseNbr):
		self.eid = eid
		self.senseNbr = senseNbr
		self.keb = None
		self.reb = None
		self.pri = 0
		# Group glosses per language, one per line
		self.translations = {}
		# Languages that should be outputed as 'fuzzy'
		self.fuzzies = []

	def contextString(self):
		return '%d %d' % (self.eid, self.senseNbr)

	def sourceString(self):
		if not self.keb: jp = '%s' % (self.reb,)
		else: jp = '%s\t%s' % (self.keb, self.reb)
		return jp + '\n' + self.trString('en')

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

class JMdictParser(xmlhandler.BasicHandler):
	def __init__(self):
		xmlhandler.BasicHandler.__init__(self)
		self.entries = {}
		self.currentEntry = None
		self.currentSense = 0
		self.currentEid = None
		self.currentKeb = None
		self.currentReb = None
		self.currentPri = 0
		self.lang = None

	def handle_end_entry(self):
		self.currentEid = None
		self.currentKeb = None
		self.currentReb = None
		self.currentSense = 0
		self.currentPri = 0

	def handle_data_ent_seq(self, data):
		self.currentEid = int(data)

	def handle_data_keb(self, data):
		if not self.currentKeb:
			self.currentKeb = data

	def handle_data_reb(self, data):
		if not self.currentReb:
			self.currentReb = data

	def handle_data_ke_pri(self, data):
		if data in ("news1", "ichi1", "spec1", "gail1"): self.currentPri += 100
		elif data in ("news2", "ichi2", "spec2", "gail2"): self.currentPri += 50
		elif data.startswith("nf"): self.currentPri += 100 - int(data[2:])

	def handle_data_re_pri(self, data):
		self.handle_data_ke_pri(data)

	def handle_start_sense(self, attrs):
		self.currentEntry = JMdictEntry(self.currentEid, self.currentSense)
		self.currentEntry.keb = self.currentKeb
		self.currentEntry.reb = self.currentReb
		self.currentEntry.pri = self.currentPri

	def handle_end_sense(self):
		self.entries['%d %d' % (self.currentEid, self.currentSense)] = self.currentEntry
		self.currentSense += 1
		self.currentEntry = None

	def handle_start_gloss(self, attrs):
		self.lang = langMatch[attrs["xml:lang"]]

	def handle_data_gloss(self, data):
		try:
			glosses = self.currentEntry.translations[self.lang]
			glosses += "\n" + data
		except KeyError:
			glosses = data
		self.currentEntry.translations[self.lang] = glosses
		self.lang = None

def parseSrcEntries(src):
	parser = xml.sax.make_parser()
	handler = JMdictParser()
	parser.setContentHandler(handler)
	parser.setFeature(xml.sax.handler.feature_external_ges, False)
	parser.setFeature(xml.sax.handler.feature_external_pes, False)
	parser.parse(src)
	return handler.entries