#!/usr/bin/python3

import sys
from gettextformat import *
from jmdict import *
from langs import *

# PO header
headerStr = """Project-Id-Version: JMdict i18n
Report-Msgid-Bugs-To: Alexandre Courbot <gnurou@gmail.com>
POT-Creation-Date: 2011-11-05 19:00:00+09:00
PO-Revision-Date: 
Last-Translator: 
Language-Team: 
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Language: %s"""

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
	entry = GetTextEntry()
	entry.msgctxt = '%d %d' % (currentEntry.eid, currentEntry.senseNbr)
	# Japanese keb and reb
	if not currentEntry.keb: ids = '%s' % (currentEntry.reb,)
	else: ids = '%s\t%s' % (currentEntry.keb, currentEntry.reb)
	# English glosses
	entry.msgid = ids + '\n' + currentEntry.sense.glosses['en'].rstrip('\n')
	entry.msgstr = glosses.rstrip('\n')
	f.write(str(entry))

def endSense(match):
	global currentEntry

	# Do not worry about senses without English glosses
	if not 'en' in currentEntry.sense.glosses: return

	# Move to filter functions
	global jlpt4list
	if currentEntry.eid in jlpt4list: clpo = lpo4
	elif currentEntry.eid in jlpt3list: clpo = lpo3
	elif currentEntry.eid in jlpt2list: clpo = lpo2
	elif currentEntry.eid in jlpt1list: clpo = lpo1
	else: return

	# Dump all senses
	writeSense(clpo['en'].f, currentEntry, "")
	for lang in langMatch.values():
		if not lang in currentEntry.sense.glosses: glosses = ""
		else: glosses = currentEntry.sense.glosses[lang]
		writeSense(clpo[lang].f, currentEntry, glosses)

	currentEntry.sense = None
	currentEntry.senseNbr += 1

def processGloss(lang, gloss):
	global currentEntry
	try:
		glosses = currentEntry.sense.glosses[lang]
	except KeyError:
		glosses = ""
	glosses += gloss + "\n"
	currentEntry.sense.glosses[lang] = glosses
	
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
	jmdict = open(sys.argv[1], 'r', encoding='utf-8')
	# Translation and template files
	lpo4 = dict([(lang, GetTextFile('jmdict-jlpt5_%s.po' % (lang,), 'w')) for lang in langMatch.values()])
	lpo4['en'] = GetTextFile('jmdict-jlpt5.pot', 'w')
	lpo3 = dict([(lang, GetTextFile('jmdict-jlpt4_%s.po' % (lang,), 'w')) for lang in langMatch.values()])
	lpo3['en'] = GetTextFile('jmdict-jlpt4.pot', 'w')
	lpo2 = dict([(lang, GetTextFile('jmdict-jlpt2_%s.po' % (lang,), 'w')) for lang in langMatch.values()])
	lpo2['en'] = GetTextFile('jmdict-jlpt2.pot', 'w')
	lpo1 = dict([(lang, GetTextFile('jmdict-jlpt1_%s.po' % (lang,), 'w')) for lang in langMatch.values()])
	lpo1['en'] = GetTextFile('jmdict-jlpt1.pot', 'w')

	header= GetTextEntry()
	header.msgstr = headerStr
	for lang in list(langMatch.values()) + ['en']:
		lpo4[lang].f.write(str(header) % (lang,))
		lpo3[lang].f.write(str(header) % (lang,))
		lpo2[lang].f.write(str(header) % (lang,))
		lpo1[lang].f.write(str(header) % (lang,))
	# And parse!
	parseFile(jmdict, actions)
