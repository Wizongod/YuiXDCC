import hexchat
import binascii
import re

__module_name__ = "Yui XDCC"
__module_version__ = "1.34"
__module_description__ = "Queues and auto-executes XDCC downloads. Checks CRC if available."
__module_author__ = "Wizongod"

# Global Variables for keeping track of things
glob_queue = [] # list of list: [bot_name, pack_no]
downloading = [] # list of list: [bot_name, pack_no, file_name]
downloaded = [] # list of list: [bot_name, pack_no, file_name]

print("\00310\002ユイ\017 v%s plugin by \00311\002Wizongod\017 has been loaded." % __module_version__)



def commander(word, word_eol, userdata):
	if len(word) < 2:
		print("\00310\002Yui>\017 Not enough arguments. Syntaxes are:")
		print("\00310\002Yui>\017 /xdcc queue|remove [<name of bot>] <#pack no.> [<#pack no.>] [<#pack no.>]...")
		print("\00310\002Yui>\017 /xdcc queue|remove [<name of bot>] range <#start> <#end>")
		print("\00310\002Yui>\017 /xdcc view \00315\035#views all queues")
		print("\00310\002Yui>\017 /xdcc view [<bot name>] \00315\035#views queue under <bot name>")
		print("\00310\002Yui>\017 /xdcc start \00315\035#starts the queue download")
		print("\00310\002Yui>\017 /xdcc simul <number> \00315\035#increases to <number> simultaneous downloads")
		print("\00310\002Yui>\017 /xdcc purge \00315\035#purges the whole queue")
		return hexchat.EAT_ALL
	
	global glob_queue

	# Adds pack(s) to global queue
	if word[1] == "queue":
		if len(word) == 2:
			print("\00310\002Yui>\017 Not enough arguments. Syntax is:")
			print("\00310\002Yui>\017 /xdcc queue [<name of bot>] <#pack no.> [<#pack no.>] [<#pack no.>]...")
			print("\00310\002Yui>\017 /xdcc queue [<name of bot>] range <#start> <#end>")
			return hexchat.EAT_ALL
			
		if strip_hash(word[2]).isdigit() or word[2] == "range":
			bot_name = hexchat.get_info('channel')
		else:
			bot_name = word[2]
		pack_list = ""
		if (len(word) > 3 and word[3] == "range") or word[2] == "range":
			if (len(word) != 6 and word[3] == "range") or (len(word) != 5 and word[2] == "range"):
				print("\00310\002Yui>\017 Wrong number of arguments. Syntax is:")
				print("\00310\002Yui>\017 /xdcc queue [<name of bot>] range <#start> <#end>")
				return hexchat.EAT_ALL
			if word[2] == "range":
				start = strip_hash(word[3])
				end = strip_hash(word[4])
			else:
				start = strip_hash(word[4])
				end = strip_hash(word[5])
			if is_valid_pack(start):
				start = int(start)
			else:
				print("\00310\002Yui>\017 %s is not a valid range starting number." % start)
			if is_valid_pack(end):
				end = int(end)
			else:
				print("\00310\002Yui>\017 %s is not a valid range ending number." % end)
			if start <= end:
				print("\00310\002Yui>\017 start number must be larger than end number.")
			for pack in range(start,end+1):
				add_to_queue(bot_name,str(pack))
				pack_list = pack_list + "#%s, " % (pack)
		else:
			if is_valid_pack(word[2]):
				add_to_queue(bot_name,strip_hash(word[2]))
				pack_list = pack_list + "#%s, " % (strip_hash(word[2]))
			if len(word) > 3:
				for pack in word[3:]:
					if is_valid_pack(pack):
						add_to_queue(bot_name,strip_hash(pack))
						pack_list = pack_list + "#%s, " % (strip_hash(pack))
					else:
						print("\00310\002Yui>\017 %s is not a valid pack number." % word[2])
						return hexchat.EAT_ALL
		pack_list = pack_list[:-2]
		print("\00310\002Yui>\017 \00303Added\017 to \00302%s\017's queue: \002%s" % (bot_name,pack_list))
		
		string = "\00310\002Yui>\017 Packs in \00302%s\017's queue: \002" % bot_name	
		for queued_item in glob_queue:
			if queued_item[0] == bot_name:
				string = string + "#%s, " % queued_item[1]
		string = string[:-2]
		print(string)

	# Starts the xdcc download (from the queue)
	elif word[1] == "start":
		dcc_list = hexchat.get_list('dcc')
		active_dl = 0
		if len(dcc_list) > 0:
			for entry in dcc_list:
				if entry.status == 1 and entry.type == 1:
					active_dl += 1
		if active_dl == 0:
			next_XDCC()

	# Views the queued xdcc packs
	elif word[1] == "view":
		if glob_queue == []:
			print("\00310\002Yui>\017 XDCC queue is empty!")
			return hexchat.EAT_ALL
		
		bot_list = {}
		if len(word) == 2:
			for queued_item in glob_queue:
				if queued_item[0] in bot_list:
					bot_list[queued_item[0]].append(queued_item[1])
				else:
					bot_list[queued_item[0]] = [queued_item[1]]
		elif len(word) == 3:
			bot_name = word[2]
			bot_list[bot_name] = []
			for queued_item in glob_queue:
				if bot_name == queued_item[0]:
					bot_list[word[2]].append(queued_item[1])
		else:
			print("\00310\002Yui>\017 Wrong number of arguments. Syntax is:")
			print("\00310\002Yui>\017 /xdcc view \00315\035#views all queues")
			print("\00310\002Yui>\017 /xdcc view [<bot name>] \00315\035#views queue under <bot name>")
			return hexchat.EAT_ALL

		for bot_name,queue in bot_list.items():
			if queue == []:
				print("\00310\002Yui>\017 No packs in \00302%s\017's queue!" % bot_name)
				return hexchat.EAT_ALL
			string = "\00310\002Yui>\017 Packs in \00302%s\017's queue: \002" % bot_name
			for item in queue:
				string = string + "#%s, " % item
			string = string[:-2]
			print(string)

	# Removes the queued xdcc packs
	elif word[1] == "remove":
		if len(word) < 3:
			print("\00310\002Yui>\017 Not enough arguments. Syntax is:")
			print("\00310\002Yui>\017 /xdcc remove [<name of bot>] <#pack no.> [<#pack no.>] [<#pack no.>]...")
			print("\00310\002Yui>\017 /xdcc remove [<name of bot>] range <#start> <#end>")
			return hexchat.EAT_ALL
			
		if strip_hash(word[2]).isdigit() or word[2] == "range":
			bot_name = hexchat.get_info('channel')
		else:
			bot_name = word[2]
		pack_list = ""
		if (len(word) > 3 and word[3] == "range") or word[2] == "range":
			if (word[3] == "range" and len(word) != 6) or (word[2] == "range" and len(word) != 5):
				print("\00310\002Yui>\017 Wrong number of arguments. Syntax is:")
				print("\00310\002Yui>\017 /xdcc remove [<name of bot>] range <#start> <#end>")
				return hexchat.EAT_ALL
			if word[2] == "range":
				start = strip_hash(word[3])
				end = strip_hash(word[4])
			else:
				start = strip_hash(word[4])
				end = strip_hash(word[5])
			if is_valid_pack(start):
				start = int(start)
			else:
				print("\00310\002Yui>\017 %s is not a valid range starting number." % start)
			if is_valid_pack(end):
				end = int(end)
			else:
				print("\00310\002Yui>\017 %s is not a valid range ending number." % end)
			if start >= end:
				print("\00310\002Yui>\017 start number must be smaller than end number.")
			for pack in range(start,end+1):
				remove_from_queue(bot_name,str(pack))
				pack_list = pack_list + "#%s, " % (pack)
		else:
			if is_valid_pack(word[2]):
				remove_from_queue(bot_name,strip_hash(word[2]))
				pack_list = pack_list + "#%s, " % (strip_hash(word[2]))
			if len(word) > 3:
				for pack in word[3:]:
					if is_valid_pack(pack):
						remove_from_queue(bot_name,strip_hash(pack))
						pack_list = pack_list + "#%s, " % (strip_hash(pack))
					else:
						print("\00310\002Yui>\017 %s is not a valid pack number." % word[2])
						return hexchat.EAT_ALL
		pack_list = pack_list[:-2]
		print("\00310\002Yui>\017 \00307Removed\017 packs from \00302%s\017's queue: \002%s" % (bot_name,pack_list))
		
		string = "\00310\002Yui>\017 Packs in \00302%s\017's queue: \002" % bot_name	
		for queued_item in glob_queue:
			if queued_item[0] == bot_name:
				string = string + "#%s, " % queued_item[1]
		string = string[:-2]
		print(string)
	
	# Changes the number of simultaneous downloads. Default is 1.
	elif word[1] == "simul":
		if len(word) != 3:
			print("\00310\002Yui>\017 Wrong number of arguments. Syntax is:")
			print("\00310\002Yui>\017 /xdcc simul <number> \00315\035#increases to <number> simultaneous downloads")
			return hexchat.EAT_ALL
		
		if not word[2].isdigit():
			print("\00310\002Yui>\017 %s is not a valid number of simultaneous downloads." % word[2])
			return hexchat.EAT_ALL

		dcc_list = hexchat.get_list('dcc')
		active_dl = 0
		if len(dcc_list) > 0:
			for entry in dcc_list:
				if entry.status == 1 and entry.type == 1:
					active_dl += 1
			
		if active_dl < int(word[2]):
			for i in range(1,int(word[2])+1-active_dl):
				next_XDCC()

	# Purges the entire download queue
	elif word[1] == "purge":
		glob_queue = []
		print("\00310\002Yui>\017 Queue has been purged.")
		print("\00310\002Yui>\017 Queue is now \035empty.")
			
	else:
		print("\00310\002Yui>\017 %s is not a valid command. Available commands are:" % word[1])
		print("\00310\002Yui>\017 /xdcc queue|remove [<name of bot>] <#pack no.> [<#pack no.>] [<#pack no.>]...")
		print("\00310\002Yui>\017 /xdcc queue|remove [<name of bot>] range <#start> <#end>")
		print("\00310\002Yui>\017 /xdcc view \00315\035#views all queues")
		print("\00310\002Yui>\017 /xdcc view [<bot name>] \00315\035#views queue under <bot name>")
		print("\00310\002Yui>\017 /xdcc start \00315\035#starts the queue download")
		print("\00310\002Yui>\017 /xdcc simul <number> \00315\035#increases to <number> simultaneous downloads")
		print("\00310\002Yui>\017 /xdcc purge \00315\035#purges the whole queue")
	
	return hexchat.EAT_ALL



def add_to_queue(bot_name,number):
	global glob_queue
	glob_queue.append([bot_name,number])
	return



def remove_from_queue(bot_name,number):
	global glob_queue
	for index,queued_item in enumerate(glob_queue):
		if queued_item[0] == bot_name and queued_item[1] == number:
			glob_queue.pop(index)
	return


def next_XDCC(bot_name=None):
	global glob_queue
	global downloading
	if len(glob_queue) > 0:
		rizon = hexchat.find_context(server="irc.rizon.net")
		rizon.command("query %s" % glob_queue[0][0])
		rizon.command("msg %s \00316\026\035\00301xdcc send \017\00316\026\00301\002#%s" % (glob_queue[0][0],glob_queue[0][1]))
		this_bot = glob_queue[0][0]
		glob_queue.pop(0)
		if len(glob_queue) > 0:
			string = "\00310\002Yui>\017 Remaining packs in \00302%s\017's queue: \002" % this_bot
			has_packs_remaining = False
			for queued_item in glob_queue:
				if queued_item[0] == this_bot:
					has_packs_remaining = True
					string = string + "#%s, " % queued_item[1]
			string = string[:-2]
			if has_packs_remaining:
				print(string)
			else:
				print("\00310\002Yui>\017 No more packs in \00302%s\017's queue!" %this_bot)
		else:
			print("\00310\002Yui>\017 No more packs in XDCC queue!")
	else:
		print("\00310\002Yui>\017 XDCC queue is empty!")
	
	return



def XDCC_complete(word, word_eol, userdata):
	file_crc = re.search(r'(\[([0-9A-F]{8}|[0-9a-f]{8})\])|(\(([0-9A-F]{8}|[0-9a-f]{8})\))',word[0])
	if file_crc:
		match = file_crc.group(0)
		if len(match) == 10:
			file_crc = match[1:9]
			cal_crc = hex(binascii.crc32(open(word[1],'rb').read()) & 0xFFFFFFFF)[2:].zfill(8)
			if cal_crc.upper() == file_crc.upper():
				print("\00310\002Yui>\017 Given CRC-> \00316\026\00302\002%s \017\00316\026\00301= \00302\002%s\017 <-Recv CRC \002\00309MATCH!" % (file_crc.upper(),cal_crc.upper()))
			else:
				print("\00304\002\026----------------------------------------")
				print("\00310\002Yui>\017 Given CRC-> \00316\026\00302\002%s \017\00316\026\00301!= \00302\002%s\017 <-Recv CRC \002\00304\026ERROR!" % (file_crc.upper(),cal_crc.upper()))
				print("\00304\002\026----------------------------------------")
		else:
			print("\00310\002Yui>\017 \002\00304\026Regex error.")
	else:
		print("\00310\002Yui>\017 CRC not detected in file name.")
	
	next_XDCC()
	
	return



def unload(userdata):
	hexchat.unhook(command_hook)
	hexchat.unhook(DCC_complete_hook)
	hexchat.unhook(unload_hook)
	print("\00310\002ユイ\017 v%s plugin by \00311\002Wizongod\017 has been unloaded." % __module_version__)
	return



# Hooks for detecting events
command_hook = hexchat.hook_command('xdcc', commander)
DCC_complete_hook = hexchat.hook_print('DCC RECV Complete',XDCC_complete)
unload_hook = hexchat.hook_unload(unload)



def is_valid_pack(pack_no):
	if strip_hash(pack_no).isdigit():
		return True
	else:
		return False



def strip_hash(string):
	if string[0] == "#":
		return string[1:]
	else:
		return string
