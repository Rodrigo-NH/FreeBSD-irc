# FreeBSDman
Limnoria plugin that replies with manpage description and link.

#### Plugin Commands
##### man
man command can be issued directly in the channel prefixed with chars as set in supybot.reply.whenaddressedby.chars variable.

man <command>[(section)] @[nick]
Output <command> description from manpage of selected [(section)] and redirects output to @[nick] in the channel. 


Considering 'config supybot.reply.whenaddressedby.chars !' as example, the command use cases are described below.




- !man groff
Simple usage, reply to channel with command's manpage

- !man zfs(8)
Same as above but also define wanted section

- !man ls @SomeNick
Append result replied on channel with 'SomeNick' nick

- !man zfs(8) @SomeNick
Same as above but also define wanted section


[![N|Solid](http://onda.qsl.br/wp-content/uploads/2019/05/bsdpower.png)](https://www.freebsd.org/)
