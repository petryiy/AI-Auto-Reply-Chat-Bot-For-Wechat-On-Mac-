-- get_wechat_messages_robust_fixed.applescript
on run
    try
        tell application "System Events"
            if not (exists process "WeChat") then
                return "Error: WeChat process not found."
            end if

            tell process "WeChat"
                if not (exists window 1) then
                    return "Error: Main WeChat window not found."
                end if

                tell window 1
                    tell splitter group 1
                        tell splitter group 1
                            tell scroll area 1
                                -- 用索引 table 1 而不是 "Messages"
                                if not (exists table 1) then
                                    return "Error: Messages table not found."
                                end if

                                tell table 1
                                    set allMessages to ""
                                    set rowCount to count of rows

                                    repeat with i from 1 to rowCount
                                        tell row i
                                            try
                                                -- 直接用 UI element 1
                                                set msgText to value of UI element 1
                                                if msgText is not missing value and msgText is not "" then
                                                    set allMessages to allMessages & msgText & "\n"
                                                end if
                                            on error
                                                try
                                                    set msgText to title of UI element 1
                                                    if msgText is not missing value and msgText is not "" then
                                                        set allMessages to allMessages & msgText & "\n"
                                                    end if
                                                end try
                                            end try
                                        end tell
                                    end repeat

                                    return allMessages
                                end tell
                            end tell
                        end tell
                    end tell
                end tell
            end tell
        end tell
    on error errMsg number errNum
        return "AppleScript Error: " & errMsg & " (Number: " & errNum & ")"
    end try
end run

