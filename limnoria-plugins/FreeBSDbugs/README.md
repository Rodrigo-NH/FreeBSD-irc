Monitor bugs.freebsd.org/bugzilla/ and echo new PR entries to registered channels

Load plugin: load freebsdbugs

Commands: 'add', 'remove', 'setactive', 'setinactive', 'setinterval', 'list'

Examples:

Adds a new channel: freebsdbugs add #somechannel 15

*15(seconds) -> Interval that plugin checks for new PRs

Remove channel: freebsdbugs remove #somechannel

Sets channel active flag: freebsdbugs setactive #somechannel

Sets channel inactive flag: freebsdbugs setinactive #somechannel

Change channel update interval(seconds): freebsdbugs setinterval #somechannel 60

List registered channels and last know bug in DB: freebsdbugs list
