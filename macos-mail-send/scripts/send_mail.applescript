on _splitAndTrim(theText, theDelim)
	set oldTIDs to AppleScript's text item delimiters
	set AppleScript's text item delimiters to theDelim
	set rawItems to every text item of (theText as text)
	set AppleScript's text item delimiters to oldTIDs

	set outItems to {}
	repeat with oneItem in rawItems
		set t to (oneItem as text)
		set t to my _trim(t)
		if t is not "" then set end of outItems to t
	end repeat
	return outItems
end _splitAndTrim

on _trim(s)
	set s to (s as text)
	set ws to {space, tab, return, linefeed}
	repeat while s is not "" and (character 1 of s) is in ws
		set s to text 2 thru -1 of s
	end repeat
	repeat while s is not "" and (character -1 of s) is in ws
		set s to text 1 thru -2 of s
	end repeat
	return s
end _trim

on _toBool(s)
	set s to (s as text)
	if s is "1" then return true
	if s is "true" then return true
	if s is "TRUE" then return true
	return false
end _toBool

on run argv
	(*
	argv layout:
	1: to (comma-separated, required)
	2: cc (comma-separated, optional)
	3: bcc (comma-separated, optional)
	4: subject (string, may be empty)
	5: body (plain text, may be empty)
	6: mode ("draft" | "send")
	7: visible ("0"|"1")
	8+: attachments (POSIX paths)
	*)

	if (count of argv) < 7 then error "Usage: send_mail.applescript <to> <cc> <bcc> <subject> <body> <mode> <visible> [attachments...]"

	set toRaw to item 1 of argv
	set ccRaw to item 2 of argv
	set bccRaw to item 3 of argv
	set theSubject to item 4 of argv
	set theBody to item 5 of argv
	set theMode to item 6 of argv
	set isVisible to my _toBool(item 7 of argv)

	set toList to my _splitAndTrim(toRaw, ",")
	set ccList to my _splitAndTrim(ccRaw, ",")
	set bccList to my _splitAndTrim(bccRaw, ",")

	if (count of toList) is 0 then error "Missing --to recipient(s)."
	if theMode is not "draft" and theMode is not "send" then error "Invalid mode; expected 'draft' or 'send'."

	set attachPaths to {}
	if (count of argv) > 7 then
		repeat with i from 8 to (count of argv)
			set p to my _trim(item i of argv)
			if p is not "" then set end of attachPaths to p
		end repeat
	end if

	tell application "Mail"
		set newMessage to make new outgoing message with properties {subject:theSubject, content:(theBody & return & return), visible:isVisible}

		tell newMessage
			repeat with a in toList
				make new to recipient at end of to recipients with properties {address:(a as text)}
			end repeat

			repeat with a in ccList
				make new cc recipient at end of cc recipients with properties {address:(a as text)}
			end repeat

			repeat with a in bccList
				make new bcc recipient at end of bcc recipients with properties {address:(a as text)}
			end repeat

			repeat with p in attachPaths
				set theFile to POSIX file (p as text) as alias
				make new attachment with properties {file name:theFile} at after last paragraph
			end repeat
		end tell

		if theMode is "send" then
			-- This may throw if Mail.app is not configured or macOS permissions block automation.
			send newMessage
		end if
	end tell
end run
