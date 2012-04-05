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

import sys, datetime, argparse, os.path
from gettextformat import *
import efilter
import subprocess

if __name__ == "__main__":
	aparser = argparse.ArgumentParser(description = "Build a .pot file and merge .po files from a source.")
	aparser.add_argument('module',
		nargs = 1,
		help = 'Module to use for extraction/merging')
	aparser.add_argument('-t',
		action = 'store',
		nargs = '*',
		default = [],
		help = 'Additional .po files to load')
	cmdargs = aparser.parse_args()

	client = __import__(cmdargs.module[0])

	# Parse source file
	print('%-30s' % ('Loading %s...' % (client.srcFile,)), end='')
	sys.stdout.flush()
	srcEntries = client.parseSrcEntries(os.path.join(client.projectShort, client.srcFile))
	srcCpt = { lang : 0 for lang in client.projectLangs }
	for entry in srcEntries.values():
		for lang in client.projectLangs:
			if lang in entry.translations: srcCpt[lang] += 1
	for lang in client.projectLangs:
		print('%-10s' % ('%s: %d' % (lang, srcCpt[lang])), end='')
	print('')

	# Parse .po files
	print('%-30s' % ('Loading .po files...'), end='')
	sys.stdout.flush()
	if os.path.exists(client.projectShort): poSources = [ os.path.join(client.projectShort, p) for p in filter(lambda f: f.endswith(".po"), os.listdir(client.projectShort)) ]
	else: poSources = []
	poSources += cmdargs.t
	poEntries = {}
	poCpt = {}
	for lang in client.projectLangs:
		poEntries[lang] = {}
		poCpt[lang] = 0
	for pof in poSources:
		ne = readPo(open(pof, 'r', encoding='utf-8'))
		if len(ne) > 0:
			lang = ne[0].lang
			if not lang in poEntries: continue
			lEntries = poEntries[lang]
			for entry in ne:
				ctx = entry.contextString()
				if ctx in lEntries:
					print('\nError: two different .po sources for "%s", aborting...' % (ctx))
					sys.exit(1)
				lEntries[ctx] = entry
				if entry.trString(lang) != '': poCpt[lang] += 1
			poEntries[lang] = lEntries
	for lang in client.projectLangs:
		print('%-10s' % ('%s: %d' % (lang, poCpt[lang])), end='')
	print('')

	# Parse regressions
	print('%-30s' % ('Loading regressions...'), end='')
	sys.stdout.flush()
	regressions = {}
	for lang in client.projectLangs:
		regressions[lang] = {}
		regfile = os.path.join(client.projectShort, client.srcFile) + '_%s.reg' % (lang,)
		if os.path.exists(regfile):
			ne = readPo(open(regfile, 'r', encoding='utf-8'))
			if len(ne) > 0:
				lEntries = regressions[lang]
				for entry in ne: lEntries[entry.contextString()] = entry
				regressions[lang] = lEntries
		print('%-10s' % ('%s: %d' % (lang, len(regressions[lang]))), end='')
		sys.stdout.flush()
	print('')

	# Check for fixed regressions
	# A regression is fixed if:
	# - the entry has been deleted
	# - a translation (not "fuzzy") is provided by its .po file
	print('%-30s' % ('Checking fixed regressions...'), end='')
	sys.stdout.flush()
	fixedRegsCpt = { lang : 0 for lang in client.projectLangs }
	for lang in client.projectLangs:
		cpt = 0
		fixed = []
		for ctxstr in regressions[lang]:
			if ctxstr not in poEntries[lang]: continue
			poEntry = poEntries[lang][ctxstr]
			if not ctxstr in poEntries[lang] or poEntry.trString(lang) != "" and not poEntry.fuzzy:
				#print('Regression %s fixed' % (ctxstr,))
				fixedRegsCpt[lang] += 1
				fixed.append(ctxstr)
		for ctxstr in fixed:
			del regressions[lang][ctxstr]
		print('%-10s' % ('%s: %d' % (lang, fixedRegsCpt[lang])), end='')
		sys.stdout.flush()
	print('')

	# Check for new regressions
	# We have a new regression for a given language if:
	# - an entry exists in the .po file and has a translation
	# - the source string from the source file is different from the one
	#   in the .po
	print('%-30s' % ('Checking new regressions...'), end='')
	sys.stdout.flush()
	newRegsCpt = { lang : 0 for lang in client.projectLangs }
	for entry in srcEntries.values():
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
	for lang in client.projectLangs:
		print('%-10s' % ('%s: %d' % (lang, newRegsCpt[lang],)), end='')
	print('')

	# Merge the new .po translations into the source file entries
	print('%-30s' % 'Merging new .po data...', end='')
	sys.stdout.flush()
	updatedPoCpt = { lang : 0 for lang in client.projectLangs }
	newPoCpt = { lang : 0 for lang in client.projectLangs }
	newSourceCpt = { lang : 0 for lang in client.projectLangs }
	for key in srcEntries:
		srcEntry = srcEntries[key]
		for lang in client.projectLangs:
			sString = srcEntry.trString(lang)
			if key in poEntries[lang]:
				poEntry = poEntries[lang][key]
				tString = poEntry.trString(lang)
				# Identical? (maybe both null?) Skip
				if tString == sString:
					continue
				# No translation? New source string, skip
				if not tString:
					newSourceCpt[lang] += 1
					continue
				if not sString: newPoCpt[lang] += 1
				else: updatedPoCpt[lang] += 1
				srcEntry.translations[lang] = tString
			else:
				if sString: newSourceCpt[lang] += 1
	for lang in client.projectLangs:
		print('%-10s' % ('%s: %d' % (lang, newPoCpt[lang] + updatedPoCpt[lang])), end='')
		sys.stdout.flush()
	print('')
	print('%-30s' % '  New translations:', end='')
	for lang in client.projectLangs:
		print('%-10s' % ('%s: %d' % (lang, newPoCpt[lang])), end='')
	print('')
	print('%-30s' % '  Updated translations:', end='')
	for lang in client.projectLangs:
		print('%-10s' % ('%s: %d' % (lang, updatedPoCpt[lang])), end='')
	print('')
	print('%-30s' % '  New source strings:', end='')
	for lang in client.projectLangs:
		print('%-10s' % ('%s: %d' % (lang, newSourceCpt[lang])), end='')
	print('')

	# Merge regressions into the parsed source entries and add fuzzy tags
	print('%-30s' % ('Merging regressions...'), end='')
	sys.stdout.flush()
	mergedRegsCpt = { lang : 0 for lang in client.projectLangs }
	for lang in client.projectLangs:
		for key in regressions[lang]:
			if key in srcEntries:
				poEntry = regressions[lang][key]
				srcEntry = srcEntries[key]
				srcEntry.translations[lang] = poEntry.trString(lang)
				srcEntry.fuzzies.append(lang)
				mergedRegsCpt[lang] += 1
		print('%-10s' % ('%s: %d' % (lang, mergedRegsCpt[lang])), end='')
		sys.stdout.flush()
	print('')

	# Report number of translations per language
	print('%-30s' % ('Total translations:'), end='')
	sys.stdout.flush()
	for lang in client.projectLangs:
		cpt = 0
		for entry in srcEntries.values():
			if entry.trString(lang) != '': cpt += 1
		print('%-10s' % ('%s: %d' % (lang, cpt)), end='')
		sys.stdout.flush()
	print('')

	# Filter entries
	print('Filtering entries...')
	filters = client.filtersList()
	for entry in srcEntries.values():
		filtered = False
		for filt in filters:
			if filt.consider(entry):
				filtered = True
				break
		if not filtered:
			pass
		
	# Output .pot files
	print('%-30s' % ('Writing new .pot files...'), end='')
	sys.stdout.flush()
	cpt = 0
	for filt in filters:
		cpt += filt.output('en')
	print("%d entries written" % (cpt,))

	# Output .po files
	if not len(client.projectLangs) == 0:
		print('%-30s' % ('Writing new .po files...'), end='')
		sys.stdout.flush()
		for lang in client.projectLangs:
			cpt = 0
			for filt in filters:
				cpt += filt.output(lang)
			print('%-10s' % ('%s: %d' % (lang, cpt)), end='')
			sys.stdout.flush()
		print('')

	# Output .jmf files
	print('%-30s' % ('Writing new .jmf files...'), end='')
	sys.stdout.flush()
	for lang in client.projectLangs:
		outf = open(os.path.join(client.projectShort, "jmf", "%s.jmf" % (lang)), 'w', encoding='utf-8')
		tEntries = {}
		for filt in filters:
			for key in filt.entries:
				entry = filt.entries[key]
				if lang in entry.translations: tEntries[key] = entry
		skeys = sorted(tEntries)
		for key in skeys:
			outf.write(tEntries[key].toJMF(lang))
		outf.close()
		print('%-10s' % ('%s: %d' % (lang, len(tEntries))), end='')
		sys.stdout.flush()
	print('')

	# Write new regressions list
	print('%-30s' % ('Writing regressions...'), end='')
	sys.stdout.flush()
	for lang in client.projectLangs:
		regfile = os.path.join(client.projectShort, client.srcFile) + '_%s.reg' % (lang,)
		outf = open(regfile, 'w', encoding='utf-8')
		header = GetTextEntry()
		header.msgstr = efilter.headerStr % (client.projectDesc, client.ownerInfo, datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000"), lang)
		outf.write(str(header))
		for entry in sorted(regressions[lang].keys()):
			outf.write(str(regressions[lang][entry]))
		print('%-10s' % ('%s: %d' % (lang, len(regressions[lang]))), end='')
		sys.stdout.flush()
	print('')

	# Update transifex resources
	print('Updating Transifex resources...')
	curDir = os.getcwd()
	os.chdir(os.path.join(curDir, client.projectShort))
	if not os.path.exists('.tx'): os.mkdir('.tx')
	open('.tx/config', 'w').write('[main]\nhost = https://www.transifex.net\ntype = PO\n')
	for filt in filters:
		comm = ["tx", "set", "--execute", "--auto-local", "--source-lang", "en"]
		comm += ["-r", "%s.%s" % (client.txProject, filt.basename)]
		comm += ["%s_<lang>.po" % (filt.basename)]
		comm += ["--source-file", "%s.pot" % (filt.basename)]
		subprocess.check_output(comm)
	os.chdir(curDir)
