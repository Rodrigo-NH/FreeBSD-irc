# FreeBSDbugcatch
- Catch PR (Problem Report) ID on IRC conversation and return Summary + Link or direct command call.
- Return PR information directly using plugin command

After loaded the plugin will detect the occurrence of the words 'pr' or 'issue' or 'bug' followed by a number and return to channel the relative Summary + Link of corresponding PR in FreeBSD bugzilla (bugs.freebsd.org/bugzilla/) for registered channels.
Besides this automatic functionality the plugin can be used directly as in chat command as explained next.

#### Plugin Commands
##### issue
Considering limnoria's 'config supybot.reply.whenaddressedby.chars !' as example the command use cases are described below.

- !issue 237932
Simple usage, reply to channel with 237932 PR entry Summary + Link

- !issue 237932 @SomeNick
Reply to channel with 237932 PR entry Summary + Link prefixed with nick 'SomeNick'

##### configuration

The automatic functionality will work for registered channels. Use the following configuration to register channels:

conf.supybot.plugins.freebsdbugcatch.channels

#### Help improving this plugin. Issues welcome!


[![N|Solid](http://onda.qsl.br/wp-content/uploads/2019/05/bsdpower.png)](https://www.freebsd.org/)
