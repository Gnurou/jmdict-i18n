import re, xmlhandler
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
		# Group glosses per language, one per line
		self.translations = {}

	def contextString(self):
		return '%d %d' % (self.eid, self.senseNbr)

	def sourceString(self):
		if not self.keb: jp = '%s' % (self.reb,)
		else: jp = '%s\t%s' % (self.keb, self.reb)
		return jp + '\n' + self.trString('en')

	def trString(self, lang):
		if not lang in self.translations: return ''
		else: return self.translations[lang].rstrip('\n')

	def asGettext(self, lang):
		entry = GetTextEntry()
		entry.msgctxt = self.contextString()
		entry.msgid = self.sourceString()
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
		self.lang = None

	def handle_end_entry(self):
		self.currentEid = None
		self.currentKeb = None
		self.currentReb = None
		self.currentSense = 0

	def handle_data_ent_seq(self, data):
		self.currentEid = int(data)

	def handle_data_keb(self, data):
		if not self.currentKeb:
			self.currentKeb = data

	def handle_data_reb(self, data):
		if not self.currentReb:
			self.currentReb = data

	def handle_start_sense(self, attrs):
		self.currentEntry = JMdictEntry(self.currentEid, self.currentSense)
		self.currentEntry.keb = self.currentKeb
		self.currentEntry.reb = self.currentReb

	def handle_end_sense(self):
		self.entries[(self.currentEid, self.currentSense)] = self.currentEntry
		self.currentSense += 1
		self.currentEntry = None

	def handle_start_gloss(self, attrs):
		self.lang = langMatch[attrs["xml:lang"]]

	def handle_data_gloss(self, data):
		try:
			glosses = self.currentEntry.translations[self.lang]
		except KeyError:
			glosses = ""
		glosses += data + "\n"
		self.currentEntry.translations[self.lang] = glosses
		self.lang = None
