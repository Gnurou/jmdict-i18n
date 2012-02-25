from gettextformat import *

# PO header
headerStr = """Project-Id-Version: %s
Report-Msgid-Bugs-To: %s
POT-Creation-Date: 2011-11-05 19:00:00+09:00
PO-Revision-Date: 
Last-Translator: 
Language-Team: 
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Language: %s"""

class Filter:
	def __init__(self, basename, project, bugsto):
		self.basename = basename
		self.project = project
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
		if lang == 'en': fstr = "%s.pot" % (self.basename,)
		else: fstr = "%s_%s.po" % (self.basename, lang)
		f = open(fstr, 'w', encoding='utf-8')
		entry = GetTextEntry()
		entry.msgstr = headerStr % (self.project, self.bugsto, lang,)
		f.write(str(entry))
		skeys = self.sortEntries()
		for skey in skeys:
			entry = self.entries[skey].asGettext(lang)
			f.write(str(entry))
