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
        set theDoc to open (POSIX file inputPptx)
        delay 2

        if (count of slides of theDoc) is not 67 then
            close theDoc saving no
            error "Expected 67 slides before Keynote finalization."
        end if

        set docWidth to width of theDoc
        set docHeight to height of theDoc

        tell slide 59 of theDoc
            -- Make the operation idempotent when the finalizer is run again.
            repeat while (count of movies) > 0
                delete movie 1
            end repeat

            -- Keynote imports a movie through the image make verb; the returned
            -- object is a native movie item embedded in the presentation.
            set thisMovie to make new image with properties {file:movieAlias}
            tell thisMovie
                set movWidth to (docWidth * 42) div 100
                set width to movWidth
                set movHeight to height

                -- Keep the video on the right side of the final comparison slide,
                -- leaving the official metrics readable on the left/upper blocks.
                set xPos to (docWidth * 55) div 100
                set yPos to (docHeight * 43) div 100
                if (xPos + movWidth) > docWidth then set xPos to docWidth - movWidth - 20
                if (yPos + movHeight) > docHeight then set yPos to docHeight - movHeight - 20
                set position to {xPos, yPos}
                set movie volume to 80
                set repetition method to none
            end tell
        end tell

        -- Save the primary Mac version, then export the same document to PPTX.
        save theDoc in outputKey
        export theDoc to (POSIX file outputPptx) as Microsoft PowerPoint
        close theDoc saving yes
    end tell
end run
