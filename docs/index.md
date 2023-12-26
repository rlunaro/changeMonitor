<img align="left" src="img/icon-64.png">

# changeMonitor

A tool to monitor for changes of files in a given directory, 
as security measure to prevent website hickjack. 

The idea behind ```changeMonitor``` is pretty simple: *what if 
you could check if a website have suffered alteration of a 
file???* Many times you notice this when the website is 
completely hickjacked, rendering impossible to track what files
where changed and when the changed started. 

Yes: you can have security configurations to make impossible 
to change a source file, but many times is impossible to have 
that because the site requires you to have some files that 
allow modification. 

Other times you forgot to disable php execution in some 
directories and hence when an attacker puts a malicious php
file in that directory, it gains instant access to your 
site. 

This tool is to prevent that in some extent: it detects 
any file change in a directory of your interest and 
sends an email every night (or with the periodicity you
want). 

