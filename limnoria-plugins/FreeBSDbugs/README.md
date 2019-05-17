# FreeBSDbugs
Limnoria plugin that monitor bugs.freebsd.org/bugzilla/ and echo new PR entries to registered channels.
Once loaded the plugin creates DB file 'freebsdbugs.db' under limnoria's /data folder.
Bot must be in the channel to be able to send bug notices.

#### Plugin Commands
##### add
freebsdbugs add [#channel] [check_interval]
Add [#channel] to receive updates in [check_interval] in seconds. [check_interval] must be between 60 and 600.

#### list
freebsdbugs list
List registered channels and last know bugzilla bug in DB

#### setinterval
freebsdbugs setinterval [#channel] [check_interval]
Change actual [#channel] [check_interval] value in seconds. [check_interval] must be between 60 and 600.

#### setactive
freebsdbugs setactive [#channel]
Set [#channel] active to receive bug updates. Channel receives the 'active' bit automatically when added (the freebsdbugs add command).

#### setinactive
freebsdbugs setinactive [#channel]
Set [#channel] inactive to receive bug updates but doesn't erase channel from the database.
#### remove
freebsdbugs remove [#channel]
Remove [#channel] from the Database.



[![N|Solid](http://onda.qsl.br/wp-content/uploads/2019/05/bsdpower.png)](https://www.freebsd.org/)
