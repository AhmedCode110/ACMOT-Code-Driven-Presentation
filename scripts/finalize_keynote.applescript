-- Finalize the generated editable PPTX in Keynote on macOS.
-- Usage:
-- osascript scripts/finalize_keynote.applescript <input.pptx> <video.mp4> <output.key> <output.pptx>

on run argv
    if (count of argv) is not 4 then
        error "Expected 4 arguments: input PPTX, video MP4, output KEY, output PPTX"
    end if

    set inputPptx to item 1 of argv
    set videoPath to item 2 of argv
    set outputKey to item 3 of argv
    set outputPptx to item 4 of argv
    set movieAlias to (POSIX file videoPath) as alias

    tell application "Keynote"
        activate
        open (POSIX file inputPptx)
        delay 4

        -- Some Keynote builds return missing value from `open`. Always bind the
        -- actual document explicitly from the front window instead.
        set theDoc to front document
        if theDoc is missing value then error "Keynote opened the PPTX but no front document was available."

        -- Use the document canvas size only after front document is resolved.
        set docWidth to width of theDoc
        set docHeight to height of theDoc
        set targetSlide to slide 59 of theDoc

        tell targetSlide
            set thisMovie to make new image with properties {file:movieAlias}
            delay 2

            if thisMovie is missing value then error "Keynote did not create a movie/image object from the selected video."

            tell thisMovie
                set movWidth to (docWidth * 40) div 100
                set width to movWidth

                -- Do not depend on Keynote reporting intrinsic movie height during
                -- import. Force a stable 16:9 box that fits the slide safely.
                set movHeight to (movWidth * 9) div 16
                set height to movHeight

                set xPos to (docWidth * 57) div 100
                set yPos to (docHeight * 48) div 100
                if (xPos + movWidth) > (docWidth - 18) then set xPos to docWidth - movWidth - 18
                if (yPos + movHeight) > (docHeight - 18) then set yPos to docHeight - movHeight - 18
                set position to {xPos, yPos}
            end tell
        end tell

        delay 1
        save theDoc in outputKey
        delay 2
        export theDoc to (POSIX file outputPptx) as Microsoft PowerPoint
        delay 2
        close theDoc saving yes
    end tell
end run
