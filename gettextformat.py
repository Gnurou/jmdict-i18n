import re

msgctxtRe = re.compile('msgctxt "(.*)"')
msgidRe = re.compile('msgid "(.*)"')
msgstrRe = re.compile('msgstr "(.*)"')
fuzzyRe = re.compile('#,.*fuzzy.*')
strRe = re.compile('"(.*)"')
languageRe = re.compile('"Language: (..)')

def gettextize(s):
	return s.replace('"', '\\"').replace('\n', '\\n"\n"').replace('\t', '\\t').replace('&', '&amp;')

def ungettextize(s):
	return s.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('&amp;', '&')

class GetTextEntry:
	def __init__(self, lang = ''):
		self.msgctxt = ""
		self.msgid = ""
		self.msgstr = ""
		self.lang = lang
		self.fuzzy = False

	def contextString(self):
		return self.msgctxt

	def sourceString(self):
		return self.msgid

	def trString(self, lang):
		if lang != self.lang: return ''
		else: return self.msgstr

	def __str__(self):
		r = ""
		if self.fuzzy: r += '#, fuzzy\n'
		if self.msgctxt:
			r += 'msgctxt "%s"\n' % (self.msgctxt,)
		s = gettextize(self.msgid)
		if '\n' in s: s = '"\n"' + s
		r += 'msgid "%s"\n' % (s,)
		s = gettextize(self.msgstr)
		if '\n' in s: s = '"\n"' + s
		r += 'msgstr "%s"\n' % (s,)
		r += '\n'
		return r

def readPo(f):
	# Find language in header
	while True:
		l = f.readline()
		match = languageRe.match(l)
		if (match):
			lang = match.group(1)
			break
		if len(l) == 0: break
	# Skip until first entry
	while True:
		l = f.readline()
		if l == '\n' or len(l) == 0: break

	# Now we can parse the entries
	entries = []
	currentEntry = None
	mode = None
	while True:
		l = f.readline()
		if l == '\n':
			if currentEntry:
				entries.append(currentEntry)
				currentEntry = None
				mode = None
			continue
		if mode == "ID" and strRe.match(l):
			currentEntry.msgid += strRe.match(l).group(1)
			continue
		elif mode == "STR" and strRe.match(l):
			currentEntry.msgstr += strRe.match(l).group(1)
			continue
		else: mode = None
		match = msgctxtRe.match(l)
		if match:
			if not currentEntry: currentEntry = GetTextEntry(lang)
			currentEntry.msgctxt = match.group(1)
			continue
		match = msgidRe.match(l)
		if match:
			if not currentEntry: currentEntry = GetTextEntry(lang)
			s = match.group(1)
			if len(s): currentEntry.msgid += s
			mode = "ID"
			continue
		match = msgstrRe.match(l)
		if match:
			s = match.group(1)
			if len(s): currentEntry.msgstr += s
			mode = "STR"
			continue
		match = fuzzyRe.match(l)
		if match:
			if not currentEntry: currentEntry = GetTextEntry(lang)
			currentEntry.fuzzy = True
			continue
		if len(l) == 0: break
	if currentEntry: entries.append(currentEntry)
	for entry in entries:
		entry.msgid = ungettextize(entry.msgid)
		entry.msgstr = ungettextize(entry.msgstr)
	return entries
