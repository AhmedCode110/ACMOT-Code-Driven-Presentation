-- Finalize the generated editable PPTX in Keynote on macOS.
-- Usage:
-- osascript scripts/finalize_keynote.applescript <input.pptx> <video.mp4> <output.key> <output.pptx>
--
-- Keep this script deliberately simple. Some Keynote builds expose imported
-- PowerPoint slides/movies through proxy collections that do not understand
-- AppleScript's `count` message reliably. We therefore avoid collection-count
-- checks and always start from the freshly generated PPTX.

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
        set theDoc to open (POSIX file inputPptx)
        delay 3

        set docWidth to width of theDoc
        set docHeight to height of theDoc
        set targetSlide to slide 59 of theDoc

        tell targetSlide
            -- The source is a freshly built PPTX, so no destructive movie cleanup
            -- is needed here. Keynote imports a supported MP4 through `make new
            -- image`; for movie files the resulting object is a native movie item
            -- stored inside the Keynote package.
            set thisMovie to make new image with properties {file:movieAlias}
            delay 1

            tell thisMovie
                set movWidth to (docWidth * 40) div 100
                set width to movWidth
                set movHeight to height

                -- Bottom-right demo region. Keep the official comparison blocks
                -- readable and leave a small safe margin around the movie.
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
