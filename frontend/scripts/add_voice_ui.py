# -*- coding: utf-8 -*-
import codecs

content = codecs.open('../src/components/AgentPanel.tsx', 'r', 'utf-8').read()

old = '''      {/* Input */}
      <div className="p-4 border-t border-nailong-cream-dark bg-white">'''

new = '''      {/* Input */}
      <div className="p-4 border-t border-nailong-cream-dark bg-white">
        {voiceError && (
          <div className="mb-3 px-4 py-2 bg-red-50 text-red-600 text-sm rounded-xl flex items-center justify-between">
            <span>{voiceError}</span>
            <button onClick={() => setVoiceError(null)} className="text-red-400 hover:text-red-700">&times;</button>
          </div>
        )}'''

content = content.replace(old, new)
codecs.open('../src/components/AgentPanel.tsx', 'w', 'utf-8').write(content)
print('voice UI added')
