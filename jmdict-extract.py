#!/usr/bin/python3
import sys
from gettextformat import *
from jmdict import *

# PO header
header = """msgid ""
msgstr ""
"Project-Id-Version: JMdict i18n\\n"
"Report-Msgid-Bugs-To: Alexandre Courbot <gnurou@gmail.com>\\n"
"POT-Creation-Date: 2011-11-05 19:00:00+09:00\\n"
"PO-Revision-Date: 2011-11-05 10:43+0000\\n"
"Last-Translator: \\n"
"Language-Team: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n\""""

currentEntry = None

def startEntry(match):
	global currentEntry
	currentEntry = Entry()
	currentEntry.eid = int(match.group(1))
	currentEntry.senseNbr = 0

def keb(match):
	if not currentEntry.keb:
		currentEntry.keb = match.group(1)
	pass

def reb(match):
	if not currentEntry.reb:
		currentEntry.reb = match.group(1)
	pass

def startSense(match):
	global currentEntry
	sense = Sense()
	currentEntry.sense = sense

def writeSense(f, currentEntry, glosses):
	entry = GetTextEntry('')
	entry.msgctx = '%d %d' % (currentEntry.eid, currentEntry.senseNbr)
	# Japanese keb and reb
	if not currentEntry.keb: ids = [ '%s\\n' % (currentEntry.reb,) ]
	else: ids = [ '%s\t%s\\n' % (currentEntry.keb, currentEntry.reb) ]
	# English glosses
	enGlosses = [ '%s\\n' % (gloss,) for gloss in currentEntry.sense.glosses['en'] ]
	# Remove last CR
	enGlosses[-1] = enGlosses[-1][:-2]
	ids += enGlosses
	entry.msgid = ids
	tGlosses = [ '%s\\n' % (gloss,) for gloss in glosses ]
	# Remove last CR
	if len(tGlosses): tGlosses[-1] = tGlosses[-1][:-2]
	entry.msgstr = tGlosses
	f.writeEntry(entry)

def endSense(match):
	global currentEntry
	# Move to filter functions
	global jlpt4list
	if currentEntry.eid in jlpt4list: clpo = lpo4
	elif currentEntry.eid in jlpt3list: clpo = lpo3
	elif currentEntry.eid in jlpt2list: clpo = lpo2
	elif currentEntry.eid in jlpt1list: clpo = lpo1
	else: return

	# Dump all senses
	writeSense(clpo['en'], currentEntry, [])
	for lang in langMatch.values():
		if not lang in currentEntry.sense.glosses: glosses = []
		else: glosses = currentEntry.sense.glosses[lang]
		writeSense(clpo[lang], currentEntry, glosses)

	currentEntry.sense = None
	currentEntry.senseNbr += 1

def processGloss(lang, gloss):
	global currentEntry
	try:
		glosses = currentEntry.sense.glosses[lang]
	except KeyError:
		glosses = []
		currentEntry.sense.glosses[lang] = glosses
	glosses.append(gloss.replace('"', '\\"'))
	
def foundOtherGloss(match):
	lang = langMatch[match.group(1)]
	gloss = match.group(2)
	processGloss(lang, gloss)

def foundEnGloss(match):
	gloss = match.group(1)
	processGloss('en', gloss)
	
actions = {
	entryStartRe	: startEntry,
	kebRe		: keb,
	rebRe		: reb,
	senseStartRe	: startSense,
	senseEndRe	: endSense,
	enGlossRe	: foundEnGloss,
	otherGlossRe	: foundOtherGloss,
}

def parseFile(f, actions):
	while True:
		line = f.readline()
		for rexp in actions:
			match = rexp.match(line)
			if rexp.match(line):
				actions[rexp](match)
				continue
		if len(line) == 0: break

jlpt4list = [ int(x) for x in open("jlpt-level4.txt").read().split('\n')[:-1] ]
jlpt3list = [ int(x) for x in open("jlpt-level3.txt").read().split('\n')[:-1] ]
jlpt2list = [ int(x) for x in open("jlpt-level2.txt").read().split('\n')[:-1] ]
jlpt1list = [ int(x) for x in open("jlpt-level1.txt").read().split('\n')[:-1] ]

if __name__ == "__main__":
	# Dictionary file
	jmdict = open('JMdict', 'r', encoding='utf-8')
	# Translation and template files
	lpo4 = dict([(lang, GetTextFile('jmdict-i18n_jlpt5_%s.po' % (lang,), 'w')) for lang in langMatch.values()])
	lpo4['en'] = GetTextFile('jmdict-i18n_jlpt5.pot', 'w')
	lpo3 = dict([(lang, GetTextFile('jmdict-i18n_jlpt4_%s.po' % (lang,), 'w')) for lang in langMatch.values()])
	lpo3['en'] = GetTextFile('jmdict-i18n_jlpt4_.pot', 'w')
	lpo2 = dict([(lang, GetTextFile('jmdict-i18n_jlpt2_%s.po' % (lang,), 'w')) for lang in langMatch.values()])
	lpo2['en'] = GetTextFile('jmdict-i18n_jlpt2.pot', 'w')
	lpo1 = dict([(lang, GetTextFile('jmdict-i18n_jlpt1_%s.po' % (lang,), 'w')) for lang in langMatch.values()])
	lpo1['en'] = GetTextFile('jmdict-i18n_jlpt1.pot', 'w')

	for lang in list(langMatch.values()) + ['en']:
		lpo4[lang].f.write("%s\n" % (header,))
		lpo4[lang].f.write('"Language: %s\\n"\n' % (lang))
		lpo3[lang].f.write("%s\n" % (header,))
		lpo3[lang].f.write('"Language: %s\\n"\n' % (lang))
		lpo2[lang].f.write("%s\n" % (header,))
		lpo2[lang].f.write('"Language: %s\\n"\n' % (lang))
		lpo1[lang].f.write("%s\n" % (header,))
		lpo1[lang].f.write('"Language: %s\\n"\n' % (lang))
	# And parse!
	parseFile(jmdict, actions)
