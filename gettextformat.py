import re

msgctxRe = re.compile('msgctxt "(.*)"')
msgidRe = re.compile('msgid "(.*)"')
msgstrRe = re.compile('msgstr "(.*)"')
strRe = re.compile('"(.*)"')
languageRe = re.compile('"Language: (..)\\\\n"')

class GetTextEntry:
	def __init__(self, lang):
		self.msgctx = ""
		self.msgid = []
		self.msgstr = []
		self.lang = lang

class GetTextFile:
	def __init__(self, name, mode):
		self.f = open(name, mode, encoding='utf-8')

	def readEntries(self):
		# Find language in header
		while True:
			l = self.f.readline()
			match = languageRe.match(l)
			if (match):
				lang = match.group(1)
				break
			if len(l) == 0: break
		# Skip until first entry
		while True:
			l = self.f.readline()
			if l == '\n': break
			if len(l) == 0: break
		# Now we can parse the entries
		entries = []
		currentEntry = None
		mode = None
		while True:
			l = self.f.readline()
			if l == '\n':
				if currentEntry:
					entries.append(currentEntry)
					currentEntry = None
					mode = None
				continue
			if mode == "ID" and strRe.match(l):
				currentEntry.msgid.append(strRe.match(l).group(1).replace('\\"', '"'))
				continue
			elif mode == "STR" and strRe.match(l):
				currentEntry.msgstr.append(strRe.match(l).group(1).replace('\\"', '"'))
				continue
			else: mode = None
			match = msgctxRe.match(l)
			if match:
				if not currentEntry: currentEntry = GetTextEntry(lang)
				currentEntry.msgctx = match.group(1)
				continue
			match = msgidRe.match(l)
			if match:
				if not currentEntry: currentEntry = GetTextEntry(lang)
				s = match.group(1)
				if len(s): currentEntry.msgid.append(s.replace('\\"', '"'))
				mode = "ID"
				continue
			match = msgstrRe.match(l)
			if match:
				s = match.group(1)
				if len(s): currentEntry.msgstr.append(s.replace('\\"', '"'))
				mode = "STR"
				continue
			if len(l) == 0: break
		if currentEntry: entries.append(currentEntry)
		return entries

	def writeEntry(self, entry):
		f = self.f
		f.write('\n')
		f.write('msgctxt "%s"\n' % (entry.msgctx,))
		f.write('msgid ""\n')
		for s in entry.msgid:
			f.write('"%s"\n' % (s,))
		f.write('msgstr ""\n')
		for s in entry.msgstr:
			f.write('"%s"\n' % (s,))
