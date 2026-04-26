<template>
  <div class="flex h-screen bg-slate-50 font-display">
    <!-- 会话侧边栏 -->
    <div class="w-80 bg-white border-r border-slate-200 flex flex-col shadow-xl z-10">
      <!-- 侧边栏头部 -->
      <div class="p-6 border-b border-slate-100 bg-white">
        <div class="flex items-center space-x-3 mb-6">
          <div class="p-2 rounded-xl bg-blue-600 text-white">
            <BotIcon class="w-6 h-6" />
          </div>
          <h1 class="text-xl font-bold text-slate-900 tracking-tight">AI 运动助手</h1>
        </div>
        <button @click="createNewSession"
                class="w-full px-4 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 shadow-sm transition-all kinetic-button flex items-center justify-center gap-2">
          <PlusIcon class="w-5 h-5" />
          新建对话
        </button>
      </div>

      <!-- 会话列表 -->
      <div class="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar">
        <div v-if="loadingSessions" class="text-center text-slate-400 py-8 flex flex-col items-center">
          <div class="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent mb-2"></div>
          <span class="text-xs font-medium">加载中...</span>
        </div>
        <div v-else-if="sessions.length === 0" class="text-center text-slate-300 py-8">
          <MessageSquareIcon class="w-8 h-8 mx-auto mb-2 opacity-20" />
          <span class="text-xs font-medium">暂无会话</span>
        </div>
        <div v-else>
          <div v-for="session in sessions" :key="session.session_id"
               @click="switchSession(session.session_id)"
               :class="['p-4 rounded-xl cursor-pointer transition-all border group relative',
                        currentSessionId === session.session_id
                          ? 'bg-blue-50 border-blue-100'
                          : 'hover:bg-slate-50 border-transparent']">
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <div class="font-bold text-slate-900 text-sm truncate">{{ session.title }}</div>
                <div class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-1">{{ displayModelLabel(session.model) }}</div>
              </div>
              <button @click.stop="deleteSession(session.session_id)"
                      class="opacity-0 group-hover:opacity-100 p-1.5 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all">
                <Trash2Icon class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 侧边栏底部 -->
      <div class="p-4 border-t border-slate-100">
        <button @click="goBack" class="w-full px-4 py-3 bg-slate-50 text-slate-600 rounded-xl font-bold hover:bg-slate-100 transition-all flex items-center justify-center gap-2 kinetic-button">
          <ChevronLeftIcon class="w-4 h-4" />
          返回首页
        </button>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="flex-1 flex flex-col">
      <!-- 顶部工具栏 -->
      <div class="bg-white border-b border-slate-100 px-8 py-4 flex items-center justify-between shadow-sm z-0">
        <div class="flex items-center gap-6">
          <h2 class="text-lg font-bold text-slate-900 tracking-tight">
            {{ currentSession?.title || '新对话' }}
          </h2>
          <div class="h-4 w-[1px] bg-slate-200"></div>
          <select v-model="selectedModel"
                  @change="changeModel"
                  class="px-3 py-1.5 border border-slate-200 bg-slate-50 rounded-lg text-xs font-bold text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer transition-all">
            <option v-for="model in availableModels" :key="model.value" :value="model.value">
              {{ model.label }}
            </option>
          </select>
        </div>
        <div class="flex gap-3">
          <button @click="clearCurrentSession"
                  class="px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-50 transition-all flex items-center gap-2 kinetic-button">
            <Trash2Icon class="w-3.5 h-3.5" />
            清空
          </button>
          <button @click="generateWeeklyReport"
                  :disabled="generatingReport"
                  class="px-4 py-2 bg-blue-50 text-blue-600 rounded-xl text-xs font-bold hover:bg-blue-100 transition-all flex items-center gap-2 kinetic-button disabled:opacity-50 disabled:pointer-events-none">
            <FileTextIcon v-if="!generatingReport" class="w-3.5 h-3.5" />
            <div v-else class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-blue-600 border-t-transparent"></div>
            智能周报
          </button>
          <button @click="exportCurrentSession"
                  class="px-6 py-2 bg-slate-900 text-white rounded-xl text-xs font-bold hover:bg-slate-800 shadow-sm transition-all flex items-center gap-2 kinetic-button">
            <ShareIcon class="w-3.5 h-3.5" />
            导出 MD
          </button>
        </div>
      </div>

      <!-- 聊天记录 -->
      <div class="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar bg-slate-50/30" ref="chatContainer">
        <div v-if="loadingMessages" class="flex flex-col items-center justify-center py-20 text-slate-400">
          <div class="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent mb-4"></div>
          <span class="text-sm font-medium">加载消息中...</span>
        </div>
        <div v-else-if="messages.length === 0" class="flex flex-col items-center justify-center py-20 text-slate-300">
          <MessageSquareIcon class="w-16 h-16 opacity-10 mb-4" stroke-width="1.5" />
          <span class="text-sm font-bold uppercase tracking-widest">开始新的对话吧</span>
        </div>
        <div v-else class="max-w-4xl mx-auto w-full space-y-8">
          <div v-for="(message, index) in messages" :key="index"
               :class="['flex w-full', message.role === 'user' ? 'justify-end' : 'justify-start']">
            <div :class="['max-w-[85%] p-5 rounded-2xl shadow-sm border transition-all kinetic-shadow',
                         message.role === 'user'
                           ? 'bg-blue-600 text-white border-blue-500 rounded-tr-none'
                           : 'bg-white text-slate-800 border-slate-100 rounded-tl-none']">
              <div v-if="message.role === 'user'" class="whitespace-pre-wrap font-medium leading-relaxed">{{ message.content }}</div>
              <div v-else class="prose prose-slate prose-sm max-w-none prose-headings:font-bold prose-a:text-blue-600" v-html="renderMarkdown(message.content)"></div>
              <div v-if="message.role !== 'user' && message.model" class="text-[10px] mt-3 font-bold uppercase tracking-widest opacity-60">
                AI ENGINE: {{ displayModelLabel(message.model) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="bg-white border-t border-slate-100 p-6 shadow-2xl z-10">
        <div class="max-w-4xl mx-auto flex gap-4 items-end">
          <div class="flex-1 relative">
            <textarea v-model="inputMessage"
                      @keyup.enter.exact="sendMessage"
                      @keydown.enter.shift.prevent="inputMessage += '\n'"
                      class="w-full px-5 py-4 rounded-2xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none font-medium text-slate-800 placeholder-slate-400 shadow-inner"
                      placeholder="咨询您的运动建议...（Shift + Enter 换行）"
                      rows="1"
                      style="min-height: 56px; max-height: 200px;"></textarea>
          </div>
          <button @click="sendMessage"
                  class="p-4 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-700 shadow-lg shadow-blue-100 transition-all kinetic-button disabled:opacity-30 disabled:pointer-events-none"
                  :disabled="!inputMessage.trim() || sendingMessage">
            <SendIcon v-if="!sendingMessage" class="w-6 h-6" />
            <div v-else class="animate-spin rounded-full h-6 w-6 border-2 border-white border-t-transparent"></div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as aiChat from '../services/aiChat'
import { marked } from 'marked'
import { Bot as BotIcon, Plus as PlusIcon, MessageSquare as MessageSquareIcon, Trash2 as Trash2Icon, ChevronLeft as ChevronLeftIcon, Share as ShareIcon, Send as SendIcon, FileText as FileTextIcon } from 'lucide-vue-next'

const router = useRouter()

// 响应式数据
const chatContainer = ref(null)
const inputMessage = ref('')
const messages = ref([])
const sessions = ref([])
const currentSessionId = ref(null)
const currentSession = ref(null)
const loadingSessions = ref(false)
const loadingMessages = ref(false)
const sendingMessage = ref(false)
const generatingReport = ref(false)
const selectedModel = ref('ollama:gemma4')
const availableModels = ref([])

const formatModelLabel = (provider, modelName) => {
  if (!provider && !modelName) return ''
  if (provider === 'ollama' && modelName) {
    return `ollama:${modelName.split(':')[0]}`
  }
  if (provider && modelName && provider !== modelName) {
    return `${provider}:${modelName}`
  }
  return modelName || provider
}

const normalizeModels = (modelsData) => {
  if (Array.isArray(modelsData)) {
    return modelsData
      .filter(value => typeof value === 'string' && value.trim())
      .map(value => ({ label: value, value }))
  }

  if (!modelsData || typeof modelsData !== 'object') {
    return []
  }

  if (Array.isArray(modelsData.available_models)) {
    return modelsData.available_models
      .filter(value => typeof value === 'string' && value.trim())
      .map(value => ({ label: value, value }))
  }

  const combinedLabel = formatModelLabel(modelsData.model, modelsData.ollama_model)
  const optionLabels = [combinedLabel, modelsData.model]
    .filter(value => typeof value === 'string' && value.trim())

  return [...new Set(optionLabels)].map(value => ({ label: value, value }))
}

const normalizeSelectedModel = (modelValue) => {
  if (modelValue && availableModels.value.some(model => model.value === modelValue)) {
    return modelValue
  }
  if (modelValue === 'ollama') {
    return availableModels.value[0]?.value || 'ollama:gemma4'
  }
  return availableModels.value[0]?.value || modelValue || 'ollama:gemma4'
}

const displayModelLabel = (modelValue) => {
  if (modelValue === 'ollama') {
    return availableModels.value[0]?.label || 'ollama:gemma4'
  }
  return modelValue || ''
}

// Markdown渲染函数
const renderMarkdown = (content) => {
  return marked(content)
}

// 获取当前用户信息
const getUserInfo = () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  return {
    id: user.id || 'default_user',
    role: user.role || 'student'
  }
}

// 加载会话列表
const loadSessions = async () => {
  loadingSessions.value = true
  try {
    const userInfo = getUserInfo()
    const result = await aiChat.getUserSessions(userInfo.id)
    if (result.success && result.data) {
      sessions.value = result.data
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
  } finally {
    loadingSessions.value = false
  }
}

// 创建新会话
const createNewSession = async () => {
  try {
    const userInfo = getUserInfo()
    const result = await aiChat.createSession(userInfo.id, selectedModel.value, userInfo.role)
    if (result.success && result.data) {
      currentSessionId.value = result.data.session_id
      currentSession.value = result.data.session
      messages.value = result.data.session.messages || []

      // 刷新会话列表
      await loadSessions()

      // 滚动到底部
      scrollToBottom()
    }
  } catch (error) {
    console.error('创建会话失败:', error)
    alert('无法连接到 AI 服务，请检查网络或稍后再试。')
  }
}

// 切换会话
const switchSession = async (sessionId) => {
  if (currentSessionId.value === sessionId) return

  loadingMessages.value = true
  try {
    const result = await aiChat.getSessionDetails(sessionId)
    if (result.success && result.data) {
      currentSessionId.value = sessionId
      currentSession.value = result.data
      messages.value = result.data.messages || []
      selectedModel.value = normalizeSelectedModel(result.data.model)

      // 滚动到底部
      scrollToBottom()
    }
  } catch (error) {
    console.error('切换会话失败:', error)
    console.error('切换会话失败:', error)
    alert('无法加载该会话历史记录。')
  } finally {
    loadingMessages.value = false
  }
}

// 删除会话
const deleteSession = async (sessionId) => {
  if (!confirm('确定要删除这个会话吗？')) return

  try {
    await aiChat.deleteSession(sessionId)

    // 从会话列表中移除
    sessions.value = sessions.value.filter(s => s.session_id !== sessionId)

    // 如果删除的是当前会话，切换到其他会话或创建新会话
    if (currentSessionId.value === sessionId) {
      if (sessions.value.length > 0) {
        await switchSession(sessions.value[0].session_id)
      } else {
        await createNewSession()
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error)
    console.error('删除会话失败:', error)
    alert('删除会话失败，请重试。')
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || sendingMessage.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: userMessage,
    model: selectedModel.value
  })

  scrollToBottom()

  sendingMessage.value = true
  try {
    const result = await aiChat.sendMessage(currentSessionId.value, userMessage, selectedModel.value)
    if (result.success && result.data) {
      // 更新会话和消息
      currentSession.value = result.data.session
      messages.value = result.data.session.messages || []

      // 更新会话列表中的标题
      const sessionIndex = sessions.value.findIndex(s => s.session_id === currentSessionId.value)
      if (sessionIndex !== -1) {
        sessions.value[sessionIndex].title = result.data.session.title
        sessions.value[sessionIndex].model = result.data.session.model
      }
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    console.error('发送消息失败:', error)
    // 如果失败，移除刚才添加到 UI 的用户消息（或者标记为发送失败），这里简单移除并弹窗
    messages.value.pop()
    alert('消息发送失败，请检查网络后重试。')
  } finally {
    sendingMessage.value = false
    scrollToBottom()
  }
}

// 清空当前会话
const clearCurrentSession = async () => {
  if (!confirm('确定要清空当前会话的所有消息吗？')) return

  try {
    await aiChat.clearSession(currentSessionId.value)
    messages.value = []
    scrollToBottom()
  } catch (error) {
    console.error('清空会话失败:', error)
    console.error('清空会话失败:', error)
    alert('清空会话失败，请重试。')
  }
}

// 导出当前会话
const exportCurrentSession = async () => {
  try {
    const response = await aiChat.exportSession(currentSessionId.value)

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `会话_${currentSessionId.value}_${new Date().toISOString().slice(0, 10)}.md`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出会话失败:', error)
    // 本地导出
    const content = messages.value.map(msg => {
      const role = msg.role === 'user' ? '用户' : '助手'
      return `## ${role}\n\n${msg.content}\n\n---\n`
    }).join('\n')

    const blob = new Blob([content], { type: 'text/markdown' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `会话_${currentSessionId.value}_${new Date().toISOString().slice(0, 10)}.md`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }
}

// 生成智能周报
const generateWeeklyReport = async () => {
  if (generatingReport.value) return
  
  generatingReport.value = true
  try {
    const userInfo = getUserInfo()
    
    // 调用生成报告接口
    const result = await aiChat.generateReport(userInfo.id)
    
    if (result.success && result.data && result.data.report) {
      const reportMsg = result.data.report
      
      // 下载为 Markdown 文件
      const blob = new Blob([reportMsg], { type: 'text/markdown' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `智能运动周报_${new Date().toISOString().slice(0, 10)}.md`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
    } else {
      alert('生成报告失败或无数据。')
    }
  } catch (error) {
    console.error('生成周报失败:', error)
    alert('生成智能周报失败，请稍后重试。')
  } finally {
    generatingReport.value = false
  }
}

// 切换模型
const changeModel = () => {
  console.log('切换模型为:', selectedModel.value)
  // 模型切换会在发送消息时生效
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// 返回首页
const goBack = () => {
  if (router.currentRoute.value.path.includes('/student')) {
    router.push('/student')
  } else if (router.currentRoute.value.path.includes('/teacher')) {
    router.push('/teacher')
  } else {
    router.push('/login')
  }
}

// 监听消息变化，自动滚动到底部
watch(() => messages.value.length, () => {
  scrollToBottom()
})

// 页面加载时初始化
onMounted(async () => {
  try {
    // 加载模型列表
    const modelsResult = await aiChat.getModels()
    if (modelsResult.success && modelsResult.data) {
      availableModels.value = normalizeModels(modelsResult.data)
      if (!availableModels.value.length) {
        availableModels.value = [{ label: 'ollama:gemma4', value: 'ollama:gemma4' }]
      }
      if (!availableModels.value.some(model => model.value === selectedModel.value)) {
        selectedModel.value = availableModels.value[0].value
      }
    } else {
      availableModels.value = [{ label: 'ollama:gemma4', value: 'ollama:gemma4' }]
      selectedModel.value = 'ollama:gemma4'
    }

    // 加载会话列表
    await loadSessions()

    // 获取用户的最新会话
    const userInfo = getUserInfo()
    const latestSessionResult = await aiChat.getLatestSession(userInfo.id)

    if (latestSessionResult.success && latestSessionResult.data) {
      await switchSession(latestSessionResult.data.session_id)
    } else if (sessions.value.length > 0) {
      // 如果没有最新会话，使用第一个会话
      await switchSession(sessions.value[0].session_id)
    } else {
      // 如果没有会话，创建新会话
      await createNewSession()
    }
  } catch (error) {
    console.error('初始化失败:', error)
    alert('AI 服务初始化失败，请检查后端服务是否正常运行。')
  }
})
</script>

<style scoped>
/* 自定义滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* 文本域自动调整高度 */
textarea {
  overflow-y: auto;
}

.prose :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.75rem;
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
  display: block;
}
</style>
