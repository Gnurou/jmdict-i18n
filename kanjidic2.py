import re

class KEntry:
	def __init__(self, literal):
		self.literal = literal
		self.groups = []
		self.grade = 0

literalRe = re.compile('<literal>(.*)</literal>')
rmgroupEndRe = re.compile('</rmgroup>')
entryEndRe = re.compile('</character>')
gradeRe = re.compile('<grade>(.*)</grade>')
enMeaningRe = re.compile('<meaning>(.*)</meaning>')
readingRe = re.compile('<reading r_type="(.*)">(.*)</reading>')
otherMeaningRe = re.compile('<meaning m_lang="(.*)">(.*)</meaning>')
