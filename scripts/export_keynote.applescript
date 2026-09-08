-- export_keynote.applescript
-- Opens the final V7 PPTX in Keynote and saves it as a native .key document.
--
-- Usage:  osascript scripts/export_keynote.applescript <input.pptx> <output.key>
--
-- Keynote automation is fragile (historic -1708 / -1700 / -1728 / -1712
-- errors), so the caller must treat failure as non-fatal: the PPTX remains
-- the authoritative deliverable.

on run argv
	set pptxPath to item 1 of argv
	set keyPath to item 2 of argv

	set pptxFile to POSIX file pptxPath
	set keyFile to POSIX file keyPath

	tell application "Keynote"
		activate
		-- Opening a .pptx makes Keynote import and convert it
		set theDoc to open pptxFile

		-- Give the import time to settle on a large deck
		delay 5

		-- Save as a native Keynote document at the requested path
		save theDoc in keyFile

		delay 2
		close theDoc saving no
	end tell

	return "saved: " & keyPath
end run
