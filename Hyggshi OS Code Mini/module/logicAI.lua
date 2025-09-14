-- logicAI.lua: Enhanced AI logic for local responses when no API is configured

local logicAI = {}

-- Initialize conversation state
logicAI.conversation_history = {}
logicAI.user_name = nil
logicAI.context = {}

-- Pattern-based responses for common queries
local patterns = {
    -- Greetings (added Vietnamese "xin chào")
    {
        patterns = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening", "xin chào"},
        responses = {
            "Hello! I'm your local AI assistant. How can I help you today?",
            "Hi there! What would you like to know?",
            "Hello! I'm here to help with your questions.",
            "Hey! What can I assist you with?"
        }
    },

    -- Programming questions
    {
        patterns = {"code", "programming", "python", "javascript", "function", "algorithm", "debug", "error", "bug"},
        responses = {
            "I'd be happy to help with programming! Could you share more details about what you're working on?",
            "Programming questions are my specialty! What language or concept would you like help with?",
            "I can help with coding issues. Please describe the problem you're facing.",
            "Let me help you with that code. What specific error or challenge are you encountering?"
        }
    },

    -- Explanations
    {
        patterns = {"what is", "explain", "how does", "why", "what are", "define"},
        responses = {
            "I'd be happy to explain that concept. Could you be more specific about what aspect you'd like me to clarify?",
            "That's an interesting topic! Let me break it down for you based on what I understand.",
            "I can help explain that. What level of detail would you like - basic overview or technical details?",
            "Good question! Let me provide you with a clear explanation."
        }
    },

    -- AI/Technology questions
    {
        patterns = {"artificial intelligence", "machine learning", "ai", "neural network", "deep learning"},
        responses = {
            "AI is a fascinating field! It involves creating systems that can perform tasks that typically require human intelligence.",
            "Machine learning is a subset of AI that enables computers to learn from data without being explicitly programmed.",
            "AI technology has many applications, from image recognition to natural language processing like what we're doing right now!",
            "Neural networks are inspired by the human brain and consist of interconnected nodes that process information."
        }
    },

    -- Help requests
    {
        patterns = {"help", "assist", "support", "can you", "need"},
        responses = {
            "I'm here to help! I can assist with explanations, coding questions, general knowledge, and more.",
            "Of course! What specific topic or problem would you like assistance with?",
            "I'd be glad to help you. Please let me know what you need assistance with.",
            "Sure thing! How can I make your day easier?"
        }
    },

    -- Math/calculations (pattern as single-quoted string)
    {
        patterns = {"calculate", "math", "equation", "formula", "solve", '%d+[%+%-%*/]%d+'},
        responses = {
            "I can help with math problems! What calculation do you need?",
            "Math is fun! Share the equation or problem you'd like me to work on.",
            "I'm ready to crunch some numbers. What's the mathematical challenge?",
            "Let's solve this together! What's the math problem?"
        }
    }
}

-- Utility functions
local function contains_word(text, pat)
    if not text or not pat then return false end
    local ok, _ = pcall(function()
        return string.find(string.lower(text), string.lower(pat))
    end)
    if ok then
        return string.find(string.lower(text), string.lower(pat)) ~= nil
    end
    return false
end

local function get_random_response(responses)
    if not responses or #responses == 0 then return "" end
    return responses[math.random(#responses)]
end

local function extract_math_expression(text)
    local expr = string.match(text, "(%d+[%+%-%*/]%d+)")
    return expr
end

local function evaluate_simple_math(expr)
    if not expr then return nil end
    local num1, op, num2 = string.match(expr, "(%d+)([%+%-%*/])(%d+)")
    if not (num1 and op and num2) then return nil end
    num1, num2 = tonumber(num1), tonumber(num2)
    if not (num1 and num2) then return nil end
    if op == "+" then return num1 + num2
    elseif op == "-" then return num1 - num2
    elseif op == "*" then return num1 * num2
    elseif op == "/" and num2 ~= 0 then return num1 / num2
    end
    return nil
end

-- Main response function
function logicAI.on_user_message(message)
    if not message or message == "" then
        return "I didn't receive any message. Could you please try again?"
    end

    table.insert(logicAI.conversation_history, {
        role = "user",
        content = message,
        timestamp = os.time()
    })
    if #logicAI.conversation_history > 10 then
        table.remove(logicAI.conversation_history, 1)
    end

    local lower_message = string.lower(message)

    -- Name introduction
    local name_match = string.match(message, "[Mm]y name is (%w+)")
    if name_match then
        logicAI.user_name = name_match
        return string.format("Nice to meet you, %s! I'll remember that. How can I help you today?", name_match)
    end

    -- Math
    local math_expr = extract_math_expression(message)
    if math_expr then
        local result = evaluate_simple_math(math_expr)
        if result then
            return string.format("The answer to %s is %g", math_expr, result)
        end
    end

    -- Pattern matching
    for _, group in ipairs(patterns) do
        for _, pat in ipairs(group.patterns) do
            if contains_word(lower_message, pat) then
                local response = get_random_response(group.responses)
                if logicAI.user_name and response then
                    response = response .. " " .. logicAI.user_name .. "!"
                end
                return response
            end
        end
    end

    -- Special cases
    if contains_word(lower_message, "thank") then
        if logicAI.user_name then
            return string.format("You're welcome, %s! Happy to help anytime.", logicAI.user_name)
        else
            return "You're welcome! Happy to help anytime."
        end
    end

    if contains_word(lower_message, "bye") or contains_word(lower_message, "goodbye") then
        if logicAI.user_name then
            return string.format("Goodbye, %s! Feel free to come back anytime you need help.", logicAI.user_name)
        else
            return "Goodbye! Feel free to come back anytime you need help."
        end
    end

    -- Context-aware
    if #logicAI.conversation_history > 1 then
        local prev = logicAI.conversation_history[#logicAI.conversation_history - 1]
        if prev and prev.role == "assistant" then
            if contains_word(lower_message, "more") or contains_word(lower_message, "tell me more") then
                return "I'd love to provide more details! Could you specify which aspect you'd like me to elaborate on?"
            end
        end
    end

    -- Default
    local default_responses = {
        "That's interesting! Could you tell me more about what you're looking for?",
        "I understand you're asking about that topic. While I don't have access to external APIs right now, I'll do my best to help based on my built-in knowledge.",
        "I'd like to help you with that question. Could you provide a bit more context?",
        "That's a good question! Let me think about how I can best assist you with that.",
        "I'm processing your request. For the most accurate information, you might want to configure an API key in the settings, but I'll try to help with what I can!",
        string.format("I received your message: '%s'. How can I provide useful information about this topic?", message)
    }
    local response = get_random_response(default_responses)
    if #logicAI.conversation_history == 1 then
        response = response .. " (Tip: Configure an API key in settings ⚙️ for more advanced AI responses!)"
    end
    return response
end

function logicAI.init(editor)
    logicAI.editor = editor
    math.randomseed(os.time())
    return "AI Assistant initialized and ready to help!"
end

function logicAI.get_conversation_history()
    return logicAI.conversation_history
end

function logicAI.clear_history()
    logicAI.conversation_history = {}
    logicAI.user_name = nil
    logicAI.context = {}
    return "Conversation history cleared."
end

function logicAI.get_stats()
    return {
        messages_count = #logicAI.conversation_history,
        user_name = logicAI.user_name,
        patterns_count = #patterns
    }
end

return logicAI