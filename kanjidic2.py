import re

class RMGroup:
        def __init__(self):
                self.readings = []
                self.glosses = {}

class KEntry:
	def __init__(self, literal):
		self.literal = literal
		self.groups = []
		self.grade = 0
		self.freq = 0

literalRe = re.compile('<literal>(.*)</literal>')
rmgroupEndRe = re.compile('</rmgroup>')
entryEndRe = re.compile('</character>')
gradeRe = re.compile('<grade>(.*)</grade>')
freqRe = re.compile('<freq>(.*)</freq>')
readingRe = re.compile('<reading r_type="(.*)">(.*)</reading>')
enMeaningRe = re.compile('<meaning>(.*)</meaning>')
otherMeaningRe = re.compile('<meaning m_lang="(.*)">(.*)</meaning>')
