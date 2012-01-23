#!/usr/bin/python3

# Handling regressions:
# We want regressions to be preserved as "fuzzy" in the .po files, but we also want them
# to stay in the JMdict file until they are updated. To allow this, when updating the source strings
# a file containing a list of regressed senses is created/updated, by appending references to those
# senses which source string has changed since the last update (we can compare the source strings
# from the JMdict file with those from the latest .pot file). Senses referenced in that file are
# exported as "fuzzy" by this script, and by doing this regressions are preserved across updates
# even though Transifex does not give us a way to fetch suggested entries from .po files.
#
# Regressions are removed from the file when a new translation for a regressed sense is provided. This
# is done by checking if the translation string has changed from what it was in the original JMdict file.
# The export script also *must* include the fuzzy translations that have not been updated on Transifex.
#
# Regressions should be re-uploaded as a file containing only fuzzy entries to ensure the "suggestion"
# field on Transifex is valid.
#
# Regressions can be stored in JMF format. Thus:
# * .po + regs = .jmf
# * regs += source strings from JMdict that changed (against previous JMdict or .pot)
# * regs -= destination strings that have been updated (since previous .po)

import sys, datetime, argparse, xmlhandler, xml.sax
from gettextformat import *
from jmdict import *
from langs import *

# PO header
headerStr = """Project-Id-Version: JMdict i18n
Report-Msgid-Bugs-To: Alexandre Courbot <gnurou@gmail.com>
POT-Creation-Date: %s
PO-Revision-Date: 
Last-Translator: 
Language-Team: 
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Language: %s"""

class JMdictParser(xmlhandler.BasicHandler):
	def __init__(self):
		xmlhandler.BasicHandler.__init__(self)
		self.entries = []
		self.currentEntry = None
		self.currentSense = None
		self.lang = None

	def handle_start_entry(self, attrs):
		self.currentEntry = Entry()

	def handle_end_entry(self):
		self.entries.append(self.currentEntry)
		self.currentEntry = None

	def handle_data_ent_seq(self, data):
		self.currentEntry.eid = int(data)

	def handle_data_keb(self, data):
		if not self.currentEntry.keb:
			self.currentEntry.keb = data

	def handle_data_reb(self, data):
		if not self.currentEntry.reb:
			self.currentEntry.reb = data

	def handle_start_sense(self, attrs):
		self.currentSense = Sense()

	def handle_end_sense(self):
		self.currentEntry.senses[len(self.currentEntry.senses)] = self.currentSense
		self.currentSense = None

	def handle_start_gloss(self, attrs):
		self.lang = langMatch[attrs["xml:lang"]]

	def handle_data_gloss(self, data):
		try:
			glosses = self.currentSense.glosses[self.lang]
		except KeyError:
			glosses = ""
		glosses += data + "\n"
		self.currentSense.glosses[self.lang] = glosses
		self.lang = None

class JLPTFilter:
	def __init__(self, level):
		self.elist = [ int(x) for x in open("jlpt-level%d.txt" % (level,)).read().split('\n')[:-1] ]
		self.name = "jlpt%d" % (level,)

	def isfiltered(self, entry):
		return entry.eid in self.elist

def writeSense(f, currentEntry, senseNbr, lang):
	entry = GetTextEntry()
	entry.msgctxt = '%d %d' % (currentEntry.eid, senseNbr)
	# Japanese keb and reb
	if not currentEntry.keb: ids = '%s' % (currentEntry.reb,)
	else: ids = '%s\t%s' % (currentEntry.keb, currentEntry.reb)

	# English glosses
	currentSense = currentEntry.senses[senseNbr]
	entry.msgid = ids + '\n' + currentSense.glosses['en'].rstrip('\n')
	if lang != "en" and lang in currentSense.glosses:
		entry.msgstr = currentSense.glosses[lang].rstrip('\n')
	f.write(str(entry))

def writeEntry(f, currentEntry, lang):
	for i in range(len(currentEntry.senses)):
		writeSense(f, currentEntry, i, lang)

def outputPo(entries, filters, lang):
	# Create files
	header = GetTextEntry()
	header.msgstr = headerStr % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S%z"), lang)
	if lang == "en": basename = "jmdict-%s.pot"
	else: basename = "jmdict-%s_" + lang + ".po"
	for filt in filters:
		filt.outf = open(basename % (filt.name,), 'w', encoding='utf-8')
		filt.outf.write(str(header))
	# Write entries
	for entry in entries:
		for filt in filters:
			if filt.isfiltered(entry):
				writeEntry(filt.outf, entry, lang)
				break
	for filt in filters:
		del filt.outf

if __name__ == "__main__":
	aparser = argparse.ArgumentParser(description = "Build a .pot file (and optionally .po files) from the JMdict.")
	aparser.add_argument('JMdict',
		nargs = 1,
		help = 'JMdict file from which to extract')
	aparser.add_argument('-l',
		action = "store",
		nargs = "*",
		default = [],
		help = '2 letters codes of languages for which a .po file will be created',
		choices = list(langMatch.values()))
	cmdargs = aparser.parse_args()
	
	# Parse whole JMdict
	parser = xml.sax.make_parser()
	handler = JMdictParser()
	parser.setContentHandler(handler)
	parser.setFeature(xml.sax.handler.feature_external_ges, False)
	parser.setFeature(xml.sax.handler.feature_external_pes, False)
	parser.parse(cmdargs.JMdict[0])

	# Filter entries
	filters = []
	filters.append(JLPTFilter(4))
	filters.append(JLPTFilter(3))
	filters.append(JLPTFilter(2))
	filters.append(JLPTFilter(1))

	# Output .pot files
	outputPo(handler.entries, filters, "en")

	# Output .po files
	for l in cmdargs.l:
		outputPo(handler.entries, filters, l)
