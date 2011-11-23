# Contains the list of langs officially supported in the project
langs = [ 'en', 'fr', 'es', 'pt', 'de', 'ru', 'it', 'th', 'vi' ]

# Associate 3 letters country codes used in glosses to more common 2 letter ones.
# This also defines which languages we are exporting to
langMatch = { "fre" : "fr", "ger" : "de", "rus" : "ru", "ita" : 'it', "tha" : 'th', 'vie' : 'vi' }
langMatchInv = dict([ (v, k) for k, v in langMatch.items() ])
