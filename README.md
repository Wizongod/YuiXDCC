# Yui XDCC
Description: A simple manager for Hexchat that allows you to queue XDCC downloads for anime on the Rizon network (only).

## Commands
If you type anything that's not in this list of commands below, Yui will prompt you with the correct syntax, so don't worry.

In general, if you don't put the name of the bot you're trying to queue packs on, then it is assumed that it is the bot of the channel(tab) which you are currently typing the commands into.

`/xdcc queue|remove [<name of bot>] <#pack no.> [<#pack no.>] [<#pack no.>]...` adds packs to queue (discrete numbers)

`/xdcc queue|remove [<name of bot>] range <#start> <#end>` adds packs to queue from <#start> to <#end> in continuous numbers

`/xdcc view \00315\035` views all queues

`/xdcc view [<bot name>]` views queue under <bot name>

`/xdcc start` starts the download from the first item in queue

`/xdcc simul <number>` increases the number of simultaneous downloads to <number>

`/xdcc purge` purges (empties) all queues
