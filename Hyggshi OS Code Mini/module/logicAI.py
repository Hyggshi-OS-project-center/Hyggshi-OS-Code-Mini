# logicAI.py
# Hyggshi OS - Lua logic for AI fallback
# This file is intended to be loaded and executed by lupa.LuaRuntime in ChatAI.py

def on_user_message(message):
    """
    Hàm Python giả lập cho Lua: trả lời mặc định khi không có API.
    Nếu bạn dùng Lua thực sự, hãy viết logic trong file logicAI.lua.
    """
    if not message.strip():
        return "Xin hãy nhập câu hỏi hoặc nội dung bạn muốn hỏi AI."
    if "hello" in message.lower() or "hi" in message.lower():
        return "Xin chào! Tôi là trợ lý AI của bạn. Hãy hỏi tôi bất cứ điều gì."
    if "python" in message.lower():
        return "Bạn muốn hỏi gì về Python? Tôi có thể giúp bạn giải thích, sửa lỗi hoặc viết code mẫu."
    return f"Bạn vừa nói: {message}\n(Tôi là AI offline, hãy cấu hình API để sử dụng AI thực sự!)"

# Nếu bạn muốn dùng Lua thực sự, hãy tạo file logicAI.lua với nội dung tương tự:
# function on_user_message(message)
#     if message == "" then
#         return "Xin hãy nhập câu hỏi hoặc nội dung bạn muốn hỏi AI."
#     end
#     if string.find(string.lower(message), "hello") or string.find(string.lower(message), "hi") then
#         return "Xin chào! Tôi là trợ lý AI của bạn. Hãy hỏi tôi bất cứ điều gì."
#     end
#     if string.find(string.lower(message), "python") then
#         return "Bạn muốn hỏi gì về Python? Tôi có thể giúp bạn giải thích, sửa lỗi hoặc viết code mẫu."
#     end
#     return "Bạn vừa nói: " .. message .. "\n(Tôi là AI offline, hãy cấu hình API để sử dụng AI thực sự!)"
# end