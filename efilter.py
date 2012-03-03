from gettextformat import *
import os, datetime

# PO header
headerStr = """Project-Id-Version: %s
Report-Msgid-Bugs-To: %s
POT-Creation-Date: %s
PO-Revision-Date: 
Last-Translator: 
Language-Team: 
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Language: %s"""

class Filter:
	def __init__(self, basename, projectShort, project, bugsto):
		self.basename = basename
		self.projectShort = projectShort
		self.project = project
		self.poDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S%z") 
		self.bugsto = bugsto
		self.entries = {}

	def consider(self, entry):
		if self.isfiltered(entry):
			self.entries[entry.contextString()] = entry
			return True
		return False

	def sortEntries(self):
		return sorted(self.entries)

	def output(self, lang):
		if not os.path.exists(self.projectShort): os.mkdir(self.projectShort)
		if lang == 'en': fstr = "%s/%s.pot" % (self.projectShort, self.basename,)
		else: fstr = "%s/%s_%s.po" % (self.projectShort, self.basename, lang)
		f = open(fstr, 'w', encoding='utf-8')
		entry = GetTextEntry()
		entry.msgstr = headerStr % (self.project, self.bugsto, self.poDate, lang,)
		f.write(str(entry))
		skeys = self.sortEntries()
		cpt = 0
		for skey in skeys:
			entry = self.entries[skey].asGettext(lang)
			if lang == 'en' or entry.trString(lang) != '': cpt += 1
			f.write(str(entry))
		return cpt
