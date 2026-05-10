<template>
  <AppLayout>
    <section class="assistant-hero panel-card">
      <div class="assistant-hero-info">
        <span class="assistant-eyebrow">AI Deep Learning Assistant</span>
        <h2>AI深度学习助手</h2>
        <p>可接入 DeepSeek 或 OpenAI 兼容接口，用于说明检测结果、整理排查思路或回答系统使用问题。</p>
      </div>
      <el-tag size="large" :type="status?.configured ? 'success' : 'warning'" effect="dark">
        {{ status?.configured ? `已配置：${status.model}` : '未配置 API Key' }}
      </el-tag>
    </section>

    <section class="assistant-workspace">
      <aside class="assistant-tool-panel panel-card">
        <div class="tool-panel-header">
          <h3>快捷提示词</h3>
          <p>选择常用问题快速开始对话</p>
        </div>
        <div class="tool-prompt-list">
          <button v-for="item in prompts" :key="item" class="tool-prompt-btn" @click="question = item">
            <span class="prompt-icon">?</span>
            <span>{{ item }}</span>
          </button>
        </div>
        <div class="assistant-status-box">
          <div class="status-indicator">
            <StatusPulse :status="status?.configured ? 'success' : 'danger'" size="sm" />
            <strong>{{ status?.configured ? '服务可用' : '未配置' }}</strong>
          </div>
          <small>{{ status?.model || '等待配置 AI_ASSISTANT_API_KEY' }}</small>
        </div>
      </aside>

      <main class="assistant-chat-panel panel-card">
        <div class="assistant-conversation" ref="chatEl">
          <div class="chat-bubble assistant">
            <div class="bubble-avatar">AI</div>
            <div class="bubble-content">
              <strong>AI深度学习助手</strong>
              <p>我可以帮助解释检测结果、排查 GPU/CUDA、整理模型管理和深度学习训练分析问题。</p>
            </div>
          </div>
          <TransitionGroup name="list">
            <template v-for="message in messages" :key="message.id">
              <div class="chat-bubble user">
                <div class="bubble-content">
                  <p>{{ message.question }}</p>
                </div>
                <div class="bubble-avatar user-avatar">U</div>
              </div>
              <div class="chat-bubble assistant">
                <div class="bubble-avatar">AI</div>
                <div class="bubble-content">
                  <p>{{ message.answer }}</p>
                </div>
              </div>
            </template>
          </TransitionGroup>
          <el-empty v-if="!messages.length" :description="status?.configured ? '发送问题后显示对话记录' : '后端未配置 AI_ASSISTANT_API_KEY，配置后即可使用'" />
        </div>
        <div class="assistant-input-bar">
          <el-input v-model="question" type="textarea" :rows="3" placeholder="请输入你的问题，Ctrl+Enter 发送" @keyup.ctrl.enter="send" />
          <div class="assistant-input-actions">
            <el-button @click="question = ''">清空</el-button>
            <el-button type="primary" :loading="loading" :disabled="!question.trim() || !status?.configured" @click="send">
              发送问题
            </el-button>
          </div>
        </div>
      </main>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppLayout from '@/components/layout/AppLayout.vue'
import StatusPulse from '@/components/common/StatusPulse.vue'
import { askAssistant, getAssistantStatus, type AssistantStatus } from '@/api/assistant'

const status = ref<AssistantStatus | null>(null)
const question = ref('')
const loading = ref(false)
const messages = ref<Array<{ id: number; question: string; answer: string }>>([])
const prompts = ['如何排查 GPU 无法使用？', '如何解释检测结果中的低置信度？', '如何给新模型维护中文类别？']

async function loadStatus() {
  status.value = await getAssistantStatus()
}
async function send() {
  const text = question.value.trim()
  if (!text) return
  loading.value = true
  try {
    const data = await askAssistant(text)
    messages.value.push({ id: Date.now(), question: text, answer: data.answer })
    status.value = { configured: data.configured, model: data.model }
    question.value = ''
  } finally {
    loading.value = false
  }
}
onMounted(loadStatus)
</script>

<style scoped>
/* Hero */
.assistant-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: var(--gap);
  background: linear-gradient(135deg, #f0f9ff 0%, #ede9fe 50%, #fdf4ff 100%);
  border: 1px solid #c7d2fe;
  position: relative;
  overflow: hidden;
}

.assistant-hero::before {
  content: "";
  position: absolute;
  top: -40%;
  right: -15%;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(124, 58, 237, 0.06) 0%, transparent 70%);
  pointer-events: none;
}

.assistant-eyebrow {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7c3aed;
  margin-bottom: 4px;
}

.assistant-hero-info h2 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 800;
  color: var(--color-ink);
}

.assistant-hero-info p {
  margin: 0;
  font-size: 13px;
  color: var(--color-muted);
  max-width: 500px;
}

/* 工具面板 */
.tool-panel-header h3 {
  margin: 0 0 4px;
  font-size: 16px;
  color: var(--color-ink);
}

.tool-panel-header p {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--color-muted);
}

.tool-prompt-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 20px;
}

.tool-prompt-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-ink);
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: all var(--motion-fast) var(--ease-standard);
  font-family: inherit;
}

.tool-prompt-btn:hover {
  border-color: var(--color-primary-light);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.prompt-icon {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

/* 状态框 */
.assistant-status-box {
  margin-top: auto;
  padding: 14px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.status-indicator strong {
  font-size: 13px;
  color: var(--color-ink);
}

.assistant-status-box small {
  display: block;
  font-size: 11px;
  color: var(--color-soft);
}

/* 聊天面板 */
.assistant-chat-panel {
  display: flex;
  flex-direction: column;
}

.assistant-conversation {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 360px;
  max-height: 520px;
  overflow: auto;
  padding: 18px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  flex: 1;
}

/* 气泡样式 */
.chat-bubble {
  display: flex;
  gap: 10px;
  max-width: 85%;
  animation: slide-up-fade var(--motion-normal) var(--ease-emphasized);
}

.chat-bubble.assistant {
  align-self: flex-start;
}

.chat-bubble.user {
  align-self: flex-end;
}

.bubble-avatar {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  flex-shrink: 0;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  color: #fff;
}

.bubble-avatar.user-avatar {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
}

.bubble-content {
  padding: 12px 16px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.chat-bubble.user .bubble-content {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  border-color: transparent;
  color: #fff;
}

.bubble-content strong {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  opacity: 0.6;
}

.bubble-content p {
  margin: 0;
  line-height: 1.7;
  white-space: pre-wrap;
  font-size: 14px;
}

/* 输入栏 */
.assistant-input-bar {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.assistant-input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 992px) {
  .assistant-hero {
    flex-direction: column;
    align-items: flex-start;
  }
  .assistant-workspace {
    grid-template-columns: 1fr;
  }
}
</style>