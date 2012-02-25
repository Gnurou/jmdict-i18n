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
#
# This script generates, from a JMdict file and an optional set of .po files:
# * A set of .pot files (one per filter) containing the source strings of the JMdict file
# * A set of .po files (one per filter and language) with the translation strings of the JMdict and regressions
# * A set of regression files (one per language) with the previously translated strings for which source string
#   has changed in the new JMdict file

import sys, datetime, argparse, xml.sax, os.path
from gettextformat import *
from jmdict import *
from langs import *
import efilter

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

class JLPTFilter(efilter.Filter):
	def __init__(self, level):
		self.name = "jlpt%d" % (level,)
		efilter.Filter.__init__(self, self.name, 'JMdict i18n', 'Alexandre Courbot <gnurou@gmail.com>')
		self.elist = [ int(x) for x in open("jlpt-level%d.txt" % (level,)).read().split('\n')[:-1] ]

	def isfiltered(self, entry):
		return entry.eid in self.elist

class PriFilter(efilter.Filter):
	def __init__(self, level):
		self.name = "pri"
		efilter.Filter.__init__(self, self.name, 'JMdict i18n', 'Alexandre Courbot <gnurou@gmail.com>')

	def isfiltered(self, entry):
		return self.ke_pri > 0

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

	# Parse JMdict
	jmdictfile = cmdargs.JMdict[0]
	print('Loading %s...\t' % (jmdictfile,), end='')
	parser = xml.sax.make_parser()
	handler = JMdictParser()
	parser.setContentHandler(handler)
	parser.setFeature(xml.sax.handler.feature_external_ges, False)
	parser.setFeature(xml.sax.handler.feature_external_pes, False)
	parser.parse(cmdargs.JMdict[0])
	print('\t%d senses loaded' % (len(handler.entries)))

	# Parse .po files
	print('Loading .po files...\t', end='')
	poEntries = {}
	for lang in cmdargs.l: poEntries[lang] = {}
	for pof in cmdargs.t:
		ne = readPo(open(pof, 'r', encoding='utf-8'))
		if len(ne) > 0:
			lang = ne[0].lang
			if not lang in poEntries: continue
			lEntries = poEntries[lang]
			for entry in ne: lEntries[entry.contextString()] = entry
			poEntries[lang] = lEntries
	for lang in poEntries:
		print('\t%s: %d' % (lang, len(poEntries[lang])), end='')
	print('')

	# Parse regressions
	print('Loading regressions...\t', end='')
	regressions = {}
	for lang in cmdargs.l:
		regressions[lang] = {}
		regfile = jmdictfile + '_%s.reg' % (lang,)
		if os.path.exists(regfile):
			ne = readPo(open(regfile, 'r', encoding='utf-8'))
			if len(ne) > 0:
				lEntries = regressions[lang]
				for entry in ne: lEntries[entry.contextString()] = entry
				regressions[lang] = lEntries
		print('\t%s: %d' % (lang, len(regressions[lang])), end='')
	print('')

	# Check for fixed regressions
	# A regression is fixed if:
	# - the entry has been deleted
	# - a translation (not "fuzzy") is provided by its .po file
	print('Checking fixed regressions...', end='')
	fixedRegsCpt = { lang : 0 for lang in cmdargs.l }
	for lang in regressions.keys():
		cpt = 0
		fixed = []
		for ctxstr in regressions[lang]:
			poEntry = poEntries[lang][ctxstr]
			if not ctxstr in poEntries[lang] or poEntry.trString(lang) != "" and not poEntry.fuzzy:
				#print('Regression %s fixed' % (ctxstr,))
				fixedRegsCpt[lang] += 1
				fixed.append(ctxstr)
		for ctxstr in fixed:
			del regressions[lang][ctxstr]
		print('\t%s: %d' % (lang, fixedRegsCpt[lang]), end='')
	print('')

	# Check for new regressions
	# We have a new regression for a given language if:
	# - an entry exists in the .po file and has a translation
	# - the source string from the JMdict is different from the one
	#   in the .po
	print('Checking new regressions...', end='')
	newRegsCpt = { lang : 0 for lang in cmdargs.l }
	for entry in handler.entries.values():
		ctx = entry.contextString()
		for lang in poEntries:
			lEntries = poEntries[lang]
			if ctx in lEntries:
				poEntry = lEntries[ctx]
				if poEntry.trString(lang) != '' and poEntry.sourceString() != entry.sourceString():
					#print('Found regression for %s' % (ctx,))
					newRegsCpt[lang] += 1
					reg = GetTextEntry(lang)
					reg.msgctxt = ctx
					reg.msgid = entry.sourceString()
					reg.msgstr = poEntry.trString(lang)
					regressions[lang][ctx] = reg
	for lang in cmdargs.l:
		print('\t%s: %d' % (lang, newRegsCpt[lang],), end='')
	print('')

	# Merge the new .po translations into the JMdict entries
	print('Merging new .po data...\t', end='')
	mergedPoCpt = { lang : 0 for lang in cmdargs.l }
	for lang in poEntries:
		for key in poEntries[lang]:
			if key in handler.entries:
				poEntry = poEntries[lang][key]
				jmEntry = handler.entries[key]
				if poEntry.trString(lang) == jmEntry.trString(lang): continue
				jmEntry.translations[lang] = poEntry.trString(lang)
				mergedPoCpt[lang] += 1
		print('\t%s: %d' % (lang, mergedPoCpt[lang]), end='')
	print('')


	# Merge regressions into the parsed JMdict and add fuzzy tags
	print('Merging regressions...\t', end='')
	mergedRegsCpt = { lang : 0 for lang in cmdargs.l }
	for lang in regressions:
		for key in regressions[lang]:
			if key in handler.entries:
				poEntry = regressions[lang][key]
				jmEntry = handler.entries[key]
				jmEntry.translations[lang] = poEntry.trString(lang)
				jmEntry.fuzzies.append(lang)
				mergedRegsCpt[lang] += 1
		print('\t%s: %d' % (lang, mergedRegsCpt[lang]), end='')
	print('')

	# Report number of translations per language
	print('Total translations:\t', end='')
	for lang in cmdargs.l:
		print('\t%s: %d' % (lang, len(poEntries[lang])))

	# Write new regressions list
	print('Writing regressions...\t', end='')
	for lang in cmdargs.l:
		regfile = jmdictfile + '_%s.reg' % (lang,)
		outf = open(regfile, 'w', encoding='utf-8')
		header = GetTextEntry()
		header.msgstr = headerStr % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S%z"), lang)
		outf.write(str(header))
		for entry in regressions[lang]:
			outf.write(str(regressions[lang][entry]))
		print('\t%s: %d' % (lang, len(regressions[lang])), end='')
	print('')

	# Filter entries
	print('Filtering entries...')
	filters = []
	filters.append(JLPTFilter(4))
	filters.append(JLPTFilter(3))
	filters.append(JLPTFilter(2))
	filters.append(JLPTFilter(1))
	for entry in handler.entries.values():
		filtered = False
		for filt in filters:
			if filt.consider(entry):
				filtered = True
				break
		if not filtered:
			pass
			#print('Warning: unfiltered entry %s!' % (entry.contextString()))
		
	# Output .pot file
	print('Outputting new .pot files...')
	for filt in filters:
		filt.output('en')

	# Output .po files
	print('Outputting new .po files...')
	for l in cmdargs.l:
		for filt in filters:
			filt.output(lang)
