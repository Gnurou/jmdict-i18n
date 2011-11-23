import re

entryStartRe = re.compile('<ent_seq>(.*)</ent_seq>')
kebRe = re.compile('<keb>(.*)</keb>')
rebRe = re.compile('<reb>(.*)</reb>')
senseStartRe = re.compile('<sense>')
senseEndRe = re.compile('</sense>')
enGlossRe = re.compile('<gloss>(.*)</gloss>')
otherGlossRe = re.compile('<gloss xml:lang="(.*)">(.*)</gloss>')

class Entry:
	def __init__(self):
		self.eid = None
		self.keb = None
		self.reb = None
		# Associates sense index to Sense instance
		self.senses = {}

class Sense:
	def __init__(self):
		# Associates language code to array of strings
		self.glosses = {}
