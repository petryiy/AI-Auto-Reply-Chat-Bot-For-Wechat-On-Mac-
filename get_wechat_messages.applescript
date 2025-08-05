-- get_wechat_messages_robust_fixed.applescript
on run
    tell application "System Events"
        if not (exists process "WeChat") then
            return "Error: WeChat process not found."
        end if
        try
            tell process "WeChat"
                set frontmost to true
                delay 0.2

                tell window 1
                    -- 取第二个 scroll area（第一个是聊天列表）
                    tell scroll area 2
                        tell table 1
                            set allMessages to ""
                            set rowList to rows

                            repeat with aRow in rowList
                                set gotText to false
                                repeat with elem in UI elements of aRow
                                    if not gotText then
                                        try
                                            set txt to value of elem
                                            if txt is not missing value and txt ≠ "" then
                                                set allMessages to allMessages & txt & "\n"
                                                set gotText to true
                                            end if
                                        end try
                                        if not gotText then
                                            try
                                                set txt to title of elem
                                                if txt is not missing value and txt ≠ "" then
                                                    set allMessages to allMessages & txt & "\n"
                                                    set gotText to true
                                                end if
                                            end try
                                        end if
                                    end if
                                end repeat
                            end repeat

                            return allMessages
                        end tell
                    end tell
                end tell
            end tell
        on error errMsg number errNum
            return "AppleScript Error: " & errMsg & " (Code: " & errNum & ")"
        end try
    end tell
end run
