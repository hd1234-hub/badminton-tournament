# -*- coding: utf-8 -*-
"""Fix voice input and update Dashboard AI prompt"""

import re

# Fix AgentPanel.tsx - improve voice input
agent_path = "../src/components/AgentPanel.tsx"
with open(agent_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add voiceError state after listening state
content = content.replace(
    'const [listening, setListening] = useState(false);',
    'const [listening, setListening] = useState(false);\n  const [voiceError, setVoiceError] = useState<string | null>(null);\n  const voiceTimeoutRef = useRef<number | null>(null);'
)

# Replace voice functions
old_voice_code = '''  const startVoice = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMessages(prev => [...prev, { role: "agent", content: "你的浏览器不支持语音输入" }]);
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "zh-CN";
    recognition.interimResults = false;
    recognition.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setInput(prev => prev + transcript);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  };

  const stopVoice = () => {
    recognitionRef.current?.stop();
    setListening(false);
  };'''

new_voice_code = '''  const clearVoiceTimeout = () => {
    if (voiceTimeoutRef.current) {
      window.clearTimeout(voiceTimeoutRef.current);
      voiceTimeoutRef.current = null;
    }
  };

  const startVoice = () => {
    setVoiceError(null);
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceError("当前浏览器不支持语音输入，请使用 Chrome 或 Edge 浏览器");
      return;
    }
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
      setVoiceError("语音输入需要 HTTPS 环境，请使用 https 访问或本地开发");
      return;
    }
    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "zh-CN";
      recognition.interimResults = true;
      recognition.continuous = false;
      recognition.maxAlternatives = 1;
      let finalTranscript = "";
      recognition.onstart = () => {
        setListening(true);
        setVoiceError(null);
        voiceTimeoutRef.current = window.setTimeout(() => {
          if (recognitionRef.current) recognitionRef.current.stop();
        }, 10000);
      };
      recognition.onresult = (e: any) => {
        let interim = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) finalTranscript += e.results[i][0].transcript;
          else interim += e.results[i][0].transcript;
        }
        setInput(prev => finalTranscript + interim);
      };
      recognition.onerror = (e: any) => {
        clearVoiceTimeout();
        setListening(false);
        const errors: Record<string, string> = {
          'no-speech': '没听到声音，请再试一次',
          'audio-capture': '无法访问麦克风，请检查权限',
          'not-allowed': '麦克风权限被拒绝',
          'network': '网络问题，请检查后重试',
          'aborted': '已取消',
        };
        setVoiceError(errors[e.error] || `识别失败: ${e.error}`);
      };
      recognition.onend = () => {
        clearVoiceTimeout();
        setListening(false);
        if (finalTranscript) setInput(finalTranscript);
      };
      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      setVoiceError("启动语音识别失败，请刷新重试");
    }
  };

  const stopVoice = () => {
    clearVoiceTimeout();
    try { recognitionRef.current?.stop(); } catch {}
    setListening(false);
  };'''

content = content.replace(old_voice_code, new_voice_code)

# Add voiceError display before input area
old_input_section = '<div className="flex gap-2">\n            <input'
new_input_section = '''{voiceError && (
              <div className="px-4 py-2 bg-red-50 text-red-600 text-xs rounded-xl mb-2">
                {voiceError}
              </div>
            )}
            <div className="flex gap-2">
            <input'''
content = content.replace(old_input_section, new_input_section)

# Close the extra div after the mic button - find the right place
content = content.replace(
    'onClick={listening ? stopVoice : startVoice}\n            className={`px-3 py-3 rounded-2xl transition ${listening ? "bg-red-500 text-white animate-pulse" : "bg-nailong-cream text-gray-500 hover:bg-nailong-cream-dark"}`}',
    'onClick={listening ? stopVoice : startVoice}\n            className={`px-3 py-3 rounded-2xl transition ${listening ? "bg-red-500 text-white animate-pulse" : "bg-nailong-cream text-gray-500 hover:bg-nailong-cream-dark"}`}\n            title={listening ? "点击停止" : "语音输入"}'
)

with open(agent_path, "w", encoding="utf-8") as f:
    f.write(content)

print("AgentPanel voice fixed")

# Fix Dashboard.tsx - update AI prompt
dash_path = "../src/pages/Dashboard.tsx"
with open(dash_path, "r", encoding="utf-8") as f:
    content = f.read()

# Update the AI assistant prompt
old_prompt = '''<p className="text-gray-800 font-medium">
            不知道怎么做？点击右上角{" "}
            <span className="text-nailong-orange font-bold">「AI 助手」</span> 问奶龙！
          </p>
          <p className="text-gray-500 text-sm mt-0.5">
            试试说：「帮我创建一个八人转比赛」「我想加入俱乐部」「记录比分 21:15」
          </p>'''

new_prompt = '''<p className="text-gray-800 font-medium">
            点击右上角{" "}
            <span className="text-nailong-orange font-bold">「AI 助手」</span>，奶龙帮你：
            创建比赛 · 预测胜负 · 查排名 · 录比分
          </p>
          <p className="text-gray-500 text-sm mt-0.5">
            例如：「帮我创建一个八人转」「预测张三和李四谁赢」「记录一下比分」
          </p>'''

content = content.replace(old_prompt, new_prompt)

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Dashboard prompt updated")
print("Done!")
