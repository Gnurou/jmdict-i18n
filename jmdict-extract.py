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
# * regs -= destination strings that have been updated (since previous .po) - i.e. that have a translation,
#   since the previous translations was sent as a suggestion and thus is not supposed to be fetched back.

import sys, datetime, argparse, xml.sax, os.path
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

class JLPTFilter:
	def __init__(self, level):
		self.elist = [ int(x) for x in open("jlpt-level%d.txt" % (level,)).read().split('\n')[:-1] ]
		self.name = "jlpt%d" % (level,)

	def isfiltered(self, entry):
		return entry.eid in self.elist

def writeEntry(f, currentEntry, lang):
	poEntry = currentEntry.asGettext(lang)
	f.write(str(poEntry))

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
	for entry in entries.values():
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
	aparser.add_argument('-t',
		action = "store",
		nargs = "*",
		default = [],
		help = '.po files to load for regression matching')
	cmdargs = aparser.parse_args()

	# Parse .po files
	poEntries = {}
	for lang in cmdargs.l: poEntries[lang] = {}
	for pof in cmdargs.t:
		print('Loading %s...' % (pof,))
		ne = readPo(open(pof, 'r', encoding='utf-8'))
		if len(ne) > 0:
			lang = ne[0].lang
			if not lang in poEntries: continue
			lEntries = poEntries[lang]
			for entry in ne: lEntries[entry.contextString()] = entry
			poEntries[lang] = lEntries

	jmdictfile = cmdargs.JMdict[0]
	# Parse regressions
	regressions = {}
	for lang in cmdargs.l:
		regressions[lang] = {}
		regfile = jmdictfile + '_%s.reg' % (lang,)
		if os.path.exists(regfile):
			print('Loading %s...' % (regfile,))
			ne = readPo(open(regfile, 'r', encoding='utf-8'))
			if len(ne) > 0:
				lEntries = regressions[lang]
				for entry in ne: lEntries[entry.contextString()] = entry
				regressions[lang] = lEntries

	# Parse new JMdict
	print('Loading %s...' % (jmdictfile,))
	parser = xml.sax.make_parser()
	handler = JMdictParser()
	parser.setContentHandler(handler)
	parser.setFeature(xml.sax.handler.feature_external_ges, False)
	parser.setFeature(xml.sax.handler.feature_external_pes, False)
	parser.parse(cmdargs.JMdict[0])

	# Check for new regressions
	# We have a new regression for a given language if:
	# - the entry is not in the regressions lists
	# - the source string from the JMdict is different that the one
	#   from the .po
	newregs = {}
	for lang in cmdargs.l: newregs[lang] = {}
	for entry in handler.entries.values():
		ctx = entry.contextString()
		for lang in poEntries.keys():
			lEntries = poEntries[lang]
			if ctx in lEntries:
				poEntry = lEntries[ctx]
				if poEntry.sourceString() != entry.sourceString():
					print('Found regression for %s' % (ctx,))
					reg = GetTextEntry(lang)
					reg.msgctxt = ctx
					reg.msgid = entry.sourceString()
					reg.msgstr = poEntry.trString(lang)
					newregs[lang][ctx] = reg

	# Check for fixed regressions
	# A regression is fixed if:
	# - the entry has been deleted
	# - a translation (i.e. not "fuzzy") is provided by its .po file
	for lang in regressions.keys:
		for ctxstr in regressions[lang].keys():
			if not ctxstr in poEntries[lang] or poEntries[lang][ctxstr].trString(lang) != "":
				del regressions[lang][ctxstr]

	# Add new regressions to regressions lists
	for lang in regressions.keys():
		for entkey in newregs[lang].keys():
			regressions[lang][entkey] = newregs[lang][entkey]

	# Merge the .po translations to the JMdict entries

	sys.exit(1)

	print('Filtering entries...')
	# Filter entries
	filters = []
	filters.append(JLPTFilter(4))
	filters.append(JLPTFilter(3))
	filters.append(JLPTFilter(2))
	filters.append(JLPTFilter(1))
	# Entries should be filtered first in groups, groups sorted by id & sense nbr,
	# then written to their respective files

	# Output .pot file
	outputPo(handler.entries, filters, "en")

	# Output .po files
	for l in cmdargs.l:
		outputPo(handler.entries, filters, l)

	# Output regressions
