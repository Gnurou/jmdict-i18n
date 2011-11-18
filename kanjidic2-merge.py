#!/usr/bin/python3

import sys
from gettextformat import *
from kanjidic2 import *

def createEntriesDictionary(gettextEntries):
	kEntries = {}
	for entry in gettextEntries:
		if len(entry.msgstr) == 0: continue
		msgstr = entry.msgstr
		lang = entry.lang

		t = entry.msgctxt.split(' ')
		eid = t[0]
		gid = int(t[1])

		try:
			kEntry = kEntries[eid]
		except KeyError:
			kEntry = KEntry(eid)
			kEntries[eid] = kEntry
		try:
			rmgroup = kEntry.groups[gid]
		except IndexError:
			rmgroup = RMGroup()
			kEntry.groups.append(rmgroup)
		# TODO get readings?
		rmgroup.glosses[lang] = msgstr

if __name__ == "__main__":
	entries = []
	for f in sys.argv[1:]:
                f = GetTextFile(f, "r")
                entries += f.readEntries()
	kEntries = createEntriesDictionary(entries)

	kdict = open("kanjidic2.xml", "r", encoding="utf-8")
	kdicti18n = open("kanjidic2-i18n.xml", "w", encoding="utf-8")
	while True:
		l = kdict.readline()
		kdicti18n.write(l)
		if len(l) == 0: break
