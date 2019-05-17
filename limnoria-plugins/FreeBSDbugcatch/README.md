# FreeBSDbugcatch
Catch PR ID on IRC talk and return Summary + Link or direct command call.

After loaded the plugin will detect every occurrence of the words 'pr' or 'issue' or 'bug' followed by a number are sent to channel and return Summary + Link of corresponding bug in FreeBSD bugzilla (bugs.freebsd.org/bugzilla/). For this to work, channels must be set in the Limnoria variable conf.supybot.plugins.freebsdbugcatch.channels.
Beside this functionality the plugin can be used directly as in chat command as explained next.

#### Plugin Commands
##### issue
Considering 'config supybot.reply.whenaddressedby.chars !' as example, the command use cases are described below.

- !issue 237932
Simple usage, reply to channel with 237932 PR entry Summary + Link

- !issue 237932 @SomeNick
Reply to channel with 237932 PR entry Summary + Link prefixed with nick 'SomeNick'

[![N|Solid](http://onda.qsl.br/wp-content/uploads/2019/05/bsdpower.png)](https://www.freebsd.org/)
