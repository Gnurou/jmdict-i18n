rsync -v ftp.monash.edu.au::nihongo/JMdict jmdict/JMdict

# temporary fix for syntax issue
sed -i '' 's/\& /\&amp; /g' jmdict/JMdict

rsync -v ftp.monash.edu.au::nihongo/kanjidic2.xml kanjidic2/kanjidic2.xml
