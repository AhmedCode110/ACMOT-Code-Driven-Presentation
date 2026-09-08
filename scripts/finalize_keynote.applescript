-- Save the generated editable V5 deck as Keynote and export a PowerPoint copy.
-- Video embedding is finalized by scripts/embed_video_v5.py after this step.
on run argv
    if (count of argv) is not 4 then error "Expected input PPTX, video MP4, output KEY, output PPTX"
    set inputPptx to item 1 of argv
    set outputKey to item 3 of argv
    set outputPptx to item 4 of argv
    tell application "Keynote"
        activate
        open (POSIX file inputPptx)
        delay 6
        set theDoc to front document
        save theDoc in (POSIX file outputKey)
        delay 4
        export theDoc to (POSIX file outputPptx) as Microsoft PowerPoint
        delay 4
        close theDoc saving yes
    end tell
end run
